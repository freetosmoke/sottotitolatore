#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path

def build():
    base_dir = Path(__file__).resolve().parent
    dist_dir = base_dir / "dist"
    app_dir = dist_dir / "SubStudio.app"
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    app_payload_dir = resources_dir / "app"
    python_target_dir = resources_dir / "python"
    dmg_staging = base_dir / "dmg_staging"
    output_dmg = base_dir / "SubStudio-Apple-Silicon.dmg"

    print("🚀 Inizio creazione pacchetto SubStudio per Apple Silicon...")

    # 1. Pulizia
    print("🧹 1/6 Pulizia cartelle di build...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    if dmg_staging.exists():
        shutil.rmtree(dmg_staging, ignore_errors=True)

    dist_dir.mkdir(parents=True, exist_ok=True)
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    app_payload_dir.mkdir(parents=True, exist_ok=True)

    # 2. Icona e Info.plist
    print("🎨 2/6 Configurazione metadati e icona macOS...")
    icon_src = base_dir / "AppIcon.icns"
    if not icon_src.exists():
        import create_icon
        create_icon.generate_icon()
    shutil.copy2(icon_src, resources_dir / "AppIcon.icns")

    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>it</string>
    <key>CFBundleExecutable</key>
    <string>SubStudio</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.salvatorepuglisi.substudio</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>SubStudio</string>
    <key>CFBundleDisplayName</key>
    <string>SubStudio</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>LSRequiresNativeExecution</key>
    <true/>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
    </array>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    (contents_dir / "Info.plist").write_text(plist_content, encoding="utf-8")
    (contents_dir / "PkgInfo").write_bytes(b"APPL????")

    # 3. Python standalone arm64 + pacchetti
    print("🐍 3/6 Copia runtime Python 3.12 Apple Silicon e librerie...")
    uv_python_dir = Path.home() / ".local/share/uv/python"
    py_standalone = uv_python_dir / "cpython-3.12.14-macos-aarch64-none"
    if not py_standalone.exists():
        py_standalone = uv_python_dir / "cpython-3.12-macos-aarch64-none"
    if not py_standalone.exists():
        candidates = list(uv_python_dir.glob("cpython-3.12*"))
        if candidates:
            py_standalone = candidates[0]
    shutil.copytree(
        py_standalone,
        python_target_dir,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )

    venv_packages = base_dir / ".venv/lib/python3.12/site-packages"
    target_packages = python_target_dir / "lib/python3.12/site-packages"
    shutil.copytree(
        venv_packages,
        target_packages,
        dirs_exist_ok=True,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.dist-info")
    )

    # 4. Codice sorgente e asset
    print("📂 4/6 Copia sorgenti, font e Web UI...")
    py_files = [
        "web_app.py", "transcriber.py", "subtitle_renderer.py",
        "video_renderer.py", "keyword_selector.py", "audio_extractor.py",
        "ass_generator.py", "silence_remover.py", "translator.py", "font_manager.py", "presets.json"
    ]
    for pf in py_files:
        src_file = base_dir / pf
        if src_file.exists():
            shutil.copy2(src_file, app_payload_dir / pf)

    shutil.copytree(base_dir / "fonts", app_payload_dir / "fonts", dirs_exist_ok=True)
    shutil.copytree(base_dir / "web_static", app_payload_dir / "web_static", dirs_exist_ok=True)

    bin_dir = resources_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for b_name in ["ffmpeg", "ffprobe"]:
        b_src = base_dir / "bin" / b_name
        if b_src.exists():
            shutil.copy2(b_src, bin_dir / b_name)
            (bin_dir / b_name).chmod(0o755)

    # Inclusione modello Whisper
    hf_snapshots = Path.home() / ".cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots"
    if hf_snapshots.exists():
        snapshots = [d for d in hf_snapshots.iterdir() if d.is_dir()]
        if snapshots:
            print(f"🤖 Inclusione modello Whisper small locale da {snapshots[0].name}...")
            dest_model = app_payload_dir / "models/small"
            dest_model.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(snapshots[0], dest_model, symlinks=False, dirs_exist_ok=True)
            print("✓ Modello Whisper integrato con successo!")

    # 5. Launcher script
    print("⚙️ 5/6 Creazione launcher SubStudio.app...")
    launcher_script = """#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENTS="$(cd "$DIR/.." && pwd)"
RESOURCES="$CONTENTS/Resources"
APP_DIR="$RESOURCES/app"
PYTHON_BIN="$RESOURCES/python/bin/python3"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export PYTHONHOME="$RESOURCES/python"
export PYTHONPATH="$APP_DIR:$RESOURCES/python/lib/python3.12/site-packages"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Cartella di output in Filmati
USER_DATA_DIR="$HOME/Movies/SubStudio"
mkdir -p "$USER_DATA_DIR/web_uploads" "$USER_DATA_DIR/web_outputs"
export SUBSTUDIO_DATA_DIR="$USER_DATA_DIR"
export SOTTOTITOLATORE_DATA_DIR="$USER_DATA_DIR"

if ! command -v ffmpeg &>/dev/null; then
    osascript -e 'display alert "FFmpeg non trovato" message "SubStudio richiede FFmpeg per il rendering video su Apple Silicon.\\n\\nPuoi installarlo aprendo il Terminale e digitando:\\nbrew install ffmpeg" as critical'
    exit 1
fi

PORT=8501
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT + 1))
    if [ $PORT -gt 8530 ]; then
        exit 1
    fi
done

export SUBSTUDIO_PORT=$PORT
export SOTTOTITOLATORE_PORT=$PORT

LOG_FILE="$HOME/Library/Logs/SubStudio.log"
mkdir -p "$HOME/Library/Logs"
echo "=== Avvio SubStudio su porta $PORT ($(date)) ===" > "$LOG_FILE"

cd "$APP_DIR"
"$PYTHON_BIN" web_app.py < /dev/null >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT SIGINT SIGTERM

for i in {1..30}; do
    if curl -s "http://localhost:$PORT/" >/dev/null 2>&1; then
        break
    fi
    sleep 0.3
done

open "http://localhost:$PORT"
wait "$SERVER_PID"
"""
    launcher_path = macos_dir / "SubStudio"
    launcher_path.write_text(launcher_script, encoding="utf-8")
    launcher_path.chmod(0o755)

    # 6. Creazione DMG
    print("💿 6/6 Creazione immagine disco DMG compressa (UDZO)...")
    dmg_staging.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, dmg_staging / "SubStudio.app", symlinks=True)
    try:
        os.symlink("/Applications", dmg_staging / "Applicazioni")
    except FileExistsError:
        pass

    if output_dmg.exists():
        output_dmg.unlink()

    cmd = [
        "hdiutil", "create",
        "-volname", "SubStudio",
        "-srcfolder", str(dmg_staging),
        "-ov",
        "-format", "UDZO",
        str(output_dmg)
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(dmg_staging, ignore_errors=True)

    dmg_size_mb = output_dmg.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 50)
    print(f"🎉 DMG CREATO CON SUCCESSO!")
    print(f"📍 Percorso: {output_dmg}")
    print(f"📦 Dimensione: {dmg_size_mb:.1f} MB")
    print("=" * 50)

if __name__ == "__main__":
    build()
