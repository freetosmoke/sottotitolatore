#!/usr/bin/env python3
"""
misura_frame.py
Analizza un frame PNG estratto da un video con i sottotitoli già corretti
e rileva automaticamente le posizioni Y e le altezze del testo bianco.

Uso:
    python misura_frame.py --frame ~/Downloads/frame_ref.png
"""
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Installa le dipendenze: pip install Pillow numpy")
    sys.exit(1)


def find_white_text_bands(img_path: Path, threshold: int = 200) -> list[dict]:
    """
    Rileva le bande orizzontali di pixel bianchi (testo) nell'immagine.
    Restituisce lista di {y_top, y_bottom, y_center, height, x_left, x_right, width}.
    """
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    w, h = img.size
    print(f"\n📐 Dimensioni video: {w} × {h} px")

    # Maschera pixel bianchi (R,G,B tutti > threshold)
    white_mask = (arr[:, :, 0] > threshold) & \
                 (arr[:, :, 1] > threshold) & \
                 (arr[:, :, 2] > threshold)

    # Conta pixel bianchi per riga
    white_per_row = white_mask.sum(axis=1)

    # Riga "attiva" = ha almeno MIN_WHITE pixel bianchi consecutivi
    MIN_WHITE = max(10, w // 80)
    active_rows = white_per_row >= MIN_WHITE

    # Raggruppa le righe attive in bande
    bands = []
    in_band = False
    start = 0
    for y in range(h):
        if active_rows[y] and not in_band:
            in_band = True
            start = y
        elif not active_rows[y] and in_band:
            in_band = False
            band_h = y - start
            if band_h >= 8:   # ignora bande troppo sottili (rumore)
                # Trova estensione orizzontale della banda
                band_rows = white_mask[start:y, :]
                x_indices = np.where(band_rows.any(axis=0))[0]
                x_left  = int(x_indices.min()) if len(x_indices) else 0
                x_right = int(x_indices.max()) if len(x_indices) else w
                bands.append({
                    "y_top":    start,
                    "y_bottom": y,
                    "y_center": (start + y) // 2,
                    "height":   band_h,
                    "x_left":   x_left,
                    "x_right":  x_right,
                    "width":    x_right - x_left,
                })
    if in_band:
        bands.append({"y_top": start, "y_bottom": h, "y_center": (start+h)//2,
                      "height": h-start, "x_left": 0, "x_right": w, "width": w})

    # Unisci bande molto vicine (< 15px di gap) → appartengono alla stessa riga di testo
    merged = []
    for b in bands:
        if merged and b["y_top"] - merged[-1]["y_bottom"] < 15:
            prev = merged[-1]
            prev["y_bottom"] = b["y_bottom"]
            prev["y_center"] = (prev["y_top"] + prev["y_bottom"]) // 2
            prev["height"]   = prev["y_bottom"] - prev["y_top"]
            prev["x_left"]   = min(prev["x_left"],  b["x_left"])
            prev["x_right"]  = max(prev["x_right"], b["x_right"])
            prev["width"]    = prev["x_right"] - prev["x_left"]
        else:
            merged.append(dict(b))

    return merged


def estimate_font_size(height_px: int) -> int:
    """Stima la dimensione font in pt dal pixel-height del glifo."""
    # Pillow con TrueType: ratio empirico ~1.15 tra font size e pixel height
    return round(height_px / 1.15)


def main():
    parser = argparse.ArgumentParser(description="Misura posizioni sottotitoli in un frame video.")
    parser.add_argument("--frame", "-f", required=True, help="Percorso del frame PNG da analizzare.")
    parser.add_argument("--threshold", "-t", type=int, default=200,
                        help="Soglia luminosità per rilevare pixel bianchi (default: 200).")
    args = parser.parse_args()

    frame_path = Path(args.frame).expanduser()
    if not frame_path.exists():
        print(f"❌ File non trovato: {frame_path}")
        sys.exit(1)

    bands = find_white_text_bands(frame_path, args.threshold)

    img = Image.open(frame_path)
    W, H = img.size

    if not bands:
        print("⚠️  Nessun testo bianco rilevato. Prova con --threshold 180 o scegli un frame con il testo visibile.")
        return

    print(f"\n{'='*60}")
    print(f"Trovate {len(bands)} zone di testo bianco:")
    print(f"{'='*60}")

    for i, b in enumerate(bands, 1):
        pct_y = b["y_center"] / H * 100
        fs    = estimate_font_size(b["height"])
        # Determina se è centrato orizzontalmente
        center_x = (b["x_left"] + b["x_right"]) // 2
        centered  = abs(center_x - W // 2) < W * 0.1
        label = "↔ centrato" if centered else f"⬅ x={b['x_left']}–{b['x_right']}"
        print(f"\n  Banda {i}:")
        print(f"    y_top      = {b['y_top']} px")
        print(f"    y_center   = {b['y_center']} px  ({pct_y:.1f}% dall'alto)  ← da usare come Y")
        print(f"    y_bottom   = {b['y_bottom']} px")
        print(f"    altezza    = {b['height']} px")
        print(f"    larghezza  = {b['width']} px  {label}")
        print(f"    font_size  ≈ {fs} pt  ← valore da mettere nel codice")

    if len(bands) >= 2:
        gap = bands[1]["y_center"] - bands[0]["y_center"]
        print(f"\n{'='*60}")
        print(f"  Gap tra banda 1 e 2: {gap} px")
        print(f"\n  ✅ Valori da inserire in subtitle_renderer.py:")
        print(f"     SUBTITLE_Y   = {bands[0]['y_center']}")
        print(f"     WATERMARK_Y  = {bands[1]['y_center']}")
        print(f"     FONT_SIZE_SUB = {estimate_font_size(bands[0]['height'])}")
        print(f"     FONT_SIZE_WM  = {estimate_font_size(bands[1]['height'])}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
