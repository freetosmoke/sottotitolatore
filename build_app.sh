#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$DIR/dist"
APP_DIR="$DIST_DIR/Sottotitolatore.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
APP_PAYLOAD_DIR="$RESOURCES_DIR/app"
PYTHON_TARGET_DIR="$RESOURCES_DIR/python"

echo "🧹 1. Pulizia build precedenti..."
chmod -R u+w "$DIST_DIR" 2>/dev/null || true
rm -rf "$DIST_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR" "$APP_PAYLOAD_DIR" "$PYTHON_TARGET_DIR"

echo "🎨 2. Copia icona macOS..."
if [ ! -f "$DIR/AppIcon.icns" ]; then
    .venv/bin/python "$DIR/create_icon.py"
fi
cp -f "$DIR/AppIcon.icns" "$RESOURCES_DIR/AppIcon.icns"

echo "📝 3. Generazione Info.plist e PkgInfo..."
cat << 'PLIST' > "$CONTENTS_DIR/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>it</string>
    <key>CFBundleExecutable</key>
    <string>Sottotitolatore</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.salvatorepuglisi.sottotitolatore</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Sottotitolatore</string>
    <key>CFBundleDisplayName</key>
    <string>Sottotitolatore</string>
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
PLIST

echo -n "APPL????" > "$CONTENTS_DIR/PkgInfo"

echo "🐍 4. Copia runtime Python 3.12 standalone (Apple Silicon arm64)..."
PYTHON_STANDALONE=$(find "$HOME/.local/share/uv/python" -maxdepth 1 -type d -name "cpython-3.12*" 2>/dev/null | head -n 1)
if [ -z "$PYTHON_STANDALONE" ] || [ ! -d "$PYTHON_STANDALONE" ]; then
    uv python install 3.12
    PYTHON_STANDALONE=$(find "$HOME/.local/share/uv/python" -maxdepth 1 -type d -name "cpython-3.12*" 2>/dev/null | head -n 1)
fi

rsync -a "$PYTHON_STANDALONE/" "$PYTHON_TARGET_DIR/"

echo "📦 5. Copia pacchetti Python (faster-whisper, Pillow, ctranslate2, ecc.)..."
rsync -a "$DIR/.venv/lib/python3.12/site-packages/" "$PYTHON_TARGET_DIR/lib/python3.12/site-packages/"

echo "📂 6. Copia codice applicazione e asset..."
cp -f "$DIR"/web_app.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/transcriber.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/subtitle_renderer.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/video_renderer.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/keyword_selector.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/audio_extractor.py "$APP_PAYLOAD_DIR/"
cp -f "$DIR"/ass_generator.py "$APP_PAYLOAD_DIR/"
[ -f "$DIR"/translator.py ] && cp -f "$DIR"/translator.py "$APP_PAYLOAD_DIR/"
rsync -a "$DIR/fonts" "$APP_PAYLOAD_DIR/"
rsync -a "$DIR/web_static" "$APP_PAYLOAD_DIR/"

echo "🤖 7. Inclusione modello Whisper small locale (offline)..."
WHISPER_CACHE_SNAPSHOT=$(find "$HOME/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [ -n "$WHISPER_CACHE_SNAPSHOT" ] && [ -d "$WHISPER_CACHE_SNAPSHOT" ]; then
    mkdir -p "$APP_PAYLOAD_DIR/models/small"
    rsync -aL "$WHISPER_CACHE_SNAPSHOT/" "$APP_PAYLOAD_DIR/models/small/"
    echo "✓ Modello Whisper small integrato con successo"
else
    echo "⚠ Snapshot Whisper non trovato in cache, il modello verrà scaricato al primo avvio"
fi

echo "🚀 8. Compilazione launcher nativo Cocoa/WebKit arm64..."
clang -O2 -fobjc-arc \
    -target arm64-apple-macos12.0 \
    -framework Cocoa \
    -framework WebKit \
    "$DIR/launcher.m" \
    -o "$MACOS_DIR/Sottotitolatore"

chmod +x "$MACOS_DIR/Sottotitolatore"

echo "✓ Sottotitolatore.app creata con successo in $DIST_DIR/Sottotitolatore.app"
