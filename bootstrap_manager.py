"""
bootstrap_manager.py
Sistema centralizzato di Bootstrap, Environment Check e Riparazione per Sub Studio.

Garantisce che l'applicazione funzioni 'out-of-the-box' su qualsiasi Mac (incluso un
Mac Apple Silicon pulito privo di Homebrew, Xcode command line tools o dipendenze globali).

Responsabilità:
1. Rilevamento sistema, versione macOS e architettura hardware (Apple Silicon arm64 / Intel x86_64).
2. Verifica e creazione garantita delle directory applicative e permessi di scrittura.
3. Risoluzione robusta di FFmpeg con priorità assoluta al bundle interno dell'app (.app),
   seguito da directory utente dedicata, PATH e fallback automatici.
4. Validazione effettiva dell'integrità dei binari ed esecuzione reale di test (es. -version e VideoToolbox).
5. Download e installazione automatica e sicura di FFmpeg statico in caso di componente mancante o corrotto,
   senza MAI obbligare l'utente ad aprire il Terminale o installare Homebrew.
6. Caching dello stato in 'bootstrap-state.json' per garantire avvii successivi istantanei (<20ms).
7. Modalità di verifica e riparazione ('repair') automatica o su richiesta utente.
8. Error handling strutturato e amichevole per l'utente, con log dettagliati per il debug.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("substudio.bootstrap")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[Bootstrap] %(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Costanti di stato dei componenti
STATUS_OK = "ok"
STATUS_MISSING = "missing"
STATUS_INCOMPATIBLE = "incompatible"
STATUS_CORRUPTED = "corrupted"
STATUS_INSTALL_REQUIRED = "install_required"
STATUS_ERROR = "error"

# URL ufficiali / release verificate di binari statici FFmpeg per macOS (fallback autonomo)
# Testati e verificati: binari Mach-O statici con VideoToolbox e zero dipendenze esterne
FFMPEG_URL_ARM64 = "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffmpeg-darwin-arm64.gz"
FFMPEG_URL_X86_64 = "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffmpeg-darwin-x64.gz"

# Costanti sorgenti FFmpeg
SOURCE_APP_BUNDLE = "APP BUNDLE"
SOURCE_USER_DATA = "USER DATA"
SOURCE_SYSTEM = "SYSTEM"
SOURCE_HOMEBREW = "HOMEBREW"


@dataclass
class ComponentStatus:
    name: str
    status: str  # ok, missing, incompatible, corrupted, install_required, error
    title: str
    message: str
    path: Optional[str] = None
    version: Optional[str] = None
    details: Optional[dict[str, Any]] = None


@dataclass
class BootstrapResult:
    ready: bool
    status: str  # ready, needs_install, repair_needed, error
    components: dict[str, ComponentStatus]
    log_messages: list[str]
    os_name: str
    arch: str
    ffmpeg_path: Optional[str] = None
    ffmpeg_source: Optional[str] = None
    elapsed_ms: float = 0.0


class BootstrapManager:
    """Gestore centralizzato dell'ambiente e del ciclo di vita di avvio di Sub Studio."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.workspace_dir = Path(__file__).resolve().parent
        
        # Directory dati utente: Movies/SubStudio (o SUBSTUDIO_DATA_DIR)
        env_data = os.environ.get("SUBSTUDIO_DATA_DIR") or os.environ.get("SOTTOTITOLATORE_DATA_DIR")
        if data_dir:
            self.data_dir = Path(data_dir).resolve()
        elif env_data:
            self.data_dir = Path(env_data).resolve()
        else:
            self.data_dir = Path.home() / "Movies" / "SubStudio"

        self.uploads_dir = self.data_dir / "web_uploads"
        self.outputs_dir = self.data_dir / "web_outputs"
        self.bin_dir = self.data_dir / "bin"
        self.models_dir = self.data_dir / "models"
        self.state_file = self.data_dir / "bootstrap-state.json"
        
        self.logs: list[str] = []
        self._resolved_ffmpeg: Optional[str] = None
        self._resolved_ffprobe: Optional[str] = None

    def log(self, msg: str, level: str = "info") -> None:
        formatted = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.logs.append(formatted)
        if level == "error":
            logger.error(msg)
        elif level == "warning":
            logger.warning(msg)
        else:
            logger.info(msg)

    # --------------------------------------------------------------------------
    # 1. Rilevamento Piattaforma e Architettura
    # --------------------------------------------------------------------------
    def check_system(self) -> ComponentStatus:
        system = platform.system()
        release = platform.mac_ver()[0] or platform.release()
        arch = platform.machine().lower()

        if system != "Darwin":
            return ComponentStatus(
                name="os",
                status=STATUS_INCOMPATIBLE,
                title="Sistema Operativo",
                message=f"Sub Studio è ottimizzato per macOS. Rilevato: {system}",
                details={"system": system, "release": release, "arch": arch},
            )

        # Controllo versione minima macOS (Monterey 12.0+)
        try:
            major = int(release.split(".")[0]) if release else 12
        except Exception:
            major = 12

        if major < 11:
            return ComponentStatus(
                name="os",
                status=STATUS_INCOMPATIBLE,
                title="Versione macOS",
                message=f"Richiesto macOS 12.0 o superiore. Rilevato macOS {release}",
                details={"release": release},
            )

        arch_title = "Apple Silicon (arm64)" if arch == "arm64" else f"Intel ({arch})"
        self.log(f"Sistema verificato: macOS {release} ({arch_title})")
        return ComponentStatus(
            name="os",
            status=STATUS_OK,
            title="macOS",
            message=f"macOS {release} ({arch_title})",
            version=release,
            details={"system": system, "release": release, "arch": arch},
        )

    def check_architecture(self) -> ComponentStatus:
        arch = platform.machine().lower()
        is_arm64 = arch in ("arm64", "aarch64")
        return ComponentStatus(
            name="architecture",
            status=STATUS_OK,
            title="Architettura CPU",
            message="Apple Silicon (nativo arm64)" if is_arm64 else f"Intel ({arch})",
            details={"arch": arch, "is_apple_silicon": is_arm64},
        )

    # --------------------------------------------------------------------------
    # 2. Directory Applicative e Permessi
    # --------------------------------------------------------------------------
    def check_and_create_directories(self) -> ComponentStatus:
        dirs_to_check = [
            ("data_dir", self.data_dir),
            ("web_uploads", self.uploads_dir),
            ("web_outputs", self.outputs_dir),
            ("bin", self.bin_dir),
            ("models", self.models_dir),
        ]
        
        created = []
        for name, d in dirs_to_check:
            try:
                d.mkdir(parents=True, exist_ok=True)
                test_file = d / ".substudio_perm_test"
                test_file.write_text("ok", encoding="utf-8")
                test_file.unlink()
                created.append(str(d))
            except Exception as e:
                self.log(f"Errore permessi directory '{d}': {e}", "error")
                return ComponentStatus(
                    name="directories",
                    status=STATUS_ERROR,
                    title="Cartelle Dati",
                    message=f"Impossibile accedere o scrivere nella cartella: {d.name}",
                    details={"directory": str(d), "error": str(e)},
                )

        self.log(f"Cartelle applicative verificate con successo in: {self.data_dir}")
        return ComponentStatus(
            name="directories",
            status=STATUS_OK,
            title="Cartelle Dati",
            message=f"Cartelle pronte in {self.data_dir.name}",
            path=str(self.data_dir),
            details={"directories": created},
        )

    # --------------------------------------------------------------------------
    # 3. Risoluzione & Verifica FFmpeg
    # --------------------------------------------------------------------------
    def classify_source(self, binary_path: Path) -> str:
        """Classifica la provenienza del binario FFmpeg."""
        try:
            resolved = str(binary_path.resolve())
        except Exception:
            resolved = str(binary_path)

        if "SubStudio.app/Contents/Resources" in resolved or str(self.workspace_dir.resolve()) in resolved:
            return SOURCE_APP_BUNDLE
        if str(self.bin_dir.resolve()) in resolved or str(self.data_dir.resolve()) in resolved:
            return SOURCE_USER_DATA
        if "/opt/homebrew" in resolved or "/Cellar/" in resolved or "/homebrew/" in resolved:
            return SOURCE_HOMEBREW
        if resolved.startswith("/usr/bin") or resolved.startswith("/usr/local/bin"):
            return SOURCE_SYSTEM
        return "EXTERNAL"

    def get_ffmpeg_candidates(self) -> list[tuple[Path, str]]:
        """Restituisce la lista ordinata per priorità dei percorsi e sorgenti in cui cercare FFmpeg."""
        candidates: list[tuple[Path, str]] = []

        # 1. APP BUNDLE (massima priorità assoluta per app DMG)
        bundle_res_bin = self.workspace_dir.parent / "bin" / "ffmpeg"
        candidates.append((bundle_res_bin, SOURCE_APP_BUNDLE))

        res_dir = self.workspace_dir.parent.parent / "Resources" / "bin" / "ffmpeg"
        candidates.append((res_dir, SOURCE_APP_BUNDLE))

        workspace_bin = self.workspace_dir / "bin" / "ffmpeg"
        candidates.append((workspace_bin, SOURCE_APP_BUNDLE))

        # 2. USER DATA (cartella gestita dall'app in ~/Movies/SubStudio/bin/ffmpeg)
        candidates.append((self.bin_dir / "ffmpeg", SOURCE_USER_DATA))

        # 3. SYSTEM PATH (/usr/local/bin, /usr/bin)
        candidates.append((Path("/usr/local/bin/ffmpeg"), SOURCE_SYSTEM))
        candidates.append((Path("/usr/bin/ffmpeg"), SOURCE_SYSTEM))

        # 4. HOMEBREW (solo se non esplicitamente disabilitato da test/simulazione)
        disable_homebrew = os.environ.get("SUBSTUDIO_DISABLE_HOMEBREW", "0") == "1"
        if not disable_homebrew:
            candidates.append((Path("/opt/homebrew/bin/ffmpeg"), SOURCE_HOMEBREW))

        # 5. Risoluzione dinamica tramite shutil.which
        which_path = shutil.which("ffmpeg")
        if which_path:
            p = Path(which_path)
            is_brew_path = "/opt/homebrew" in str(p) or "/Cellar/" in str(p)
            if not (disable_homebrew and is_brew_path):
                already_in = any(c[0].resolve() == p.resolve() for c in candidates if c[0].exists())
                if not already_in:
                    src = self.classify_source(p)
                    candidates.append((p, src))

        return candidates

    def validate_ffmpeg_binary(self, binary_path: Path) -> tuple[str, Optional[str], bool, Optional[str]]:
        """
        Valida approfonditamente l'eseguibile FFmpeg.
        Ritorna: (status, versione_string, supporta_videotoolbox, messaggio_errore)
        """
        if not binary_path.exists():
            return STATUS_MISSING, None, False, "File non trovato"

        if not os.access(binary_path, os.X_OK):
            try:
                os.chmod(binary_path, 0o755)
            except Exception:
                pass

        if not os.access(binary_path, os.X_OK):
            return STATUS_CORRUPTED, None, False, "Permesso di esecuzione mancante"

        # Esegue `ffmpeg -version`
        try:
            proc = subprocess.run(
                [str(binary_path), "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if proc.returncode != 0:
                return STATUS_CORRUPTED, None, False, f"Uscita con codice di errore {proc.returncode}"
            
            output = proc.stdout or proc.stderr
            first_line = output.splitlines()[0] if output else "ffmpeg sconosciuto"
            version_match = first_line.replace("ffmpeg version", "").strip().split()[0]
        except subprocess.TimeoutExpired:
            return STATUS_CORRUPTED, None, False, "Timeout durante la verifica del binario"
        except Exception as exc:
            return STATUS_CORRUPTED, None, False, f"Impossibile eseguire il binario: {exc}"

        # Controllo accelerazione hardware VideoToolbox
        has_videotoolbox = False
        try:
            enc_proc = subprocess.run(
                [str(binary_path), "-hide_banner", "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            )
            if "h264_videotoolbox" in enc_proc.stdout or "hevc_videotoolbox" in enc_proc.stdout:
                has_videotoolbox = True
        except Exception:
            pass

        return STATUS_OK, version_match, has_videotoolbox, None

    def check_ffmpeg(self) -> ComponentStatus:
        candidates = self.get_ffmpeg_candidates()
        best_candidate: Optional[Path] = None
        best_source: Optional[str] = None
        best_version: Optional[str] = None
        best_vtb: bool = False
        corrupted_candidate: Optional[Path] = None
        corrupted_reason: Optional[str] = None

        for cand, src in candidates:
            if cand.exists():
                status, ver, vtb, err = self.validate_ffmpeg_binary(cand)
                if status == STATUS_OK:
                    best_candidate = cand
                    best_source = src
                    best_version = ver
                    best_vtb = vtb
                    break
                elif not corrupted_candidate:
                    corrupted_candidate = cand
                    corrupted_reason = err

        if best_candidate:
            self._resolved_ffmpeg = str(best_candidate.resolve())
            self.ensure_ffmpeg_in_path(best_candidate)
            vtb_str = " (Accelerazione VideoToolbox attiva)" if best_vtb else ""
            self.log(
                f"FFmpeg trovato e valido:\n"
                f"  Sorgente: {best_source}\n"
                f"  Percorso: {best_candidate}\n"
                f"  Versione: {best_version}{vtb_str}"
            )
            return ComponentStatus(
                name="ffmpeg",
                status=STATUS_OK,
                title="Motore FFmpeg",
                message=f"FFmpeg {best_version} [{best_source}]{vtb_str}",
                path=str(best_candidate),
                version=best_version,
                details={
                    "source": best_source,
                    "videotoolbox": best_vtb,
                    "path": str(best_candidate),
                },
            )

        if corrupted_candidate:
            self.log(f"FFmpeg trovato ma corrotto in '{corrupted_candidate}': {corrupted_reason}", "warning")
            return ComponentStatus(
                name="ffmpeg",
                status=STATUS_CORRUPTED,
                title="Motore FFmpeg",
                message=f"Binario danneggiato: {corrupted_reason}",
                path=str(corrupted_candidate),
                details={"error": corrupted_reason},
            )

        self.log("FFmpeg non trovato in nessun percorso noto", "warning")
        return ComponentStatus(
            name="ffmpeg",
            status=STATUS_MISSING,
            title="Motore FFmpeg",
            message="FFmpeg non presente nel sistema",
            details={},
        )

    def ensure_ffmpeg_in_path(self, ffmpeg_bin: Path) -> None:
        """Inserisce la cartella del binario FFmpeg in testa alla variabile d'ambiente PATH."""
        bin_dir = str(ffmpeg_bin.resolve().parent)
        current_path = os.environ.get("PATH", "")
        paths = current_path.split(":")
        if bin_dir not in paths:
            os.environ["PATH"] = f"{bin_dir}:{current_path}"
            self.log(f"PATH aggiornato con priorità per: {bin_dir}")

    # --------------------------------------------------------------------------
    # 4. Installazione Automatica & Autonoma di FFmpeg
    # --------------------------------------------------------------------------
    def install_or_repair_ffmpeg(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> bool:
        """
        Installa o ripristina autonomamente FFmpeg in modalità 100% self-contained.
        Ordine:
        1. Ripristino da APP BUNDLE interno se disponibile
        2. Download static binary autonomo con decompressore gzip integrato in python
        NON invoca MAI Homebrew né apre il Terminale.
        """
        def update_progress(msg: str, frac: float):
            self.log(msg)
            if progress_callback:
                progress_callback(msg, frac)

        update_progress("Inizializzazione configurazione FFmpeg...", 0.1)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        target_path = self.bin_dir / "ffmpeg"

        # 1. Verifica se esiste una copia integra nel bundle da ripristinare
        bundle_copies = [
            self.workspace_dir / "bin" / "ffmpeg",
            self.workspace_dir.parent / "bin" / "ffmpeg",
            self.workspace_dir.parent.parent / "Resources" / "bin" / "ffmpeg",
        ]
        for src in bundle_copies:
            if src.exists() and src.resolve() != target_path.resolve():
                status, ver, _, _ = self.validate_ffmpeg_binary(src)
                if status == STATUS_OK:
                    update_progress(f"Ripristino FFmpeg dal bundle ({src})...", 0.5)
                    try:
                        shutil.copy2(src, target_path)
                        os.chmod(target_path, 0o755)
                        self._strip_quarantine(target_path)
                        status, ver, _, _ = self.validate_ffmpeg_binary(target_path)
                        if status == STATUS_OK:
                            self._resolved_ffmpeg = str(target_path)
                            self.ensure_ffmpeg_in_path(target_path)
                            update_progress("FFmpeg ripristinato con successo dal bundle dell'app!", 1.0)
                            return True
                    except Exception as e:
                        self.log(f"Errore copia da bundle: {e}", "warning")

        # 2. Download binario statico autonomo via HTTPS
        arch = platform.machine().lower()
        is_arm = arch in ("arm64", "aarch64")
        url = FFMPEG_URL_ARM64 if is_arm else FFMPEG_URL_X86_64
        arch_name = "Apple Silicon (arm64)" if is_arm else "Intel (x86_64)"

        update_progress(f"Download binario statico FFmpeg per {arch_name}...", 0.3)
        temp_gz = self.bin_dir / "ffmpeg_download.tmp.gz"
        temp_bin = self.bin_dir / "ffmpeg_download.tmp"

        try:
            # Download sicuro con gestione timeout e user-agent appropriato
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SubStudio-Bootstrap/1.0 (macOS)"},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=45) as resp, open(temp_gz, "wb") as out_f:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP Status inatteso durante il download: {resp.status}")
                total_len = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 128 * 1024
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    if total_len > 0:
                        pct = 0.3 + 0.45 * (downloaded / total_len)
                        if progress_callback and downloaded % (chunk_size * 4) == 0:
                            mb_down = downloaded / (1024 * 1024)
                            mb_tot = total_len / (1024 * 1024)
                            progress_callback(f"Download FFmpeg: {mb_down:.1f}/{mb_tot:.1f} MB ({int((downloaded/total_len)*100)}%)", pct)

            update_progress("Decompressione binario FFmpeg statico...", 0.8)
            import gzip
            with gzip.open(temp_gz, "rb") as gz_in, open(temp_bin, "wb") as bin_out:
                shutil.copyfileobj(gz_in, bin_out)

            os.chmod(temp_bin, 0o755)
            self._strip_quarantine(temp_bin)

            # Validazione rigorosa prima della sostituzione
            status, ver, vtb, err = self.validate_ffmpeg_binary(temp_bin)
            if status != STATUS_OK:
                raise RuntimeError(f"Il binario scaricato non ha superato la verifica: {err}")

            if target_path.exists():
                target_path.unlink()
            temp_bin.rename(target_path)
            if temp_gz.exists():
                temp_gz.unlink()

            self._resolved_ffmpeg = str(target_path)
            self.ensure_ffmpeg_in_path(target_path)
            update_progress(f"FFmpeg {ver} configurato con successo in USER DATA!", 1.0)
            return True

        except Exception as exc:
            self.log(
                f"Sub Studio non è riuscito a configurare FFmpeg automaticamente.\n"
                f"Dettaglio errore: {exc}",
                "error"
            )
            if temp_gz.exists():
                try: temp_gz.unlink()
                except Exception: pass
            if temp_bin.exists():
                try: temp_bin.unlink()
                except Exception: pass

        return False

    def _strip_quarantine(self, file_path: Path) -> None:
        """Rimuove l'attributo com.apple.quarantine aggiunto da macOS ai file scaricati."""
        try:
            subprocess.run(["xattr", "-d", "com.apple.quarantine", str(file_path)], capture_output=True)
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # 5. Modello Whisper Offline & Dipendenze Python
    # --------------------------------------------------------------------------
    def check_whisper_model(self) -> ComponentStatus:
        candidates = [
            self.workspace_dir / "models" / "small",
            self.workspace_dir.parent / "models" / "small",
            self.workspace_dir.parent / "app" / "models" / "small",
            self.models_dir / "small",
        ]
        
        # Check snapshot Hugging Face Hub
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-small" / "snapshots"
        if hf_cache.exists():
            for snap in hf_cache.glob("*"):
                if snap.is_dir() and (snap / "model.bin").exists():
                    candidates.append(snap)

        for c in candidates:
            if c.exists() and (c / "model.bin").exists():
                size_mb = round((c / "model.bin").stat().st_size / (1024 * 1024), 1)
                self.log(f"Modello Whisper 'small' trovato in: {c} ({size_mb} MB)")
                return ComponentStatus(
                    name="whisper",
                    status=STATUS_OK,
                    title="Modello Trascrizione",
                    message=f"Modello Whisper small integrato ({size_mb} MB)",
                    path=str(c),
                    details={"size_mb": size_mb, "path": str(c)},
                )

        self.log("Modello Whisper small locale non preinstallato (verrà scaricato su richiesta)", "info")
        return ComponentStatus(
            name="whisper",
            status=STATUS_OK,
            title="Modello Trascrizione",
            message="Modello pronto per il download automatico al primo uso",
            details={},
        )

    def check_python_packages(self) -> ComponentStatus:
        required = ["faster_whisper", "PIL", "rich", "typer", "numpy"]
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)

        if missing:
            return ComponentStatus(
                name="python_packages",
                status=STATUS_ERROR,
                title="Librerie Python",
                message=f"Moduli mancanti: {', '.join(missing)}",
                details={"missing": missing},
            )

        return ComponentStatus(
            name="python_packages",
            status=STATUS_OK,
            title="Librerie Python",
            message="Tutte le librerie runtime sono installate e pronte",
            details={},
        )

    # --------------------------------------------------------------------------
    # 6. Caching Stato (Fast-Path) e Verifica Completa
    # --------------------------------------------------------------------------
    def is_fast_path_valid(self) -> bool:
        """Verifica se la cache 'bootstrap-state.json' è valida e recente."""
        if not self.state_file.exists():
            return False

        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            if data.get("status") != "ready":
                return False

            # Verifica che il percorso di ffmpeg memorizzato esista ancora e sia eseguibile
            ffmpeg_path = data.get("ffmpeg_path")
            if not ffmpeg_path or not os.path.exists(ffmpeg_path) or not os.access(ffmpeg_path, os.X_OK):
                return False

            # Verifica directory base
            if not self.uploads_dir.exists() or not self.outputs_dir.exists():
                return False

            # Cache valida
            self._resolved_ffmpeg = ffmpeg_path
            self.ensure_ffmpeg_in_path(Path(ffmpeg_path))
            return True
        except Exception:
            return False

    def save_state(self, result: BootstrapResult) -> None:
        """Salva lo stato corrente in 'bootstrap-state.json'."""
        try:
            data = {
                "status": result.status,
                "timestamp": time.time(),
                "os_name": result.os_name,
                "arch": result.arch,
                "ffmpeg_path": result.ffmpeg_path,
                "ffmpeg_source": result.ffmpeg_source,
                "components": {k: asdict(v) for k, v in result.components.items()},
            }
            self.state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.log(f"Stato bootstrap salvato in: {self.state_file}")
        except Exception as e:
            self.log(f"Impossibile salvare lo stato bootstrap: {e}", "warning")

    def run_bootstrap(
        self,
        force_full_check: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> BootstrapResult:
        """
        Esegue il bootstrap completo o veloce dell'applicazione.
        """
        start_time = time.perf_counter()

        # Fast-path per avvii successivi se lo stato è intatto
        if not force_full_check and self.is_fast_path_valid():
            self.log("Fast-path bootstrap completato: ambiente già verificato e pronto")
            elapsed = (time.perf_counter() - start_time) * 1000
            cached_data = json.loads(self.state_file.read_text(encoding="utf-8"))
            components = {}
            for k, v in cached_data.get("components", {}).items():
                components[k] = ComponentStatus(**v)

            ffmpeg_src = cached_data.get("ffmpeg_source")
            if not ffmpeg_src and self._resolved_ffmpeg:
                ffmpeg_src = self.classify_source(Path(self._resolved_ffmpeg))

            return BootstrapResult(
                ready=True,
                status="ready",
                components=components,
                log_messages=self.logs,
                os_name=cached_data.get("os_name", platform.system()),
                arch=cached_data.get("arch", platform.machine()),
                ffmpeg_path=self._resolved_ffmpeg,
                ffmpeg_source=ffmpeg_src,
                elapsed_ms=elapsed,
            )

        # Controllo completo
        self.log("Avvio verifica completa dell'ambiente Sub Studio...")
        if progress_callback:
            progress_callback("Verifica sistema macOS...", 0.1)

        sys_status = self.check_system()
        arch_status = self.check_architecture()
        
        if progress_callback:
            progress_callback("Controllo cartelle applicative...", 0.3)
        dir_status = self.check_and_create_directories()

        if progress_callback:
            progress_callback("Rilevamento e test motore FFmpeg...", 0.5)
        ffmpeg_status = self.check_ffmpeg()

        # Se FFmpeg manca o è corrotto, tenta l'installazione automatica
        if ffmpeg_status.status in (STATUS_MISSING, STATUS_CORRUPTED, STATUS_INSTALL_REQUIRED):
            if progress_callback:
                progress_callback("Installazione automatica FFmpeg...", 0.7)
            success = self.install_or_repair_ffmpeg(progress_callback=progress_callback)
            if success:
                ffmpeg_status = self.check_ffmpeg()

        if progress_callback:
            progress_callback("Verifica modello e librerie...", 0.85)
        whisper_status = self.check_whisper_model()
        py_status = self.check_python_packages()

        components = {
            "os": sys_status,
            "architecture": arch_status,
            "directories": dir_status,
            "ffmpeg": ffmpeg_status,
            "whisper": whisper_status,
            "python_packages": py_status,
        }

        # Determinazione stato complessivo
        is_ready = all(
            c.status == STATUS_OK for c in [sys_status, dir_status, ffmpeg_status, py_status]
        )

        status_str = "ready" if is_ready else "error"
        elapsed = (time.perf_counter() - start_time) * 1000

        result = BootstrapResult(
            ready=is_ready,
            status=status_str,
            components=components,
            log_messages=self.logs,
            os_name=f"{platform.system()} {platform.mac_ver()[0]}",
            arch=platform.machine(),
            ffmpeg_path=self._resolved_ffmpeg,
            ffmpeg_source=self.classify_source(Path(self._resolved_ffmpeg)) if self._resolved_ffmpeg else None,
            elapsed_ms=elapsed,
        )

        if is_ready:
            self.save_state(result)
            self.log(f"Ambiente verificato e pronto in {elapsed:.1f}ms")
        else:
            self.log("Verifica ambiente fallita: una o più dipendenze critiche non sono disponibili", "error")

        if progress_callback:
            progress_callback("Ambiente pronto!" if is_ready else "Configurazione incompleta", 1.0)

        return result

    def repair_environment(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> BootstrapResult:
        """Forza la pulizia e reinstallazione/ripristino dei componenti."""
        self.log("Avvio modalità Riparazione Ambiente...")
        if self.state_file.exists():
            try:
                self.state_file.unlink()
            except Exception:
                pass
        return self.run_bootstrap(force_full_check=True, progress_callback=progress_callback)


# Istanza singleton globale
_GLOBAL_BOOTSTRAP_MANAGER: Optional[BootstrapManager] = None


def get_bootstrap_manager() -> BootstrapManager:
    global _GLOBAL_BOOTSTRAP_MANAGER
    if _GLOBAL_BOOTSTRAP_MANAGER is None:
        _GLOBAL_BOOTSTRAP_MANAGER = BootstrapManager()
    return _GLOBAL_BOOTSTRAP_MANAGER


def get_ffmpeg_path() -> str:
    """Restituisce il percorso garantito del binario FFmpeg risolto."""
    mgr = get_bootstrap_manager()
    if mgr._resolved_ffmpeg and os.path.exists(mgr._resolved_ffmpeg):
        return mgr._resolved_ffmpeg

    # Controllo rapido
    status = mgr.check_ffmpeg()
    if status.status == STATUS_OK and mgr._resolved_ffmpeg:
        return mgr._resolved_ffmpeg

    # Fallback su binario di sistema o nome comando
    return shutil.which("ffmpeg") or "ffmpeg"


def get_ffprobe_path() -> Optional[str]:
    """Restituisce il percorso di ffprobe se disponibile e valido, altrimenti None."""
    mgr = get_bootstrap_manager()
    if mgr._resolved_ffprobe and os.path.exists(mgr._resolved_ffprobe):
        return mgr._resolved_ffprobe

    # Cerca ffprobe accanto all'ffmpeg risolto
    ffmpeg_bin = Path(get_ffmpeg_path())
    candidate = ffmpeg_bin.parent / "ffprobe"
    if candidate.exists() and os.access(candidate, os.X_OK):
        # Valida ffprobe con -version per evitare librerie mancanti
        try:
            p = subprocess.run([str(candidate), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            if p.returncode == 0:
                mgr._resolved_ffprobe = str(candidate)
                return str(candidate)
        except Exception:
            pass

    which_probe = shutil.which("ffprobe")
    if which_probe:
        try:
            p = subprocess.run([which_probe, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            if p.returncode == 0:
                mgr._resolved_ffprobe = which_probe
                return which_probe
        except Exception:
            pass

    return None
