"""
test_typography.py — Script di test automatizzato per la libreria tipografica.

Verifica:
1. Catalogo font (Arial, Inter, Roboto, Montserrat, Poppins, Bebas Neue, Playfair Display, ecc.)
2. Varianti specifiche per famiglia (es. Bebas Neue solo Regular, Montserrat completa)
3. Risoluzione e caricamento Pillow per:
   - Arial (sistema)
   - Inter (Google)
   - Roboto (Google)
   - Montserrat (Google)
   - Poppins (Google)
   - Bebas Neue (Google)
   - Playfair Display (Google)
   - Font con Bold
   - Font con Italic
4. Rendering frame sottotitolo (render_subtitle) con cambio font e varianti
5. Export video completo (render_all + burn_subtitles) con il nuovo font
"""

import sys
import tempfile
from pathlib import Path

# Aggiunge la root del workspace al sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from PIL import Image

import font_manager
import subtitle_renderer
from video_renderer import burn_subtitles, get_video_duration, get_video_dimensions

def test_1_font_catalog():
    print("--- TEST 1: Verifica Catalogo Font ---")
    catalog = font_manager.get_all_fonts_catalog()
    sys_fonts = catalog["system_preinstalled"]
    families = {f["family"].lower(): f for f in sys_fonts}

    required = [
        "arial", "helvetica", "helvetica neue", "inter", "roboto", "open sans",
        "lato", "montserrat", "poppins", "raleway", "nunito", "nunito sans",
        "oswald", "bebas neue", "anton", "roboto condensed", "roboto slab",
        "merriweather", "playfair display", "dm sans", "manrope", "outfit",
        "plus jakarta sans", "space grotesk", "barlow", "barlow condensed",
        "fira sans", "source sans 3", "ubuntu", "work sans", "archivo",
        "ibm plex sans", "ibm plex serif", "libre baskerville",
        "cormorant garamond", "cinzel", "pacifico", "lobster"
    ]

    for req in required:
        assert req in families, f"Font obbligatorio mancante: {req}"
        entry = families[req]
        assert len(entry["variants"]) > 0, f"Nessuna variante per {req}"

    # Verifica varianti Bebas Neue (solo Regular)
    bebas = families["bebas neue"]
    assert len(bebas["variants"]) == 1 and bebas["variants"][0]["name"] == "Regular", \
        f"Bebas Neue deve avere solo Regular, trovato: {bebas['variants']}"

    # Verifica varianti Montserrat (10 varianti)
    mont = families["montserrat"]
    assert len(mont["variants"]) >= 10, f"Montserrat deve avere tutte le varianti, trovate: {len(mont['variants'])}"

    print("✔ Catalogo e varianti verificate con successo!")


def test_2_font_resolution():
    print("\n--- TEST 2: Risoluzione e Caricamento Pillow ---")
    test_cases = [
        ("Arial", "Regular"),
        ("Arial", "Bold"),
        ("Arial", "Italic"),
        ("Inter", "Regular"),
        ("Inter", "Bold"),
        ("Inter", "Italic"),
        ("Roboto", "Regular"),
        ("Roboto", "Bold"),
        ("Roboto", "Italic"),
        ("Montserrat", "Regular"),
        ("Montserrat", "Bold"),
        ("Montserrat", "Italic"),
        ("Poppins", "Regular"),
        ("Poppins", "Bold"),
        ("Poppins", "Italic"),
        ("Bebas Neue", "Regular"),
        ("Playfair Display", "Regular"),
        ("Playfair Display", "Bold"),
        ("Playfair Display", "Italic"),
    ]

    for fam, var in test_cases:
        f = font_manager.resolve_font(fam, var, 40)
        assert f is not None, f"Impossibile risolvere {fam} {var}"
        name = f.getname()
        print(f"  ✔ {fam} [{var}] caricato: {name}")

    print("✔ Tutti i font target caricati correttamente!")


def test_3_frame_rendering():
    print("\n--- TEST 3: Rendering Frame con Nuovi Font ---")
    with tempfile.TemporaryDirectory() as tmp_d:
        tmp_dir = Path(tmp_d)

        # Test A: Montserrat Light (normale) + Montserrat Bold (keyword)
        sub_png_1 = tmp_dir / "sub_montserrat.png"
        f_norm = subtitle_renderer.load_font_variant(50, "Montserrat", "Light")
        f_kw = subtitle_renderer.load_font_variant(50, "Montserrat", "Bold")

        subtitle_renderer.render_subtitle(
            words=["QUESTO", "È", "UN", "TEST", "MONTSERRAT"],
            bold_indices=[3, 4],
            light=f_norm,
            semibold=f_kw,
            out=sub_png_1,
            normal_color=(255, 255, 255, 255),
            keyword_color=(255, 215, 0, 255), # Oro per keyword
            canvas_width=1080,
            canvas_height=1920,
        )
        assert sub_png_1.exists() and sub_png_1.stat().st_size > 500, "Render frame Montserrat fallito"
        print("  ✔ Frame Montserrat renderizzato:", sub_png_1.stat().st_size, "bytes")

        # Test B: Playfair Display Italic (normale) + Bebas Neue Regular (keyword)
        sub_png_2 = tmp_dir / "sub_playfair_bebas.png"
        f_playfair = subtitle_renderer.load_font_variant(50, "Playfair Display", "Italic")
        f_bebas = subtitle_renderer.load_font_variant(50, "Bebas Neue", "Regular")

        subtitle_renderer.render_subtitle(
            words=["ELEGANTE", "E", "IMPATTO"],
            bold_indices=[2],
            light=f_playfair,
            semibold=f_bebas,
            out=sub_png_2,
            normal_color=(255, 255, 255, 255),
            keyword_color=(0, 255, 255, 255),
            canvas_width=1080,
            canvas_height=1920,
        )
        assert sub_png_2.exists() and sub_png_2.stat().st_size > 500, "Render frame Playfair+Bebas fallito"
        print("  ✔ Frame Playfair+Bebas renderizzato:", sub_png_2.stat().st_size, "bytes")

    print("✔ Rendering frame completato con successo!")


def test_4_video_export():
    print("\n--- TEST 4: Export Video con Nuovi Font ---")
    video_source = Path("web_uploads/uploaded_video.mp4")
    if not video_source.exists():
        video_source = Path("web_uploads/Download.mp4")
    if not video_source.exists():
        print("  ⚠ Nessun video di test trovato in web_uploads, salto test export video.")
        return

    duration = min(get_video_duration(video_source), 4.0) # Primi 4 secondi per test rapido
    w, h = get_video_dimensions(video_source)
    print(f"  Video sorgente: {video_source.name} ({w}x{h}, {duration:.1f}s)")

    chunks = [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "words": [
                {"word": "TEST", "start": 0.0, "end": 0.5},
                {"word": "POPPINS", "start": 0.5, "end": 1.0},
                {"word": "BOLD", "start": 1.0, "end": 2.0},
            ],
            "bold_indices": [1, 2],
            "text": "TEST POPPINS BOLD"
        },
        {
            "id": 1,
            "start": 2.0,
            "end": 4.0,
            "words": [
                {"word": "ROBOTO", "start": 2.0, "end": 3.0},
                {"word": "ITALIC", "start": 3.0, "end": 4.0},
            ],
            "bold_indices": [1],
            "text": "ROBOTO ITALIC"
        }
    ]

    preset = {
        "name": "Test Typography Preset",
        "font_name": "Poppins",
        "font_size_sub": 45,
        "font_size_wm": 25,
        "watermark_text": "@substudio",
        "offset_sub_x": 0,
        "offset_sub_y": 0,
        "offset_wm_x": 0,
        "offset_wm_y": 100,
        "subtitle_style": {
            "normal": {
                "font_family": "Poppins",
                "font_variant": "Regular",
                "color": "#FFFFFF"
            },
            "keyword": {
                "font_family": "Poppins",
                "font_variant": "Bold",
                "color": "#FFCC00"
            }
        },
        "keywords": {"enabled": True, "mode": "automatic"}
    }

    with tempfile.TemporaryDirectory() as tmp_d:
        tmp_dir = Path(tmp_d)
        rendered_chunks, ffconcat_path, wm_path = subtitle_renderer.render_all(
            chunks=chunks,
            work_dir=tmp_dir,
            total_duration=duration,
            preset=preset,
            canvas_width=w,
            canvas_height=h,
        )
        assert len(rendered_chunks) == 2, "Chunk non renderizzati"
        assert ffconcat_path.exists(), "ffconcat non generato"

        output_file = tmp_dir / "output_test_subtitled.mp4"
        burn_subtitles(
            video_path=video_source,
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=output_file,
            use_hw=True,
            quality="booster",
        )
        assert output_file.exists() and output_file.stat().st_size > 10000, "Video esportato vuoto o non creato"
        final_dur = get_video_duration(output_file)
        print(f"  ✔ Video esportato con successo: {output_file.name} ({output_file.stat().st_size} bytes, durata: {final_dur:.2f}s)")

    print("✔ Export video verificato con successo!")


if __name__ == "__main__":
    test_1_font_catalog()
    test_2_font_resolution()
    test_3_frame_rendering()
    test_4_video_export()
    print("\n🎉 TUTTI I TEST TIPOGRAFICI SONO STATI SUPERATI CON SUCCESSO! 🎉")
