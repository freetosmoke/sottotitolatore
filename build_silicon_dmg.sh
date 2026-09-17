#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="/tmp/sottotitolatore_app_build_$$"
STAGING_DIR="/tmp/sottotitolatore_dmg_staging_$$"
OUTPUT_DMG="$PROJECT_DIR/Sottotitolatore-Apple-Silicon.dmg"

echo "🚀 [1/5] Inizializzazione ambiente di build in $BUILD_DIR..."
rm -rf "$BUILD_DIR" "$STAGING_DIR"
mkdir -p "$BUILD_DIR/Sottotitolatore.app/Contents/MacOS"
mkdir -p "$BUILD_DIR/Sottotitolatore.app/Contents/Resources/app"

APP_DIR="$BUILD_DIR/Sottotitolatore.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
APP_PAYLOAD_DIR="$RESOURCES_DIR/app"
PYTHON_DIR="$RESOURCES_DIR/python"

echo "🎨 [2/5] Configurazione icona e Info.plist..."
if [ ! -f "$PROJECT_DIR/AppIcon.icns" ]; then
    .venv/bin/python "$PROJECT_DIR/create_icon.py"
fi
cp -f "$PROJECT_DIR/AppIcon.icns" "$RESOURCES_DIR/AppIcon.icns"

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
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.video</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST
echo -n "APPL????" > "$CONTENTS_DIR/PkgInfo"

echo "🐍 [3/5] Integrazione runtime Python 3.12 standalone (arm64 Apple Silicon) e pacchetti..."
PY_SRC=$(find "$HOME/.local/share/uv/python" -maxdepth 1 -type d -name "cpython-3.12*" 2>/dev/null | head -n 1)
if [ -z "$PY_SRC" ] || [ ! -d "$PY_SRC" ]; then
    uv python install 3.12
    PY_SRC=$(find "$HOME/.local/share/uv/python" -maxdepth 1 -type d -name "cpython-3.12*" 2>/dev/null | head -n 1)
fi

cp -R "$PY_SRC" "$PYTHON_DIR"

/opt/homebrew/bin/uv pip install -r "$PROJECT_DIR/requirements.txt" \
    --target "$PYTHON_DIR/lib/python3.12/site-packages" \
    --python "$PYTHON_DIR/bin/python3" --quiet

echo "📂 [4/5] Integrazione codice sorgente, font, Web UI e modello Whisper offline..."
cp -f "$PROJECT_DIR"/web_app.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/transcriber.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/subtitle_renderer.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/video_renderer.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/keyword_selector.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/audio_extractor.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/ass_generator.py "$APP_PAYLOAD_DIR/"
cp -f "$PROJECT_DIR"/translator.py "$APP_PAYLOAD_DIR/"
cp -R "$PROJECT_DIR"/fonts "$APP_PAYLOAD_DIR/"
cp -R "$PROJECT_DIR"/web_static "$APP_PAYLOAD_DIR/"

# Modello Whisper small
WHISPER_SNAPSHOT=$(find "$HOME/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1)
if [ -n "$WHISPER_SNAPSHOT" ] && [ -d "$WHISPER_SNAPSHOT" ]; then
    mkdir -p "$APP_PAYLOAD_DIR/models/small"
    cp -LR "$WHISPER_SNAPSHOT"/* "$APP_PAYLOAD_DIR/models/small/"
    echo "✓ Modello Whisper small (offline) integrato con successo"
fi

# Binari standalone (FFmpeg nativo Apple Silicon)
mkdir -p "$RESOURCES_DIR/bin"
cp -f "$PROJECT_DIR/bin/ffmpeg" "$RESOURCES_DIR/bin/ffmpeg"
chmod +x "$RESOURCES_DIR/bin/ffmpeg"
echo "✓ Binario statico FFmpeg (Apple Silicon arm64) integrato nel bundle"

# Launcher nativo Cocoa (arm64)
echo "🔨 Compilazione launcher nativo Cocoa Apple Silicon (arm64)..."
clang -O2 -arch arm64 -framework Cocoa -o "$MACOS_DIR/Sottotitolatore" "$PROJECT_DIR/launcher.m"
chmod +x "$MACOS_DIR/Sottotitolatore"

echo "✍️ Firma ad-hoc del bundle e di tutte le librerie interne..."
codesign --force --deep -s - "$APP_DIR"

echo "💿 [5/5] Creazione DMG compressa per Apple Silicon con hdiutil..."
mkdir -p "$STAGING_DIR"
cp -R "$APP_DIR" "$STAGING_DIR/Sottotitolatore.app"
ln -s /Applications "$STAGING_DIR/Applicazioni"

rm -f "$OUTPUT_DMG"
hdiutil create \
    -volname "Sottotitolatore" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$OUTPUT_DMG"

# Pulizia temporanei
rm -rf "$BUILD_DIR" "$STAGING_DIR"

echo ""
echo "========================================================"
echo "🎉 PACCHETTO INSTALLER DMG APPLE SILICON PRONTO!"
echo "📍 Percorso file: $OUTPUT_DMG"
ls -lh "$OUTPUT_DMG"
echo "========================================================"
