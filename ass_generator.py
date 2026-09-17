"""
ass_generator.py
Modulo per la generazione del file .ass (Advanced SubStation Alpha)
con stili tipografici, watermark e sottotitoli con keyword in grassetto.
"""
from __future__ import annotations

import os
from pathlib import Path

from keyword_selector import apply_bold_tag
from transcriber import SubtitleChunk

# ---------------------------------------------------------------------------
# Costanti tipografiche
# ---------------------------------------------------------------------------

FONT_NAME = "Raleway"
FONT_FALLBACK = "Arial"          # usato se Raleway non è installato

SUBTITLE_FONT_SIZE = 62
WATERMARK_FONT_SIZE = 36
WATERMARK_TEXT = "@lavocedelsuccesso"

# Colori ASS: &HAABBGGRR  (AA=00 → opaco)
COLOR_WHITE = "&H00FFFFFF"
COLOR_OUTLINE = "&H00000000"     # bordo nero
COLOR_SHADOW = "&H80000000"      # ombra semi-trasparente

# Dimensioni riferimento
REF_WIDTH = 1080
REF_HEIGHT = 1920

# Posizione Y del sottotitolo e watermark
SUBTITLE_Y = REF_HEIGHT // 2         # 960 px (Centro esatto)
WATERMARK_Y = SUBTITLE_Y + 100       # 1060 px (100px sotto il centro)


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------

def _detect_font() -> str:
    """
    Rileva se Raleway è disponibile (controlla ./fonts e cartelle di sistema macOS).
    """
    local_fonts = Path("./fonts")
    if local_fonts.exists():
        for f in local_fonts.iterdir():
            if "raleway" in f.name.lower():
                return FONT_NAME

    # Cartelle di sistema macOS
    system_dirs = [
        Path.home() / "Library/Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
    ]
    for d in system_dirs:
        if d.exists():
            for f in d.iterdir():
                if "raleway" in f.name.lower():
                    return FONT_NAME

    return FONT_FALLBACK


def _ts(seconds: float) -> str:
    """Converte i secondi nel formato timestamp ASS: H:MM:SS.cs"""
    centiseconds = round(seconds * 100)
    cs = centiseconds % 100
    total_seconds = centiseconds // 100
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ---------------------------------------------------------------------------
# Costruzione del file .ass
# ---------------------------------------------------------------------------

ASS_HEADER_TEMPLATE = """\
[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 0
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{subtitle_style}
{watermark_style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def _build_subtitle_style(font: str) -> str:
    """Stile base per i sottotitoli: Raleway Light peso 300."""
    return (
        f"Style: SubtitleStyle,"
        f"{font},"
        f"{SUBTITLE_FONT_SIZE},"
        f"{COLOR_WHITE},"     # Primary
        f"{COLOR_WHITE},"     # Secondary
        f"{COLOR_OUTLINE},"   # Outline
        f"{COLOR_SHADOW},"    # Back (shadow)
        f"0,"                 # Bold (gestito inline con \b)
        f"0,"                 # Italic
        f"0,"                 # Underline
        f"0,"                 # StrikeOut
        f"100,100,"           # ScaleX, ScaleY
        f"0,"                 # Spacing
        f"0,"                 # Angle
        f"1,"                 # BorderStyle (1=outline+shadow)
        f"2,"                 # Outline width px
        f"1,"                 # Shadow depth px
        f"5,"                 # Alignment: 5 = centro
        f"0,0,0,"             # MarginL, MarginR, MarginV
        f"1"                  # Encoding
    )


def _build_watermark_style(font: str) -> str:
    """Stile per il watermark: Raleway SemiBold peso 600."""
    return (
        f"Style: WatermarkStyle,"
        f"{font},"
        f"{WATERMARK_FONT_SIZE},"
        f"{COLOR_WHITE},"
        f"{COLOR_WHITE},"
        f"{COLOR_OUTLINE},"
        f"{COLOR_SHADOW},"
        f"0,"                 # Bold gestito inline
        f"0,0,0,"
        f"100,100,"
        f"0,0,"
        f"1,"
        f"2,"
        f"1,"
        f"5,"                 # Alignment: 5 = centro
        f"0,0,0,"
        f"1"
    )


def _dialogue(
    start: float,
    end: float,
    style: str,
    text: str,
    layer: int = 0,
) -> str:
    """Genera una riga Dialogue ASS."""
    return (
        f"Dialogue: {layer},"
        f"{_ts(start)},"
        f"{_ts(end)},"
        f"{style},"
        f","           # Name (vuoto)
        f"0000,"       # MarginL
        f"0000,"       # MarginR
        f"0000,"       # MarginV
        f","           # Effect
        f"{text}"
    )


def generate_ass(
    chunks: list[SubtitleChunk],
    output_path: Path,
    total_duration: float,
) -> Path:
    """
    Genera il file .ass completo.

    Args:
        chunks:         Lista di SubtitleChunk da renderizzare.
        output_path:    Percorso di destinazione del file .ass.
        total_duration: Durata totale del video in secondi (per il watermark).

    Returns:
        Path del file .ass generato.
    """
    font = _detect_font()
    from rich.console import Console
    console = Console(stderr=True)
    if font == FONT_FALLBACK:
        console.log(
            f"[yellow]⚠ Raleway non trovato, utilizzo font fallback: {FONT_FALLBACK}[/]\n"
            f"  Installa Raleway o inserisci i file .ttf in ./fonts/"
        )
    else:
        console.log(f"[green]✓ Font rilevato:[/] {font}")

    sub_style = _build_subtitle_style(font)
    wm_style = _build_watermark_style(font)

    header = ASS_HEADER_TEMPLATE.format(
        width=REF_WIDTH,
        height=REF_HEIGHT,
        subtitle_style=sub_style,
        watermark_style=wm_style,
    )

    lines: list[str] = [header]

    # ------------------------------------------------------------------
    # 1. Watermark fisso per tutta la durata del video
    #    Usiamo \an5 (centro) con \pos per piazzarlo a WATERMARK_Y
    # ------------------------------------------------------------------
    wm_x = REF_WIDTH // 2
    wm_text = (
        r"{\an5\pos(" + f"{wm_x},{WATERMARK_Y}" + r")"
        r"\b600}" + WATERMARK_TEXT + r"{\b300}"
    )
    lines.append(_dialogue(0.0, total_duration, "WatermarkStyle", wm_text, layer=1))

    # ------------------------------------------------------------------
    # 2. Sottotitoli
    #    Ogni chunk è centrato orizzontalmente a SUBTITLE_Y
    # ------------------------------------------------------------------
    sub_x = REF_WIDTH // 2
    for chunk in chunks:
        words = [w.word for w in chunk.words]
        text_with_bold = apply_bold_tag(words)

        # Override di posizione + peso base Light (\b300)
        ass_text = (
            r"{\an5\pos(" + f"{sub_x},{SUBTITLE_Y}" + r")"
            r"\b300}" + text_with_bold
        )
        lines.append(
            _dialogue(chunk.start, chunk.end, "SubtitleStyle", ass_text)
        )

    content = "\n".join(lines) + "\n"
    output_path.write_text(content, encoding="utf-8-sig")

    console.log(f"[green]✓ File ASS generato:[/] {output_path}")
    return output_path
