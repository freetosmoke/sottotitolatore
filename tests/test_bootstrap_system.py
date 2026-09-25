"""
tests/test_bootstrap_system.py
Suite di test completa per il sistema di Bootstrap, Environment Check e Riparazione di Sub Studio.

Scenari coperti:
1. Verifica rilevamento ambiente e architettura Apple Silicon / macOS.
2. Risoluzione prioritaria di FFmpeg (bundle > local > data_dir > path).
3. Test Fast-Path: avvii successivi istantanei senza rieseguire controlli pesanti (<50ms).
4. Simulazione dipendenza mancante / corrotta e recupero automatico.
5. Verifica funzionamento modalità REPAIR.
6. Test risoluzione binari globali.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Assicura importazione dalla cartella root del progetto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bootstrap_manager import (
    BootstrapManager,
    STATUS_OK,
    STATUS_MISSING,
    STATUS_CORRUPTED,
    get_ffmpeg_path,
    get_ffprobe_path,
)


def run_all_tests():
    print("========================================================")
    print("🧪 AVVIO TEST SUITE: BOOTSTRAP & ENVIRONMENT INITIALIZER")
    print("========================================================")

    passed = 0
    failed = 0

    def test(name, func):
        nonlocal passed, failed
        try:
            print(f"▶ Esecuzione: {name}...", end=" ", flush=True)
            func()
            print("✅ PASS")
            passed += 1
        except Exception as e:
            print(f"❌ FAIL: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    def test_system_and_arch():
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = BootstrapManager(data_dir=Path(tmp_dir))
            sys_status = mgr.check_system()
            arch_status = mgr.check_architecture()

            assert sys_status.status == STATUS_OK, f"Status non OK: {sys_status.status}"
            assert "macOS" in sys_status.title, f"Titolo errato: {sys_status.title}"
            assert arch_status.status == STATUS_OK
            assert arch_status.details["is_apple_silicon"] is True or arch_status.details["arch"] in ("arm64", "x86_64")

    def test_directories():
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            mgr = BootstrapManager(data_dir=data_dir)
            status = mgr.check_and_create_directories()
            assert status.status == STATUS_OK
            assert (data_dir / "web_uploads").exists()
            assert (data_dir / "web_outputs").exists()
            assert (data_dir / "bin").exists()
            assert (data_dir / "models").exists()

    def test_ffmpeg_resolution():
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = BootstrapManager(data_dir=Path(tmp_dir))
            candidates = mgr.get_ffmpeg_candidates()
            assert len(candidates) > 0

            status = mgr.check_ffmpeg()
            assert status.status == STATUS_OK
            assert mgr._resolved_ffmpeg is not None
            assert os.path.exists(mgr._resolved_ffmpeg)
            assert os.access(mgr._resolved_ffmpeg, os.X_OK)
            assert status.details.get("videotoolbox") is True

    def test_fast_path():
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = BootstrapManager(data_dir=Path(tmp_dir))
            # Primo avvio completo
            res1 = mgr.run_bootstrap(force_full_check=True)
            assert res1.ready is True
            assert mgr.state_file.exists()

            # Secondo avvio: fast-path
            res2 = mgr.run_bootstrap(force_full_check=False)
            assert res2.ready is True
            assert res2.elapsed_ms < 50.0, f"Fast-path troppo lento: {res2.elapsed_ms}ms"

    def test_corrupted_ffmpeg_handling():
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            mgr = BootstrapManager(data_dir=data_dir)
            fake_bin = data_dir / "bin" / "ffmpeg"
            fake_bin.parent.mkdir(parents=True, exist_ok=True)
            fake_bin.write_text("CORRUPTED_NOT_A_MACH_O_BINARY")
            os.chmod(fake_bin, 0o755)

            status, ver, vtb, err = mgr.validate_ffmpeg_binary(fake_bin)
            assert status == STATUS_CORRUPTED
            assert err is not None

    def test_repair():
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = BootstrapManager(data_dir=Path(tmp_dir))
            mgr.run_bootstrap(force_full_check=True)
            assert mgr.state_file.exists()

            # Repair
            res_repair = mgr.repair_environment()
            assert res_repair.ready is True
            assert mgr.state_file.exists()

    def test_global_getters():
        ffmpeg_p = get_ffmpeg_path()
        assert ffmpeg_p is not None
        assert os.path.exists(ffmpeg_p)
        assert os.access(ffmpeg_p, os.X_OK)

        probe_p = get_ffprobe_path()
        if probe_p:
            assert os.path.exists(probe_p)

    def test_real_download_without_homebrew():
        orig_disable = os.environ.get("SUBSTUDIO_DISABLE_HOMEBREW")
        orig_path = os.environ.get("PATH")
        workspace_ffmpeg = Path(__file__).resolve().parent.parent / "bin" / "ffmpeg"
        backup_ffmpeg = Path(__file__).resolve().parent.parent / "bin" / "ffmpeg.test_bak"

        try:
            # 1. Rimuovi temporaneamente la copia del workspace
            if workspace_ffmpeg.exists():
                workspace_ffmpeg.rename(backup_ffmpeg)

            # 2. Disabilita esplicitamente Homebrew e pulisci il PATH
            os.environ["SUBSTUDIO_DISABLE_HOMEBREW"] = "1"
            os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"

            with tempfile.TemporaryDirectory() as tmp_dir:
                data_dir = Path(tmp_dir)
                mgr = BootstrapManager(data_dir=data_dir)

                # Verifica preliminare: nessun FFmpeg deve essere presente prima del download
                pre_status = mgr.check_ffmpeg()
                assert pre_status.status == STATUS_MISSING, f"FFmpeg non doveva essere presente: {pre_status}"

                # 3. Esegui il Bootstrap autonomo (deve scaricare senza Homebrew)
                res = mgr.run_bootstrap(force_full_check=True)

                assert res.ready is True, f"Bootstrap fallito: {res.log_messages}"
                assert res.ffmpeg_source == "USER DATA", f"Sorgente inattesa: {res.ffmpeg_source}"
                assert Path(res.ffmpeg_path).resolve() == (data_dir / "bin" / "ffmpeg").resolve()
                assert os.path.exists(res.ffmpeg_path)
                assert os.access(res.ffmpeg_path, os.X_OK)

                # 4. Verifica videoToolbox
                ffmpeg_comp = res.components.get("ffmpeg")
                assert ffmpeg_comp is not None
                assert ffmpeg_comp.status == STATUS_OK
                assert ffmpeg_comp.details.get("videotoolbox") is True

        finally:
            # Ripristina ambiente
            if backup_ffmpeg.exists():
                backup_ffmpeg.rename(workspace_ffmpeg)
            if orig_disable is not None:
                os.environ["SUBSTUDIO_DISABLE_HOMEBREW"] = orig_disable
            else:
                os.environ.pop("SUBSTUDIO_DISABLE_HOMEBREW", None)
            if orig_path is not None:
                os.environ["PATH"] = orig_path

    test("1. Rilevamento Sistema & Architettura CPU", test_system_and_arch)
    test("2. Creazione Directory & Permessi Dati", test_directories)
    test("3. Risoluzione Prioritaria FFmpeg & VideoToolbox", test_ffmpeg_resolution)
    test("4. Fast-Path Caching (avvio <50ms)", test_fast_path)
    test("5. Rilevamento Binario Corrotto / Non Valido", test_corrupted_ffmpeg_handling)
    test("6. Modalità REPAIR e Ripristino Automatico", test_repair)
    test("7. Getters Globali get_ffmpeg_path / get_ffprobe_path", test_global_getters)
    test("8. DOWNLOAD REALE FFmpeg (SENZA Homebrew)", test_real_download_without_homebrew)

    print("========================================================")
    print(f"📊 RISULTATO TEST: {passed} passati, {failed} falliti")
    print("========================================================")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
