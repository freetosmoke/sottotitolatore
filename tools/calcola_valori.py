#!/usr/bin/env python3
"""
calcola_valori.py
Converte le misure dal video di riferimento (qualsiasi risoluzione)
ai valori corretti per il canvas 1080x1920 e aggiorna subtitle_renderer.py.

Uso:
    python calcola_valori.py --frame ~/Downloads/frame_ref.png
"""
import sys, argparse, re
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Installa: pip install Pillow numpy")
    sys.exit(1)

TARGET_W = 1080
TARGET_H = 1920


def find_text_bands(img_path, threshold=150, min_width_frac=0.05):
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    W, H = img.size

    white = (arr[:,:,0] > threshold) & (arr[:,:,1] > threshold) & (arr[:,:,2] > threshold)
    white_per_row = white.sum(axis=1)

    min_white = max(5, int(W * min_width_frac))
    active = white_per_row >= min_white

    bands, in_band, start = [], False, 0
    for y in range(H):
        if active[y] and not in_band:
            in_band, start = True, y
        elif not active[y] and in_band:
            in_band = False
            h = y - start
            if h >= 6:
                rows = white[start:y, :]
                xs = np.where(rows.any(axis=0))[0]
                bands.append({
                    "y_top": start, "y_bottom": y,
                    "y_center": (start + y) // 2,
                    "height": h,
                    "x_left": int(xs.min()) if len(xs) else 0,
                    "x_right": int(xs.max()) if len(xs) else W,
                    "width": int(xs.max()-xs.min()) if len(xs) else W,
                    "W": W, "H": H,
                })

    # Unisci bande vicine (< 20px)
    merged = []
    for b in bands:
        if merged and b["y_top"] - merged[-1]["y_bottom"] < 20:
            p = merged[-1]
            p["y_bottom"] = b["y_bottom"]
            p["y_center"] = (p["y_top"] + p["y_bottom"]) // 2
            p["height"]   = p["y_bottom"] - p["y_top"]
            p["x_left"]   = min(p["x_left"],  b["x_left"])
            p["x_right"]  = max(p["x_right"], b["x_right"])
            p["width"]    = p["x_right"] - p["x_left"]
        else:
            merged.append(dict(b))

    return merged, W, H


def scale_to_target(value, src_dim, tgt_dim):
    return round(value * tgt_dim / src_dim)


def pick_subtitle_and_watermark(bands, W, H):
    """
    Scegli le due bande più probabili: sottotitolo e watermark.
    Criteri:
    - Centrate orizzontalmente (|centro_x - W/2| < W*0.15)
    - y_center tra 35% e 75% dell'altezza
    - Larghezza > 5% del frame
    """
    candidates = []
    for b in bands:
        cx = (b["x_left"] + b["x_right"]) // 2
        pct_y = b["y_center"] / H
        centered = abs(cx - W//2) < W * 0.15
        in_range = 0.35 < pct_y < 0.75
        wide_enough = b["width"] > W * 0.05
        if centered and in_range and wide_enough:
            candidates.append(b)

    # Prendi le prime due (ordinate per y_center)
    candidates.sort(key=lambda b: b["y_center"])
    return candidates[:2]


def update_renderer(sub_y, wm_y, fs_sub, fs_wm):
    path = Path("subtitle_renderer.py")
    if not path.exists():
        print("⚠️  subtitle_renderer.py non trovato nella cartella corrente.")
        return
    text = path.read_text()
    replacements = [
        (r"^SUBTITLE_Y\s*=.*$",   f"SUBTITLE_Y   = {sub_y}"),
        (r"^WATERMARK_Y\s*=.*$",  f"WATERMARK_Y  = {wm_y}"),
        (r"^FONT_SIZE_SUB\s*=.*$",f"FONT_SIZE_SUB = {fs_sub}"),
        (r"^FONT_SIZE_WM\s*=.*$", f"FONT_SIZE_WM  = {fs_wm}"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.MULTILINE)
    path.write_text(text)
    print(f"\n✅ subtitle_renderer.py aggiornato automaticamente!")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frame", "-f", required=True)
    p.add_argument("--threshold", "-t", type=int, default=150)
    p.add_argument("--apply", action="store_true",
                   help="Aggiorna subtitle_renderer.py con i valori calcolati.")
    args = p.parse_args()

    frame_path = Path(args.frame).expanduser()
    bands, W, H = find_text_bands(frame_path, args.threshold)

    print(f"\n📐 Risoluzione riferimento: {W}×{H}")
    print(f"🎯 Target output:           {TARGET_W}×{TARGET_H}")
    print(f"📊 Scala: ×{TARGET_W/W:.3f} (W)  ×{TARGET_H/H:.3f} (H)")
    print(f"\nBande di testo trovate: {len(bands)}")
    for i, b in enumerate(bands, 1):
        cx = (b["x_left"]+b["x_right"])//2
        print(f"  [{i}] y={b['y_center']}px ({b['y_center']/H*100:.1f}%)  "
              f"h={b['height']}px  w={b['width']}px  cx={cx}px")

    candidates = pick_subtitle_and_watermark(bands, W, H)

    if len(candidates) < 2:
        print(f"\n⚠️  Trovate solo {len(candidates)} bande valide (servono 2).")
        print("   Prova con --threshold 120 oppure scegli un frame con il testo ben visibile.")
        return

    sub, wm = candidates[0], candidates[1]

    # Converti nella risoluzione target
    sub_y  = scale_to_target(sub["y_center"], H, TARGET_H)
    wm_y   = scale_to_target(wm["y_center"],  H, TARGET_H)
    sub_h  = scale_to_target(sub["height"],   H, TARGET_H)
    wm_h   = scale_to_target(wm["height"],    H, TARGET_H)

    # Stima font size (ratio empirico Pillow: height ≈ font_size × 1.10)
    fs_sub = max(30, round(sub_h / 1.10 / 5) * 5)
    fs_wm  = max(20, round(wm_h  / 1.10 / 5) * 5)

    print(f"\n{'='*55}")
    print(f"  Sottotitolo (fonte {W}×{H}):")
    print(f"    y_center originale: {sub['y_center']}px  ({sub['y_center']/H*100:.1f}%)")
    print(f"    altezza  originale: {sub['height']}px")
    print(f"  Watermark:")
    print(f"    y_center originale: {wm['y_center']}px  ({wm['y_center']/H*100:.1f}%)")
    print(f"    altezza  originale: {wm['height']}px")
    print(f"\n  ✅ Valori per canvas {TARGET_W}×{TARGET_H}:")
    print(f"     SUBTITLE_Y   = {sub_y}")
    print(f"     WATERMARK_Y  = {wm_y}")
    print(f"     FONT_SIZE_SUB = {fs_sub}")
    print(f"     FONT_SIZE_WM  = {fs_wm}")
    print(f"     Gap           = {wm_y - sub_y}px")
    print(f"{'='*55}")

    if args.apply:
        update_renderer(sub_y, wm_y, fs_sub, fs_wm)
    else:
        print(f"\n  Aggiungi --apply per aggiornare subtitle_renderer.py automaticamente.")
        print(f"  Esempio:")
        print(f"    python calcola_valori.py --frame {args.frame} --apply")


if __name__ == "__main__":
    main()
