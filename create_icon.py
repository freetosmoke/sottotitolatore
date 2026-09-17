#!/usr/bin/env python3
"""
Genera l'icona per Sottotitolatore.app (AppIcon.icns) in formato macOS nativo.
"""
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def generate_icon():
    base_dir = Path(__file__).resolve().parent
    iconset_dir = base_dir / "AppIcon.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir(parents=True, exist_ok=True)

    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base squircle macOS (arrotondamento Apple standard)
    pad = 64
    box = [pad, pad, size - pad, size - pad]
    radius = 200

    # Maschera arrotondata
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(box, radius=radius, fill=255)

    # Immagine sfondo sfumata da grafite scuro a nero profondo
    bg = Image.new("RGBA", (size, size), (18, 20, 26, 255))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(pad, size - pad):
        factor = (y - pad) / (size - 2 * pad)
        r = int(24 * (1 - factor) + 12 * factor)
        g = int(26 * (1 - factor) + 14 * factor)
        b = int(32 * (1 - factor) + 18 * factor)
        bg_draw.line([(pad, y), (size - pad, y)], fill=(r, g, b, 255))

    img.paste(bg, (0, 0), mask=mask)

    # Bordo raffinato ambrato/dorato
    draw.rounded_rectangle(box, radius=radius, outline=(245, 158, 11, 200), width=8)

    # 2. Elementi grafici centrali:
    # Simbolo fumetto / riquadro sottotitoli con gradiente ambra
    sub_box = [230, 270, 794, 650]
    sub_radius = 48
    draw.rounded_rectangle(sub_box, radius=sub_radius, fill=(30, 34, 44, 255), outline=(251, 191, 36, 255), width=10)

    # Linea 1: barra lunga ambrata
    draw.rounded_rectangle([300, 360, 724, 410], radius=16, fill=(245, 158, 11, 255))
    # Linea 2: parola evidenziata in grassetto oro + parola secondaria bianca
    draw.rounded_rectangle([300, 440, 520, 490], radius=16, fill=(251, 191, 36, 255))
    draw.rounded_rectangle([550, 440, 724, 490], radius=16, fill=(226, 232, 240, 200))
    # Linea 3: barra sottotitoli
    draw.rounded_rectangle([300, 520, 640, 560], radius=14, fill=(148, 163, 184, 180))

    # Badge a forma di microfono/onda podcast in basso
    wave_y = 750
    center_x = size // 2
    bar_heights = [24, 48, 80, 120, 160, 110, 70, 40, 20]
    spacing = 40
    start_x = center_x - ((len(bar_heights) - 1) * spacing) // 2

    for i, h in enumerate(bar_heights):
        bx = start_x + i * spacing
        b_top = wave_y - h // 2
        b_bot = wave_y + h // 2
        draw.rounded_rectangle([bx - 8, b_top, bx + 8, b_bot], radius=8, fill=(245, 158, 11, 230))

    # Salva le varie risoluzioni richieste da macOS per .iconset
    icon_sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for s, name in icon_sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / name)

    # Crea il file .icns con iconutil
    icns_path = base_dir / "AppIcon.icns"
    subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)], check=True)
    shutil.rmtree(iconset_dir)
    print(f"✓ Icona macOS generata con successo: {icns_path}")

if __name__ == "__main__":
    generate_icon()
