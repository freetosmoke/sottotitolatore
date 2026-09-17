"""
subtitle_renderer.py
Renderizza sottotitoli e watermark come PNG trasparenti (1080x1920) con Pillow,
poi genera un ffconcat con il timing corretto.
Coordinate intuitive con CENTRO DELLO SCHERMO a (0, 0):
- X=0: Centro orizzontale (+dx verso destra, -sx verso sinistra)
- Y=0: Centro verticale (+giù verso il basso, -su verso l'alto)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple, Any

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

from keyword_selector import select_keyword
from transcriber import SubtitleChunk

console = Console(stderr=True)

# ── Dimensioni Canvas 1080x1920 ───────────────────────────────────────────────
WIDTH  = 1080
HEIGHT = 1920
CENTER_X = 540
CENTER_Y = 960

# Preset defaults con coordinate:
# Sottotitoli: Raleway Light, size 45pt, Offset (X: 0, Y: 0) -> Centro esatto (Y=960px)
# Watermark:   Raleway SemiBold, size 30pt, Offset (X: 0, Y: +100) -> 100px sotto il centro (Y=1060px)
DEFAULT_OFFSET_SUB_X = 0
DEFAULT_OFFSET_SUB_Y = 0
DEFAULT_OFFSET_WM_X  = 0
DEFAULT_OFFSET_WM_Y  = 100

SUBTITLE_Y = CENTER_Y + DEFAULT_OFFSET_SUB_Y  # 960 (Centro esatto)
WATERMARK_Y = CENTER_Y + DEFAULT_OFFSET_WM_Y  # 1060 (100px sotto il centro)
SUBTITLE_X = CENTER_X + DEFAULT_OFFSET_SUB_X  # 540
WATERMARK_X = CENTER_X + DEFAULT_OFFSET_WM_X  # 540

FONT_SIZE_SUB = 45  # CapCut dimensione 8
FONT_SIZE_WM  = 30  # CapCut dimensione 5
WATERMARK_TEXT = "@lavocedelsuccesso"

TEXT_COLOR = (255, 255, 255, 255)
STROKE_WIDTH = 0
STROKE_COLOR = (0, 0, 0, 0)
SHADOW_OFFSET = 0
SHADOW_COLOR = (0, 0, 0, 0)

# ── Struttura dati ────────────────────────────────────────────────────────────
class RenderedChunk(NamedTuple):
    image_path: Path
    start: float
    end: float

# ── Rilevamento font ──────────────────────────────────────────────────────────
_RALEWAY_LIGHT    = [
    "./fonts/Raleway-Light.ttf",
    str(Path(__file__).parent / "fonts" / "Raleway-Light.ttf"),
    "~/Library/Fonts/Raleway-Light.ttf",
    "/Library/Fonts/Raleway-Light.ttf"
]
_RALEWAY_SEMIBOLD = [
    "./fonts/Raleway-SemiBold.ttf",
    str(Path(__file__).parent / "fonts" / "Raleway-SemiBold.ttf"),
    "~/Library/Fonts/Raleway-SemiBold.ttf",
    "/Library/Fonts/Raleway-SemiBold.ttf"
]
_ALATA_REGULAR    = [
    "./fonts/Alata-Regular.ttf",
    str(Path(__file__).parent / "fonts" / "Alata-Regular.ttf"),
    "~/Library/Fonts/alata-regular.ttf",
    "~/Library/Fonts/Alata-Regular.ttf",
    "/Library/Fonts/Alata-Regular.ttf"
]
_FALLBACK_REG  = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf",      "/System/Library/Fonts/Supplemental/Arial.ttf"]
_FALLBACK_BOLD = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]

def _find(candidates: list[str]) -> str | None:
    for c in candidates:
        p = Path(os.path.expanduser(c))
        if p.exists():
            return str(p)
    return None

def _load(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size, index=index) if path.endswith(".ttc") else ImageFont.truetype(path, size)

def load_pair(size: int, font_name: str = "Raleway") -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    safe_size = max(int(size or 1), 1)
    fn = (font_name or "").strip().lower()
    if fn == "alata":
        ap = _find(_ALATA_REGULAR)
        if ap:
            af = _load(ap, safe_size)
            return af, af
    lp = _find(_RALEWAY_LIGHT)
    sp = _find(_RALEWAY_SEMIBOLD)
    if lp and sp:
        return _load(lp, safe_size), _load(sp, safe_size)
    rp = _find(_FALLBACK_REG)
    bp = _find(_FALLBACK_BOLD)
    if rp and bp:
        bold_idx = 1 if bp.endswith(".ttc") else 0
        return _load(rp, safe_size, 0), _load(bp, safe_size, bold_idx)
    d = ImageFont.load_default(size=max(safe_size, 10))
    return d, d

# ── Utility ───────────────────────────────────────────────────────────────────
def _w(text: str, font: ImageFont.FreeTypeFont) -> int:
    bb = font.getbbox(text)
    return bb[2] - bb[0]

def _h(font: ImageFont.FreeTypeFont) -> int:
    bb = font.getbbox("Agpj")
    return bb[3] - bb[1]

def _word_w(text: str, font: ImageFont.FreeTypeFont, letter_spacing: int = 0) -> int:
    if not letter_spacing or len(text) <= 1:
        return _w(text, font)
    return sum(_w(ch, font) + letter_spacing for ch in text) - letter_spacing

def _draw_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: tuple[int, int, int, int] = TEXT_COLOR,
    stroke_width: int = 0,
    stroke_color: tuple[int, int, int, int] = STROKE_COLOR,
    shadow_offset: int = 0,
    shadow_color: tuple[int, int, int, int] = SHADOW_COLOR,
    faux_bold: bool = False,
    letter_spacing: int = 0,
) -> None:
    if not letter_spacing or len(text) <= 1:
        if shadow_offset > 0 and shadow_color[3] > 0:
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
            if faux_bold:
                draw.text((x + shadow_offset + 1, y + shadow_offset), text, font=font, fill=shadow_color)
        if faux_bold:
            draw.text(
                (x + 1, y),
                text,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color if stroke_width > 0 else None
            )
        draw.text(
            (x, y),
            text,
            font=font,
            fill=fill_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color if stroke_width > 0 else None
        )
    else:
        cx = x
        for ch in text:
            if shadow_offset > 0 and shadow_color[3] > 0:
                draw.text((cx + shadow_offset, y + shadow_offset), ch, font=font, fill=shadow_color)
                if faux_bold:
                    draw.text((cx + shadow_offset + 1, y + shadow_offset), ch, font=font, fill=shadow_color)
            if faux_bold:
                draw.text(
                    (cx + 1, y),
                    ch,
                    font=font,
                    fill=fill_color,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_color if stroke_width > 0 else None
                )
            draw.text(
                (cx, y),
                ch,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color if stroke_width > 0 else None
            )
            cx += _w(ch, font) + letter_spacing + (1 if faux_bold else 0)

# ── Rendering PNG ─────────────────────────────────────────────────────────────
def render_subtitle(
    words: list[str],
    bold_indices: set[int] | list[int] | int,
    light,
    semibold,
    out: Path,
    offset_x: int = DEFAULT_OFFSET_SUB_X,
    offset_y: int = DEFAULT_OFFSET_SUB_Y,
    stroke_width: int = 0,
    shadow_offset: int = 0,
    subtitle_x: int | None = None,
    subtitle_y: int | None = None,
    pattern: str = "",
    all_caps: bool = False,
    letter_spacing: int = 0,
    capcut_sub_x: int | None = None,
    capcut_sub_y: int | None = None,
) -> Path:
    if capcut_sub_x is not None:
        offset_x = round(float(capcut_sub_x) * 0.51)
    elif subtitle_x is not None:
        offset_x = subtitle_x - CENTER_X

    if capcut_sub_y is not None:
        # Convenzione CapCut calibrata: 1 unit CapCut = 0.51 px (negativo = verso il basso)
        offset_y = -round(float(capcut_sub_y) * 0.51)
    elif subtitle_y is not None:
        offset_y = subtitle_y - CENTER_Y

    if all_caps:
        words = [w.upper() for w in words]

    if isinstance(bold_indices, int):
        b_set = {bold_indices} if bold_indices >= 0 else set()
    else:
        b_set = set(bold_indices)

    is_bold_pattern = bool(pattern and pattern.strip().lower() == "bold")
    is_light_pattern = bool(pattern and pattern.strip().lower() == "light")

    img  = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    space_w = _w(" ", light) + letter_spacing
    ref_font = semibold if is_bold_pattern else light
    asc, desc = ref_font.getmetrics()

    def _is_bold(idx):
        if is_light_pattern:
            return False
        return is_bold_pattern or (idx in b_set)

    total_w = sum(_word_w(w, semibold if _is_bold(i) else light, letter_spacing) for i, w in enumerate(words))
    total_w += space_w * max(0, len(words) - 1)

    # Coordinate assolute convertite dal centro (CENTER_X=540, CENTER_Y=960)
    abs_center_x = CENTER_X + offset_x
    abs_center_y = CENTER_Y + offset_y

    start_x = abs_center_x - (total_w // 2)
    start_y = abs_center_y - (asc // 2) - round(asc * 0.12)

    cur_x = start_x
    for i, word in enumerate(words):
        is_word_bold = _is_bold(i)
        font = semibold if is_word_bold else light
        use_faux = is_bold_pattern or (is_word_bold and light == semibold)
        _draw_text(
            draw, cur_x, start_y, word, font,
            fill_color=TEXT_COLOR,
            stroke_width=stroke_width,
            stroke_color=(0, 0, 0, 220) if stroke_width > 0 else (0,0,0,0),
            shadow_offset=shadow_offset,
            shadow_color=(0, 0, 0, 140) if shadow_offset > 0 else (0,0,0,0),
            faux_bold=use_faux,
            letter_spacing=letter_spacing
        )
        cur_x += _word_w(word, font, letter_spacing) + (1 if use_faux else 0)
        if i < len(words) - 1:
            cur_x += space_w

    img.save(out, "PNG")
    return out

def render_watermark(
    semibold,
    out: Path,
    watermark_text: str = WATERMARK_TEXT,
    offset_x: int = DEFAULT_OFFSET_WM_X,
    offset_y: int = DEFAULT_OFFSET_WM_Y,
    stroke_width: int = 0,
    shadow_offset: int = 0,
    watermark_x: int | None = None,
    watermark_y: int | None = None,
    capcut_wm_x: int | None = None,
    capcut_wm_y: int | None = None,
) -> Path:
    if capcut_wm_x is not None:
        offset_x = round(float(capcut_wm_x) * 0.51)
    elif watermark_x is not None:
        offset_x = watermark_x - CENTER_X

    if capcut_wm_y is not None:
        # Convenzione CapCut calibrata: 1 unit CapCut = 0.51 px (negativo = verso il basso)
        offset_y = -round(float(capcut_wm_y) * 0.51)
    elif watermark_y is not None:
        offset_y = watermark_y - CENTER_Y

    img  = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    if not watermark_text or not watermark_text.strip():
        img.save(out, "PNG")
        return out

    draw = ImageDraw.Draw(img)
    wm_w = _w(watermark_text, semibold)
    asc, desc = semibold.getmetrics()

    abs_center_x = CENTER_X + offset_x
    abs_center_y = CENTER_Y + offset_y

    x = abs_center_x - (wm_w // 2)
    y = abs_center_y - (asc // 2) - round(asc * 0.20)

    _draw_text(
        draw, x, y, watermark_text, semibold,
        fill_color=TEXT_COLOR,
        stroke_width=stroke_width,
        stroke_color=(0, 0, 0, 220) if stroke_width > 0 else (0,0,0,0),
        shadow_offset=shadow_offset,
        shadow_color=(0, 0, 0, 140) if shadow_offset > 0 else (0,0,0,0)
    )
    img.save(out, "PNG")
    return out

def render_blank(work_dir: Path) -> Path:
    blank = work_dir / "blank.png"
    Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0)).save(blank, "PNG")
    return blank

# ── ffconcat ──────────────────────────────────────────────────────────────────
def create_ffconcat(
    rendered: list[RenderedChunk],
    blank_path: Path,
    total_duration: float,
    work_dir: Path,
) -> Path:
    ffconcat_path = work_dir / "subs.ffconcat"
    lines = ["ffconcat version 1.0"]
    current_t = 0.0

    for rc in rendered:
        # Assicura che start_t non preceda current_t, eliminando overlap o gap negativi
        start_t = max(current_t, float(rc.start))
        end_t = max(start_t + 0.05, float(rc.end))

        gap = start_t - current_t
        if gap > 0.005:
            lines.append(f"file '{blank_path.resolve()}'")
            lines.append(f"duration {gap:.4f}")

        dur = end_t - start_t
        if dur > 0.005:
            lines.append(f"file '{rc.image_path.resolve()}'")
            lines.append(f"duration {dur:.4f}")

        current_t = end_t

    trailing = total_duration - current_t
    if trailing > 0.005:
        lines.append(f"file '{blank_path.resolve()}'")
        lines.append(f"duration {trailing:.4f}")

    lines.append(f"file '{blank_path.resolve()}'")
    ffconcat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ffconcat_path

# ── Funzione pubblica ─────────────────────────────────────────────────────────
def render_all(
    chunks: list[SubtitleChunk] | list[dict[str, Any]],
    work_dir: Path,
    total_duration: float,
    preset: dict[str, Any] | None = None,
) -> tuple[list[RenderedChunk], Path, Path]:
    settings = {
        "offset_sub_x": DEFAULT_OFFSET_SUB_X,
        "offset_sub_y": DEFAULT_OFFSET_SUB_Y,
        "offset_wm_x": DEFAULT_OFFSET_WM_X,
        "offset_wm_y": DEFAULT_OFFSET_WM_Y,
        "font_size_sub": FONT_SIZE_SUB,
        "font_size_wm": FONT_SIZE_WM,
        "watermark_text": WATERMARK_TEXT,
        "stroke_width": 0,
        "shadow_offset": 0
    }
    if preset:
        # Supporta coordinate e dimensioni native CapCut
        if "capcut_sub_x" in preset and preset["capcut_sub_x"] is not None:
            settings["offset_sub_x"] = round(float(preset["capcut_sub_x"]) * 0.51)
        elif "capcut_x" in preset and preset["capcut_x"] is not None:
            settings["offset_sub_x"] = round(float(preset["capcut_x"]) * 0.51)
        elif "offset_sub_x" in preset:
            settings["offset_sub_x"] = int(preset["offset_sub_x"])
        elif "subtitle_x" in preset:
            settings["offset_sub_x"] = int(preset["subtitle_x"]) - CENTER_X

        if "capcut_sub_y" in preset and preset["capcut_sub_y"] is not None:
            # Scala CapCut calibrata: 1 unit CapCut = 0.51 px video
            settings["offset_sub_y"] = -round(float(preset["capcut_sub_y"]) * 0.51)
        elif "capcut_y" in preset and preset["capcut_y"] is not None:
            settings["offset_sub_y"] = -round(float(preset["capcut_y"]) * 0.51)
        elif "offset_sub_y" in preset:
            settings["offset_sub_y"] = int(preset["offset_sub_y"])
        elif "subtitle_y" in preset:
            settings["offset_sub_y"] = int(preset["subtitle_y"]) - CENTER_Y

        if "capcut_size" in preset and preset["capcut_size"]:
            sub_scale = float(preset.get("capcut_sub_scale", 100)) / 100.0
            settings["font_size_sub"] = round(float(preset["capcut_size"]) * sub_scale * 5.35)

        if "capcut_wm_x" in preset and preset["capcut_wm_x"] is not None:
            settings["offset_wm_x"] = round(float(preset["capcut_wm_x"]) * 0.51)
        elif "offset_wm_x" in preset:
            settings["offset_wm_x"] = int(preset["offset_wm_x"])
        elif "watermark_x" in preset:
            settings["offset_wm_x"] = int(preset["watermark_x"]) - CENTER_X

        if "capcut_wm_y" in preset and preset["capcut_wm_y"] is not None:
            settings["offset_wm_y"] = -round(float(preset["capcut_wm_y"]) * 0.51)
        elif "offset_wm_y" in preset:
            settings["offset_wm_y"] = int(preset["offset_wm_y"])
        elif "watermark_y" in preset:
            settings["offset_wm_y"] = int(preset["watermark_y"]) - CENTER_Y

        if "capcut_wm_size" in preset and preset["capcut_wm_size"]:
            wm_scale = float(preset.get("capcut_wm_scale", 100)) / 100.0
            settings["font_size_wm"] = round(float(preset["capcut_wm_size"]) * wm_scale * 5.35)

        for k in ["font_size_sub", "font_size_wm", "watermark_text", "stroke_width", "shadow_offset", "font_name", "font_family", "pattern", "all_caps", "letter_spacing"]:
            if k in preset:
                settings[k] = preset[k]

    sub_ox = int(settings["offset_sub_x"])
    sub_oy = int(settings["offset_sub_y"])
    wm_ox  = int(settings["offset_wm_x"])
    wm_oy  = int(settings["offset_wm_y"])
    fs_sub = int(settings["font_size_sub"])
    fs_wm  = int(settings["font_size_wm"])
    stroke_w = int(settings.get("stroke_width", 0))
    shadow_off = int(settings.get("shadow_offset", 0))
    font_name = settings.get("font_name") or settings.get("font_family") or "Raleway"
    pattern = settings.get("pattern", "")
    all_caps = bool(settings.get("all_caps", False))
    letter_spacing = int(settings.get("letter_spacing", 0))

    light_sub, semibold_sub = load_pair(fs_sub, font_name=font_name)
    _,         semibold_wm  = load_pair(fs_wm, font_name=font_name)

    wm_path = work_dir / "watermark.png"
    render_watermark(
        semibold_wm,
        wm_path,
        settings["watermark_text"],
        offset_x=wm_ox,
        offset_y=wm_oy,
        stroke_width=stroke_w,
        shadow_offset=shadow_off
    )

    blank = render_blank(work_dir)

    rendered: list[RenderedChunk] = []
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            raw_words = chunk.get("words", [])
            words = [w if isinstance(w, str) else w.get("word", "") for w in raw_words]
            if "bold_indices" in chunk and isinstance(chunk["bold_indices"], list):
                b_indices = set(chunk["bold_indices"])
            else:
                kw_idx = chunk.get("keyword_index", -1)
                if kw_idx is None or kw_idx < 0 or kw_idx >= len(words):
                    kw = select_keyword(words)
                    b_indices = {kw} if kw is not None else set()
                else:
                    b_indices = {kw_idx}

            c_start = float(chunk.get("start", 0.0))
            c_end = float(chunk.get("end", 0.0))
        else:
            words = [w.word for w in chunk.words]
            kw = select_keyword(words)
            b_indices = {kw} if kw is not None else set()
            c_start = float(chunk.start)
            c_end = float(chunk.end)

        if i > 0 and len(rendered) > 0:
            last_end = rendered[-1].end
            if c_start < last_end:
                c_start = last_end
        if c_end <= c_start:
            c_end = c_start + 0.15

        out = work_dir / f"sub_{i:04d}.png"
        render_subtitle(
            words,
            b_indices,
            light_sub,
            semibold_sub,
            out,
            offset_x=sub_ox,
            offset_y=sub_oy,
            stroke_width=stroke_w,
            shadow_offset=shadow_off,
            pattern=pattern,
            all_caps=all_caps,
            letter_spacing=letter_spacing
        )
        rendered.append(RenderedChunk(image_path=out, start=c_start, end=c_end))

    console.log(f"[green]✓ {len(rendered)} frame sottotitolo renderizzati (sub_offset=({sub_ox},{sub_oy}), wm_offset=({wm_ox},{wm_oy}))[/]")
    ffconcat_path = create_ffconcat(rendered, blank, total_duration, work_dir)
    return rendered, ffconcat_path, wm_path
