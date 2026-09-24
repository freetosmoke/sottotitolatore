"""
font_manager.py — Gestione centralizzata della libreria tipografica per il Sottotitolatore.

Fornisce:
- Catalogo centralizzato dei font con varianti reali (pesi e stili)
- Supporto per Google Fonts con download e caching automatico in ./fonts/google/
- Risoluzione dei font di sistema (Arial, Helvetica, Helvetica Neue su macOS)
- Rilevamento dinamico dei font personalizzati caricati in ./fonts/
- Risoluzione sicura per il rendering Pillow (Pillow ImageFont) con fallback intelligente
"""

import os
import re
import io
import json
import logging
import threading
import urllib.request
from pathlib import Path
from typing import Any, Optional
from PIL import ImageFont

logger = logging.getLogger("font_manager")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_FONTS_DIR = BASE_DIR / "fonts"
GOOGLE_FONTS_CACHE_DIR = PROJECT_FONTS_DIR / "google"

GOOGLE_FONTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Lock per il download thread-safe dei font
_DOWNLOAD_LOCK = threading.Lock()

# ── 1. DEFINIZIONE DEL CATALOGO TIPOGRAFICO ────────────────────────────────────

# Mappa globale delle varianti e pesi standard
STANDARD_VARIANTS = {
    "Thin": {"weight": 100, "style": "normal"},
    "ExtraLight": {"weight": 200, "style": "normal"},
    "Light": {"weight": 300, "style": "normal"},
    "Regular": {"weight": 400, "style": "normal"},
    "Medium": {"weight": 500, "style": "normal"},
    "SemiBold": {"weight": 600, "style": "normal"},
    "Bold": {"weight": 700, "style": "normal"},
    "ExtraBold": {"weight": 800, "style": "normal"},
    "Black": {"weight": 900, "style": "normal"},
    "Italic": {"weight": 400, "style": "italic"},
    "Bold Italic": {"weight": 700, "style": "italic"},
}

def _make_variants(*names: str) -> list[dict[str, Any]]:
    variants = []
    for name in names:
        if name in STANDARD_VARIANTS:
            v = dict(STANDARD_VARIANTS[name])
            v["name"] = name
            variants.append(v)
    return variants

# Catalogo completo di font predefiniti e ben organizzati
FONT_CATALOG: list[dict[str, Any]] = [
    # ── Font di sistema macOS ─────────────────────────────
    {
        "family": "Arial",
        "category": "sans-serif",
        "source": "system",
        "variants": _make_variants("Regular", "Bold", "Italic", "Bold Italic", "Black"),
    },
    {
        "family": "Helvetica",
        "category": "sans-serif",
        "source": "system",
        "variants": _make_variants("Light", "Regular", "Bold", "Italic", "Bold Italic"),
    },
    {
        "family": "Helvetica Neue",
        "category": "sans-serif",
        "source": "system",
        "variants": _make_variants("Thin", "Light", "Regular", "Medium", "Bold", "Black", "Italic", "Bold Italic"),
    },

    # ── Font locali del progetto ──────────────────────────
    {
        "family": "Raleway",
        "category": "sans-serif",
        "source": "local",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Alata",
        "category": "sans-serif",
        "source": "local",
        "variants": _make_variants("Regular"),
    },

    # ── Google Fonts (Open Source) ────────────────────────
    {
        "family": "Inter",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Roboto",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "Light", "Regular", "Medium", "Bold", "Black", "Italic"),
    },
    {
        "family": "Open Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Italic"),
    },
    {
        "family": "Lato",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "Light", "Regular", "Bold", "Black", "Italic"),
    },
    {
        "family": "Montserrat",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Poppins",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Nunito",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Nunito Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Oswald",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold"),
    },
    {
        "family": "Bebas Neue",
        "category": "display",
        "source": "google",
        "variants": _make_variants("Regular"),
    },
    {
        "family": "Anton",
        "category": "display",
        "source": "google",
        "variants": _make_variants("Regular"),
    },
    {
        "family": "Roboto Condensed",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "SemiBold", "Bold", "Black", "Italic"),
    },
    {
        "family": "Roboto Slab",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"),
    },
    {
        "family": "Merriweather",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Bold", "Black", "Italic"),
    },
    {
        "family": "Playfair Display",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "DM Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Manrope",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"),
    },
    {
        "family": "Outfit",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"),
    },
    {
        "family": "Plus Jakarta Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Italic"),
    },
    {
        "family": "Space Grotesk",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "SemiBold", "Bold"),
    },
    {
        "family": "Barlow",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Barlow Condensed",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Fira Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Source Sans 3",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "Black", "Italic"),
    },
    {
        "family": "Ubuntu",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "Bold", "Italic"),
    },
    {
        "family": "Work Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "Archivo",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black", "Italic"),
    },
    {
        "family": "IBM Plex Sans",
        "category": "sans-serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "Italic"),
    },
    {
        "family": "IBM Plex Serif",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "Italic"),
    },
    {
        "family": "Libre Baskerville",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Regular", "Bold", "Italic"),
    },
    {
        "family": "Cormorant Garamond",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Light", "Regular", "Medium", "SemiBold", "Bold", "Italic"),
    },
    {
        "family": "Cinzel",
        "category": "serif",
        "source": "google",
        "variants": _make_variants("Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"),
    },
    {
        "family": "Pacifico",
        "category": "handwriting",
        "source": "google",
        "variants": _make_variants("Regular"),
    },
    {
        "family": "Lobster",
        "category": "display",
        "source": "google",
        "variants": _make_variants("Regular"),
    },
]

# Lookup rapido per nome famiglia (case-insensitive)
CATALOG_BY_FAMILY = {f["family"].lower(): f for f in FONT_CATALOG}


# ── 2. SCANSIONE FONT PERSONALIZZATI (fonts/) ──────────────────────────────────

def scan_custom_fonts() -> list[dict[str, Any]]:
    """
    Rileva tutti i file di font personalizzati (.ttf, .otf) inseriti dall'utente in ./fonts/
    (esclusi i font standard Raleway/Alata e la cache di Google).
    """
    custom_families: dict[str, dict[str, Any]] = {}
    known_local_stems = {"alata-regular", "raleway-light", "raleway-semibold", "raleway-bold"}

    if not PROJECT_FONTS_DIR.exists():
        return []

    for f in PROJECT_FONTS_DIR.iterdir():
        if not f.is_file() or f.suffix.lower() not in (".ttf", ".otf"):
            continue
        if f.stem.lower() in known_local_stems:
            continue

        try:
            # Legge il nome della famiglia e della variante dai metadati del font
            probe = ImageFont.truetype(str(f), 24)
            names = probe.getname()
            fam_name = names[0] if names and names[0] else f.stem
            sub_name = names[1] if names and len(names) > 1 and names[1] else "Regular"

            # Normalizza variante
            v_name = "Regular"
            sub_lower = sub_name.lower()
            if "thin" in sub_lower: v_name = "Thin"
            elif "extralight" in sub_lower or "extra light" in sub_lower: v_name = "ExtraLight"
            elif "light" in sub_lower: v_name = "Light"
            elif "semibold" in sub_lower or "semi bold" in sub_lower: v_name = "SemiBold"
            elif "extrabold" in sub_lower or "extra bold" in sub_lower: v_name = "ExtraBold"
            elif "black" in sub_lower or "heavy" in sub_lower: v_name = "Black"
            elif "bold" in sub_lower: v_name = "Bold"
            elif "medium" in sub_lower: v_name = "Medium"
            elif "italic" in sub_lower or "oblique" in sub_lower: v_name = "Italic"

            fam_key = fam_name.lower()
            if fam_key not in custom_families:
                custom_families[fam_key] = {
                    "family": fam_name,
                    "category": "custom",
                    "source": "custom",
                    "variants": [],
                    "files": {},
                }

            v_info = dict(STANDARD_VARIANTS.get(v_name, {"weight": 400, "style": "normal"}))
            v_info["name"] = v_name
            v_info["filename"] = f.name

            # Evita duplicati nella lista varianti
            if not any(v["name"] == v_name for v in custom_families[fam_key]["variants"]):
                custom_families[fam_key]["variants"].append(v_info)
            custom_families[fam_key]["files"][v_name.lower()] = str(f)

        except Exception as e:
            logger.warning(f"Impossibile leggere font custom {f.name}: {e}")

    return list(custom_families.values())


def get_all_fonts_catalog() -> dict[str, list[dict[str, Any]]]:
    """
    Ritorna la suddivisione completa per l'interfaccia:
    - system_preinstalled: font di sistema e preinstallati (Google Fonts + macOS + Raleway/Alata)
    - custom: font personalizzati rilevati
    """
    custom_list = scan_custom_fonts()
    return {
        "system_preinstalled": FONT_CATALOG,
        "custom": custom_list,
    }


# ── 3. RISOLUZIONE E DOWNLOAD DEI FONT PER PILLOW ─────────────────────────────

def _get_google_font_url(family: str, weight: int = 400, italic: bool = False) -> Optional[str]:
    """Interroga l'API CSS2 di Google Fonts per ottenere il link diretto al file .ttf."""
    fam_param = family.replace(" ", "+")
    spec = f"ital,wght@1,{weight}" if italic else f"wght@{weight}"
    url = f"https://fonts.googleapis.com/css2?family={fam_param}:{spec}&display=swap"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            css = response.read().decode("utf-8")
        matches = re.findall(r"url\((https://[^)]+)\)", css)
        return matches[-1] if matches else None
    except Exception as e:
        logger.warning(f"Errore recupero CSS Google Font {family} ({weight}): {e}")
        return None


def ensure_google_font_cached(family: str, variant_name: str) -> Optional[Path]:
    """Scarica e memorizza nella cache locale (fonts/google/) la variante richiesta."""
    entry = CATALOG_BY_FAMILY.get(family.lower())
    if not entry or entry["source"] != "google":
        return None

    # Trova info variante
    v_info = None
    for v in entry["variants"]:
        if v["name"].lower() == variant_name.lower():
            v_info = v
            break
    if not v_info:
        v_info = entry["variants"][0] if entry["variants"] else {"weight": 400, "style": "normal"}

    weight = v_info.get("weight", 400)
    is_italic = v_info.get("style") == "italic"

    safe_fam = family.replace(" ", "_")
    italic_suffix = "_italic" if is_italic else ""
    filename = f"{safe_fam}_{weight}{italic_suffix}.ttf"
    dest_path = GOOGLE_FONTS_CACHE_DIR / filename

    if dest_path.exists() and dest_path.stat().st_size > 1000:
        return dest_path

    with _DOWNLOAD_LOCK:
        if dest_path.exists() and dest_path.stat().st_size > 1000:
            return dest_path

        ttf_url = _get_google_font_url(family, weight=weight, italic=is_italic)
        if not ttf_url:
            return None

        try:
            req = urllib.request.Request(ttf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
            dest_path.write_bytes(data)
            logger.info(f"Scaricato Google Font in cache: {dest_path.name}")
            return dest_path
        except Exception as e:
            logger.warning(f"Errore download file TTF per {family}: {e}")
            return None


def _resolve_system_font(family: str, variant_name: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
    """Risolve font nativi di macOS (Arial, Helvetica, Helvetica Neue)."""
    fam_lower = family.lower().strip()
    var_lower = variant_name.lower().strip()

    if fam_lower == "arial":
        stem_map = {
            "bold": "Arial Bold.ttf",
            "italic": "Arial Italic.ttf",
            "bold italic": "Arial Bold Italic.ttf",
            "black": "Arial Black.ttf",
            "regular": "Arial.ttf",
        }
        filename = stem_map.get(var_lower, "Arial.ttf")
        candidates = [
            Path("/System/Library/Fonts/Supplemental") / filename,
            Path("/Library/Fonts") / filename,
            Path("/System/Library/Fonts") / "ArialHB.ttc",
        ]
        for c in candidates:
            if c.exists():
                return ImageFont.truetype(str(c), size)

    elif fam_lower == "helvetica":
        ttc_path = Path("/System/Library/Fonts/Helvetica.ttc")
        if ttc_path.exists():
            # Mappa indici TTC Helvetica
            idx_map = {
                "regular": 0,
                "bold": 1,
                "italic": 2,
                "bold italic": 3,
                "light": 4,
            }
            idx = idx_map.get(var_lower, 0)
            try:
                return ImageFont.truetype(str(ttc_path), size, index=idx)
            except Exception:
                return ImageFont.truetype(str(ttc_path), size, index=0)

    elif fam_lower in ("helvetica neue", "helveticaneue"):
        ttc_path = Path("/System/Library/Fonts/HelveticaNeue.ttc")
        if ttc_path.exists():
            idx_map = {
                "regular": 0,
                "bold": 1,
                "italic": 2,
                "bold italic": 3,
                "light": 7,
                "medium": 10,
                "thin": 12,
                "black": 9,
            }
            idx = idx_map.get(var_lower, 0)
            try:
                return ImageFont.truetype(str(ttc_path), size, index=idx)
            except Exception:
                return ImageFont.truetype(str(ttc_path), size, index=0)

    return None


def _resolve_local_font(family: str, variant_name: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
    """Risolve i font locali inclusi nel progetto (Raleway e Alata)."""
    fam_lower = family.lower().strip()
    var_lower = variant_name.lower().strip()

    if fam_lower == "alata":
        p = PROJECT_FONTS_DIR / "Alata-Regular.ttf"
        if p.exists():
            return ImageFont.truetype(str(p), size)

    if fam_lower == "raleway":
        if "light" in var_lower or "thin" in var_lower or "extralight" in var_lower:
            target = PROJECT_FONTS_DIR / "Raleway-Light.ttf"
        elif "semibold" in var_lower:
            target = PROJECT_FONTS_DIR / "Raleway-SemiBold.ttf"
        elif "bold" in var_lower or "black" in var_lower or "medium" in var_lower:
            target = PROJECT_FONTS_DIR / "Raleway-Bold.ttf"
        else:
            target = PROJECT_FONTS_DIR / "Raleway-Light.ttf"

        if target.exists():
            return ImageFont.truetype(str(target), size)

    return None


def _resolve_custom_font(family: str, variant_name: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
    """Risolve font custom caricati dall'utente in ./fonts/."""
    customs = scan_custom_fonts()
    for c in customs:
        if c["family"].lower() == family.lower():
            # Cerca variante esatta
            var_file = c["files"].get(variant_name.lower())
            if var_file and Path(var_file).exists():
                return ImageFont.truetype(var_file, size)
            # Fallback: prima variante disponibile
            if c["files"]:
                first_file = next(iter(c["files"].values()))
                if Path(first_file).exists():
                    return ImageFont.truetype(first_file, size)
    return None


def resolve_font(
    font_name: str = "Raleway",
    variant: str = "Regular",
    size: int = 45,
) -> ImageFont.FreeTypeFont:
    """
    Risolve e carica il font Pillow richiesto con fallback a cascata:
    1. Font personalizzati utente
    2. Font locali (Raleway, Alata)
    3. Font di sistema macOS (Arial, Helvetica, Helvetica Neue)
    4. Google Fonts (cache locale o download on-demand)
    5. Fallback generico di sistema (Arial/Helvetica/Pillow default)
    """
    safe_size = max(int(size or 1), 1)
    family = str(font_name or "Raleway").strip()
    var_name = str(variant or "Regular").strip()

    # 1. Custom font
    cf = _resolve_custom_font(family, var_name, safe_size)
    if cf:
        return cf

    # 2. Local font
    lf = _resolve_local_font(family, var_name, safe_size)
    if lf:
        return lf

    # 3. System font
    sf = _resolve_system_font(family, var_name, safe_size)
    if sf:
        return sf

    # 4. Google Font (da cache o download)
    gf_path = ensure_google_font_cached(family, var_name)
    if gf_path and gf_path.exists():
        try:
            return ImageFont.truetype(str(gf_path), safe_size)
        except Exception as e:
            logger.warning(f"Errore caricamento font da {gf_path}: {e}")

    # Fallback su Raleway locale se disponibile
    raleway_fallback = PROJECT_FONTS_DIR / "Raleway-Light.ttf"
    if raleway_fallback.exists():
        try:
            return ImageFont.truetype(str(raleway_fallback), safe_size)
        except Exception:
            pass

    # Fallback su Arial di sistema
    arial_fallback = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if arial_fallback.exists():
        try:
            return ImageFont.truetype(str(arial_fallback), safe_size)
        except Exception:
            pass

    return ImageFont.load_default(size=max(safe_size, 10))


def resolve_font_pair(
    font_name: str = "Raleway",
    size: int = 45,
) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    Ritorna una coppia (Regular/Light, Bold/SemiBold) del font specificato.
    Utilizzata per il watermark e la compatibilità legacy.
    """
    safe_size = max(int(size or 1), 1)
    family = str(font_name or "Raleway").strip()

    # Se la famiglia ha varianti nel catalogo, seleziona le migliori per light e bold
    entry = CATALOG_BY_FAMILY.get(family.lower())
    if entry:
        v_names = [v["name"] for v in entry["variants"]]
        # Light o Regular
        reg_var = "Regular"
        if "Light" in v_names and "Regular" not in v_names:
            reg_var = "Light"
        elif "Regular" not in v_names and v_names:
            reg_var = v_names[0]

        # Bold o SemiBold
        bold_var = "Bold"
        if "Bold" not in v_names:
            if "SemiBold" in v_names:
                bold_var = "SemiBold"
            elif "Medium" in v_names:
                bold_var = "Medium"
            elif v_names:
                bold_var = v_names[-1]

        f_reg = resolve_font(family, reg_var, safe_size)
        f_bold = resolve_font(family, bold_var, safe_size)
        return f_reg, f_bold

    # Altrimenti fallback
    f_reg = resolve_font(family, "Regular", safe_size)
    f_bold = resolve_font(family, "Bold", safe_size)
    return f_reg, f_bold
