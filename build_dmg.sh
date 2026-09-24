#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
DMG_NAME="Sottotitolatore-Apple-Silicon.dmg"
OUTPUT_DMG="$DIR/$DMG_NAME"
STAGING_DIR="$DIR/dmg_staging"
APP_BUNDLE="$DIR/dist/Sottotitolatore.app"

echo "🔨 1/3 Compilazione app bundle Sottotitolatore.app..."
"$DIR/build_app.sh"

echo "📂 2/3 Preparazione staging DMG con symlink /Applications..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

mkdir -p "$STAGING_DIR/Sottotitolatore.app"
(cd "$APP_BUNDLE" && tar -cf - .) | (cd "$STAGING_DIR/Sottotitolatore.app" && tar -xf -)
ln -s /Applications "$STAGING_DIR/Applicazioni"

echo "💿 3/3 Creazione immagine disco DMG compressa (UDZO)..."
rm -f "$OUTPUT_DMG"

hdiutil create \
    -volname "Sottotitolatore" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$OUTPUT_DMG"

rm -rf "$STAGING_DIR"

echo ""
echo "🎉 DMG creato con successo!"
echo "📍 Percorso: $OUTPUT_DMG"
ls -lh "$OUTPUT_DMG"
