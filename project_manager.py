#!/usr/bin/env python3
"""
project_manager.py
Gestore persistente della Project Library per SubStudio.
Supporta:
- Creazione, elenco, aggiornamento, cancellazione e duplicazione progetti.
- Tipologia progetto: 'subtitles' (video + sottotitoli) oppure 'video_only'.
- Associazione media sicura e resiliente (percorsi relativi, memorizzazione filename/hash/size, fallback dinamico per media spostati).
- Generazione automatica di thumbnail video ad alta prestazione con FFmpeg.
- Atomic file writing per prevenire corruzione dei dati.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from bootstrap_manager import get_ffmpeg_path
from video_renderer import get_video_duration, get_video_dimensions

logger = logging.getLogger("project_manager")

WORKSPACE = Path(__file__).resolve().parent
DATA_DIR_ENV = os.environ.get("SUBSTUDIO_DATA_DIR", os.environ.get("SOTTOTITOLATORE_DATA_DIR"))
DATA_DIR = Path(DATA_DIR_ENV) if DATA_DIR_ENV else WORKSPACE
PROJECTS_DIR = DATA_DIR / "projects"
UPLOADS_DIR = DATA_DIR / "web_uploads"

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_project_id(raw_id: str | None = None) -> str:
    """Genera o sanitizza un ID univoco e sicuro per il file di progetto."""
    if raw_id:
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "", str(raw_id))
        if clean:
            return clean
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand_suffix = os.urandom(3).hex()
    return f"proj_{now_str}_{rand_suffix}"


def generate_video_thumbnail_base64(video_path: Path, max_width: int = 400) -> str:
    """
    Estrae rapidamente un fotogramma dal video come miniatura JPEG in base64.
    Usa ffmpeg con seeking rapido (-ss).
    """
    if not video_path.exists() or not video_path.is_file():
        return ""
    try:
        ffmpeg_bin = get_ffmpeg_path()
        dur = 0.0
        try:
            dur = get_video_duration(video_path)
        except Exception:
            dur = 0.0

        # Cerca a 1s o a metà se il video è brevissimo
        seek_pos = "0.5"
        if dur > 2.0:
            seek_pos = "1.0"
        elif dur > 0.5:
            seek_pos = str(round(dur * 0.25, 2))

        cmd = [
            ffmpeg_bin, "-y",
            "-ss", seek_pos,
            "-i", str(video_path.resolve()),
            "-frames:v", "1",
            "-vf", f"scale={max_width}:-1",
            "-q:v", "3",
            "-f", "image2",
            "pipe:1"
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
        if proc.returncode == 0 and proc.stdout:
            b64 = base64.b64encode(proc.stdout).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
    except Exception as exc:
        logger.warning(f"Generazione miniatura video fallita per {video_path}: {exc}")
    return ""


def resolve_media_location(media: dict[str, Any], project_id: str = "") -> dict[str, Any]:
    """
    Risolve dinamicamente il percorso reale del video.
    Se il file è stato spostato, tenta il recupero intelligente tra le directory note
    senza invalidare o perdere i sottotitoli e le impostazioni del progetto.
    """
    m = dict(media or {})
    server_path_str = m.get("server_path") or ""
    stored_name = m.get("stored_filename") or (Path(server_path_str).name if server_path_str else "")
    orig_name = m.get("filename") or stored_name

    candidates: list[Path] = []

    # 1. Percorso assoluto registrato
    if server_path_str:
        candidates.append(Path(server_path_str))

    # 2. UPLOADS_DIR con nome memorizzato
    if stored_name:
        candidates.append(UPLOADS_DIR / stored_name)

    # 3. UPLOADS_DIR con nome originale
    if orig_name and orig_name != stored_name:
        candidates.append(UPLOADS_DIR / orig_name)

    # 4. Cartella dedicata del progetto (se esiste)
    if project_id and stored_name:
        candidates.append(PROJECTS_DIR / project_id / stored_name)

    # 5. Cartella Movies/SubStudio dell'utente
    if stored_name:
        candidates.append(Path.home() / "Movies" / "SubStudio" / "web_uploads" / stored_name)

    # 6. WORKSPACE fallback
    if stored_name:
        candidates.append(WORKSPACE / "web_uploads" / stored_name)

    found_path: Optional[Path] = None
    for cand in candidates:
        try:
            if cand.exists() and cand.is_file() and cand.stat().st_size > 0:
                found_path = cand.resolve()
                break
        except Exception:
            continue

    if found_path:
        m["server_path"] = str(found_path)
        m["stored_filename"] = found_path.name
        m["url"] = f"/media/{found_path.name}"
        m["missing"] = False
        try:
            m["size"] = found_path.stat().st_size
        except Exception:
            pass
    else:
        m["missing"] = True
        logger.warning(f"File video non trovato per progetto {project_id}: {m}")

    return m


class ProjectManager:
    """
    Gestione della Project Library di SubStudio:
    - Salvataggio atomico su disco (JSON con formattazione leggibile)
    - Elenco progetti con metadati e miniature
    - Recupero e aggiornamento stato
    """

    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_file(self, project_id: str) -> Path:
        clean_id = _safe_project_id(project_id)
        return self.projects_dir / f"{clean_id}.json"

    def list_projects(self) -> list[dict[str, Any]]:
        """
        Ritorna la lista di tutti i progetti disponibili ordinati per data di ultima modifica decrescente.
        Include metadati leggeri, stato media e miniatura per rendering immediato.
        """
        projects: list[dict[str, Any]] = []
        for json_file in self.projects_dir.glob("*.json"):
            if not json_file.is_file():
                continue
            try:
                content = json_file.read_text(encoding="utf-8")
                data = json.loads(content)
                pid = data.get("id") or json_file.stem
                # Risoluzione dinamica media
                media = data.get("media") or {}
                media = resolve_media_location(media, pid)

                item = {
                    "id": pid,
                    "name": data.get("name") or "Nuovo Progetto",
                    "type": data.get("type", "subtitles"),  # 'subtitles' | 'video_only'
                    "created_at": data.get("created_at") or "",
                    "updated_at": data.get("updated_at") or "",
                    "duration": data.get("duration", media.get("duration", 0.0)),
                    "resolution": data.get("resolution", {"width": 1080, "height": 1920}),
                    "status": data.get("status", "ready"),
                    "thumbnail": data.get("thumbnail") or "",
                    "chunks_count": len(data.get("chunks") or []),
                    "video_clips_count": len(data.get("video_clips") or []),
                    "media": {
                        "filename": media.get("filename") or "",
                        "stored_filename": media.get("stored_filename") or "",
                        "url": media.get("url") or "",
                        "missing": media.get("missing", False),
                        "size": media.get("size", 0),
                        "duration": media.get("duration", 0.0),
                    },
                    "settings": data.get("settings") or {},
                }
                projects.append(item)
            except Exception as exc:
                logger.error(f"Errore caricamento progetto {json_file}: {exc}")

        # Ordina per data di modifica più recente
        def _sort_key(p: dict[str, Any]) -> str:
            return p.get("updated_at") or p.get("created_at") or ""

        projects.sort(key=_sort_key, reverse=True)
        return projects

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """
        Ritorna il payload completo di un progetto per l'apertura nell'editor.
        Verifica e aggiorna lo stato dei media.
        """
        pfile = self._get_project_file(project_id)
        if not pfile.exists():
            return None
        try:
            content = pfile.read_text(encoding="utf-8")
            data = json.loads(content)
            # Risoluzione percorso media
            if "media" in data and isinstance(data["media"], dict):
                data["media"] = resolve_media_location(data["media"], project_id)
            return data
        except Exception as exc:
            logger.error(f"Errore lettura progetto {project_id}: {exc}")
            return None

    def save_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Salva o aggiorna un progetto atomicamente.
        Genera automaticamente ID, timestamp, metadati media e miniatura se mancanti.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        raw_id = payload.get("id")
        project_id = _safe_project_id(raw_id)
        pfile = self._get_project_file(project_id)

        # Se il progetto esiste già, carica i dati preesistenti per non perdere campi non inviati
        existing_data: dict[str, Any] = {}
        if pfile.exists():
            try:
                existing_data = json.loads(pfile.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Tipo progetto: 'subtitles' o 'video_only'
        project_type = str(payload.get("type") or existing_data.get("type") or "subtitles").strip().lower()
        if project_type not in ("subtitles", "video_only"):
            project_type = "subtitles"

        # Media handling
        media_input = payload.get("media") or existing_data.get("media") or {}
        media = resolve_media_location(media_input, project_id)

        # Se non c'è ancora la miniatura e abbiamo un video valido, proviamo a generarla
        thumbnail = payload.get("thumbnail") or existing_data.get("thumbnail") or ""
        server_path_str = media.get("server_path")
        if not thumbnail and server_path_str:
            p_video = Path(server_path_str)
            if p_video.exists():
                thumbnail = generate_video_thumbnail_base64(p_video, max_width=400)

        # Durata e risoluzione
        duration = float(payload.get("duration") or existing_data.get("duration") or media.get("duration") or 0.0)
        if duration <= 0 and server_path_str:
            try:
                duration = get_video_duration(Path(server_path_str))
            except Exception:
                pass
        media["duration"] = duration

        resolution = payload.get("resolution") or existing_data.get("resolution")
        if not resolution and server_path_str:
            try:
                w, h = get_video_dimensions(Path(server_path_str))
                resolution = {"width": w, "height": h}
            except Exception:
                resolution = {"width": 1080, "height": 1920}
        elif not resolution:
            resolution = {"width": 1080, "height": 1920}

        created_at = existing_data.get("created_at") or payload.get("created_at") or now_iso

        project_data: dict[str, Any] = {
            "version": 1,
            "id": project_id,
            "name": str(payload.get("name") or existing_data.get("name") or "Nuovo Progetto").strip(),
            "type": project_type,
            "status": str(payload.get("status") or existing_data.get("status") or "ready").strip(),
            "created_at": created_at,
            "updated_at": now_iso,
            "duration": round(duration, 2),
            "resolution": resolution,
            "thumbnail": thumbnail,
            "media": media,
            "settings": payload.get("settings") or existing_data.get("settings") or {
                "language": "it",
                "speaker_detection": True,
                "num_speakers": "auto",
                "activePresetId": payload.get("activePresetId") or "voce_del_successo",
            },
            "activePresetId": payload.get("activePresetId") or existing_data.get("activePresetId") or "voce_del_successo",
            "chunks": payload.get("chunks", existing_data.get("chunks", [])),
            "video_clips": payload.get("video_clips", existing_data.get("video_clips", [])),
            "allOriginalWords": payload.get("allOriginalWords", existing_data.get("allOriginalWords", [])),
            "snapshot": payload.get("snapshot", existing_data.get("snapshot", {})),
        }

        # Scrittura atomica per sicurezza
        tmp_file = pfile.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_file.replace(pfile)

        logger.info(f"Progetto salvato con successo: {project_id} ('{project_data['name']}')")
        return project_data

    def delete_project(self, project_id: str) -> bool:
        """Elimina il file di progetto dalla libreria."""
        pfile = self._get_project_file(project_id)
        if pfile.exists():
            try:
                pfile.unlink()
                logger.info(f"Progetto eliminato: {project_id}")
                return True
            except Exception as exc:
                logger.error(f"Errore cancellazione progetto {project_id}: {exc}")
                return False
        return False

    def duplicate_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Duplica un progetto esistente creando una copia con nuovo ID."""
        original = self.get_project(project_id)
        if not original:
            return None

        copy_data = dict(original)
        copy_data["id"] = ""  # Force new ID
        orig_name = original.get("name", "Progetto")
        copy_data["name"] = f"{orig_name} (Copia)"
        copy_data["created_at"] = ""
        copy_data["updated_at"] = ""
        return self.save_project(copy_data)


_global_pm: Optional[ProjectManager] = None

def get_project_manager() -> ProjectManager:
    """Singleton accessor per il ProjectManager di SubStudio."""
    global _global_pm
    if _global_pm is None:
        _global_pm = ProjectManager()
    return _global_pm
