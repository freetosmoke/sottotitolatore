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
import re
from pathlib import Path
from typing import NamedTuple, Any

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

# ── Dizionari per Capitalizzazione Intelligente ──────────────────────────────
ACRONYMS = {
    "AI", "API", "B2B", "B2C", "CEO", "CTO", "CFO", "COO", "CMO", "CRM", "CSS", "CTA",
    "DMG", "DNA", "FAQ", "FFMPEG", "GPU", "HTML", "HTTP", "HTTPS", "ID", "IP", "IT",
    "JSON", "NASA", "OK", "OS", "PC", "PDF", "RAM", "ROI", "ROM", "SEO", "SMS", "SRT",
    "TG", "TV", "UI", "URL", "USA", "UX", "VFX", "VIP", "VPN", "VR", "XML"
}

PROPER_NOUNS = {
    "Salvatore", "Puglisi", "Guglielmino", "Luca", "Marco", "Matteo", "Giovanni", "Andrea",
    "Alessandro", "Francesco", "Davide", "Federico", "Lorenzo", "Giulia", "Chiara", "Sara",
    "Elena", "Francesca", "Valentina", "Alex", "Hormozi", "Steve", "Jobs", "Elon", "Musk",
    "Google", "Apple", "Microsoft", "Amazon", "Meta", "Facebook", "Instagram", "WhatsApp",
    "Telegram", "TikTok", "YouTube", "LinkedIn", "Twitter", "X", "OpenAI", "ChatGPT",
    "CapCut", "SubStudio", "Premiere", "Photoshop", "FinalCut", "Netflix", "Spotify",
    "iOS", "iPadOS", "macOS", "Mac", "Android", "Windows", "Linux",
    "Italia", "Roma", "Milano", "Napoli", "Torino", "Firenze", "Bologna", "Palermo",
    "Genova", "Venezia", "Verona", "Bari", "Catania", "Messina", "Padova", "Trieste",
    "Europa", "America", "Francia", "Spagna", "Germania", "Inghilterra", "Londra",
    "Parigi", "Berlino", "Madrid", "New", "York", "California"
}

LOWERCASE_WORDS_IT = {
    "a", "ad", "agli", "ai", "al", "all", "alla", "alle", "allo", "con", "col", "coi",
    "da", "dal", "dalla", "dalle", "dallo", "dai", "dagli", "dei", "del", "dell",
    "della", "delle", "dello", "degli", "di", "ed", "e", "fra", "in", "il", "la", "le",
    "lo", "gli", "i", "ma", "ne", "nel", "nella", "nelle", "nello", "nei", "negli",
    "o", "od", "per", "pel", "pei", "se", "su", "sul", "sulla", "sulle", "sullo",
    "sui", "sugli", "tra", "un", "uno", "una", "che", "chi", "cui", "non"
}

def apply_capitalization(text: str, mode: str = "smartcase") -> str:
    """
    Applica la trasformazione di capitalizzazione al testo:
    - uppercase: tutto MAIUSCOLO
    - lowercase: tutto minuscolo
    - titlecase: Prima Lettera Maiuscola di ogni parola
    - smartcase: capitalizzazione intelligente con preservazione acronimi,
      nomi propri, brand, città e inizio frase.
    """
    if not text or not isinstance(text, str):
        return text or ""

    mode = (mode or "smartcase").lower().strip()
    if mode in ("uppercase", "caps", "all_caps"):
        return text.upper()
    if mode == "lowercase":
        return text.lower()
    if mode == "titlecase":
        def _cap_word(m):
            w = m.group(0)
            return w.capitalize()
        return re.sub(r"[A-Za-zÀ-ÿ0-9]+", _cap_word, text)
    if mode in ("smartcase", "smart"):
        acro_map = {a.upper(): a for a in ACRONYMS}
        proper_map = {p.lower(): p for p in PROPER_NOUNS}

        tokens = re.split(r"(\s+|[.,!?;:\"()\[\]{}]+)", text)
        is_sentence_start = True
        result = []

        for tok in tokens:
            if not tok:
                continue
            if re.match(r"^(\s+|[.,!?;:\"()\[\]{}]+)$", tok):
                if any(p in tok for p in ".!?"):
                    is_sentence_start = True
                result.append(tok)
                continue

            if "'" in tok or "’" in tok:
                sub_parts = re.split(r"(['’])", tok)
                proc_sub = []
                for sp in sub_parts:
                    if sp in ("'", "’"):
                        proc_sub.append(sp)
                    elif sp.lower() in proper_map:
                        proc_sub.append(proper_map[sp.lower()])
                    elif sp.upper() in acro_map:
                        proc_sub.append(acro_map[sp.upper()])
                    elif is_sentence_start:
                        proc_sub.append(sp.capitalize())
                        is_sentence_start = False
                    elif sp.lower() in LOWERCASE_WORDS_IT:
                        proc_sub.append(sp.lower())
                    else:
                        proc_sub.append(sp)
                result.append("".join(proc_sub))
                is_sentence_start = False
                continue

            tok_upper = tok.upper()
            tok_lower = tok.lower()

            if tok_upper in acro_map:
                result.append(acro_map[tok_upper])
                is_sentence_start = False
            elif tok_lower in proper_map:
                result.append(proper_map[tok_lower])
                is_sentence_start = False
            elif is_sentence_start:
                result.append(tok.capitalize())
                is_sentence_start = False
            elif tok_lower in LOWERCASE_WORDS_IT:
                result.append(tok_lower)
            else:
                if any(c.isupper() for c in tok[1:]):
                    result.append(tok)
                else:
                    result.append(tok.lower())

        return "".join(result)

    return text

from keyword_selector import select_keyword
from transcriber import SubtitleChunk

console = Console(stderr=True)

# ── Dimensioni Canvas Base e Calibrazione CapCut ─────────────────────────────
BASE_WIDTH  = 1080
BASE_HEIGHT = 1920
BASE_CENTER_X = 540
BASE_CENTER_Y = 960

# Costanti di calibrazione CapCut (NON MODIFICARE I VALORI)
CAPCUT_SIZE_FACTOR = 5.35
CAPCUT_COORD_SCALE = 0.50

# Alias retrocompatibili
WIDTH  = BASE_WIDTH
HEIGHT = BASE_HEIGHT
CENTER_X = BASE_CENTER_X
CENTER_Y = BASE_CENTER_Y

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
_RALEWAY_LIGHT = [
    "./fonts/Raleway-Light.ttf",
    str(Path(__file__).parent / "fonts" / "Raleway-Light.ttf"),
    "~/Library/Fonts/Raleway-Light.ttf",
    "/Library/Fonts/Raleway-Light.ttf"
]
_RALEWAY_BOLD = [
    "./fonts/Raleway-Bold.ttf",
    str(Path(__file__).parent / "fonts" / "Raleway-Bold.ttf"),
    "~/Library/Fonts/Raleway-Bold.ttf",
    "/Library/Fonts/Raleway-Bold.ttf",
    "./fonts/Raleway-SemiBold.ttf",
    str(Path(__file__).parent / "fonts" / "Raleway-SemiBold.ttf"),
]
_ALATA_REGULAR = [
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


_FONT_VARIANT_ALIASES = {
    "thin": ["thin", "100"],
    "extralight": ["extra light", "extralight", "ultralight", "200"],
    "light": ["light", "300"],
    "regular": ["regular", "normal", "book", "400"],
    "medium": ["medium", "500"],
    "semibold": ["semibold", "semi bold", "demibold", "600"],
    "bold": ["bold", "700"],
    "extrabold": ["extra bold", "extrabold", "800"],
    "black": ["black", "heavy", "900"],
    "italic": ["italic", "oblique"],
}


def _normalize_font_variant(variant: str | None) -> str:
    value = str(variant or "regular").strip().lower()
    value = value.replace("-", "").replace("_", "").replace(" ", "")

    aliases = {
        "normal": "regular",
        "book": "regular",
        "demibold": "semibold",
        "semi": "semibold",
        "heavy": "black",
        "oblique": "italic",
    }

    return aliases.get(value, value)


def _font_variant_score(path: Path, variant: str) -> int:
    stem = path.stem.lower()
    compact = stem.replace("-", "").replace("_", "").replace(" ", "")

    variant = _normalize_font_variant(variant)
    aliases = _FONT_VARIANT_ALIASES.get(variant, [variant])

    # Corrispondenza esatta.
    for alias in aliases:
        token = alias.replace("-", "").replace("_", "").replace(" ", "")
        if token and token in compact:
            return 100

    # Se chiediamo Regular, un file senza indicazione di peso
    # è il fallback naturale.
    if variant == "regular":
        known_variants = (
            "thin", "extralight", "light", "medium",
            "semibold", "bold", "extrabold", "black",
            "italic", "oblique"
        )
        if not any(v in compact for v in known_variants):
            return 80

    return 0


def load_font_variant(
    size: int,
    font_name: str = "Raleway",
    variant: str = "Regular",
) -> ImageFont.FreeTypeFont:
    """
    Carica una specifica variante del font.
    Utilizza il gestore centralizzato font_manager.
    """
    try:
        from font_manager import resolve_font
        return resolve_font(font_name=font_name, variant=variant, size=size)
    except Exception as e:
        logger.warning(f"Errore caricamento font con font_manager ({font_name}, {variant}): {e}")

    # Fallback di emergenza
    safe_size = max(int(size or 1), 1)
    d = ImageFont.load_default(size=max(safe_size, 10))
    return d


def load_pair(size: int, font_name: str = "Raleway") -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    Carica coppia (Regular, Bold) del font per watermark e compatibilità legacy.
    Utilizza il gestore centralizzato font_manager.
    """
    try:
        from font_manager import resolve_font_pair
        return resolve_font_pair(font_name=font_name, size=size)
    except Exception as e:
        logger.warning(f"Errore caricamento font pair con font_manager ({font_name}): {e}")

    safe_size = max(int(size or 1), 1)
    d = ImageFont.load_default(size=max(safe_size, 10))
    return d, d

# ── Utility ───────────────────────────────────────────────────────────────────
def get_font_typo_metrics(font_name: str = "Raleway", font_size: int = 45) -> dict[str, int]:
    """Calcola le metriche tipografiche (asc, desc, typoH, baselineOffset) usando Pillow FreeType."""
    safe_size = max(int(font_size or 1), 1)
    font, _ = load_pair(safe_size, font_name=font_name)
    asc, desc = font.getmetrics()
    typo_h = asc + desc
    diff = asc - desc
    baseline_offset = (diff // 2) if (diff % 2 == 0) else round(diff / 2)
    return {
        "asc": asc,
        "desc": desc,
        "typoH": typo_h,
        "baselineOffset": baseline_offset,
    }

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

def is_apostrophe_bound(prev_txt: str, next_txt: str) -> bool:
    """Verifica se due token consecutivi sono legati da elisione/apostrofo."""
    import re
    p = str(prev_txt).strip()
    n = str(next_txt).strip()
    if not p or not n:
        return False
    if re.search(r"['’`´]$", p):
        return True
    if re.search(r"^['’`´]", n):
        return True
    clean_p = re.sub(r"^[^\w]+|[^\w]+$", "", p).lower()
    elision_particles = {
        "l", "d", "c", "s", "m", "t", "v", "un", "all", "dell",
        "nell", "sull", "dall", "quest", "quell", "tutt", "qualch",
        "mezz", "poc", "sant", "com"
    }
    if clean_p in elision_particles and (re.search(r"['’`´]", n) or re.search(r"^[aeiouàèéìòù]", n.lower())):
        if "'" in n or "’" in n or "'" in p or "’" in p:
            return True
    return False


def _layout_lines(
    words: list[str],
    is_bold_fn,
    light_font: ImageFont.FreeTypeFont,
    semibold_font: ImageFont.FreeTypeFont,
    letter_spacing: int,
    space_w: int,
    max_width: int,
    min_words_per_line: int = 2,
    max_words_per_line: int = 7,
    num_lines: int = 2,
    line_breaks: list[int] | None = None,
) -> list[list[tuple[int, str]]]:
    """Lay out subtitle words into lines without ever dropping tokens.

    Priority:
    1. Never lose words.
    2. Respect explicit line breaks or newlines.
    3. Respect max_width whenever possible.
    4. Respect max_words_per_line whenever possible.
    5. Keep the number of lines <= num_lines whenever possible.
    6. Try to satisfy min_words_per_line when possible.

    If the constraints are mathematically incompatible, all words are still
    rendered and the least important constraint is relaxed rather than
    dropping tokens.
    """
    min_words_per_line = max(1, int(min_words_per_line))
    max_words_per_line = max(min_words_per_line, int(max_words_per_line))
    num_lines = max(1, int(num_lines))

    # Expand explicit newlines while preserving the original word indices.
    tokens: list[tuple[int, str]] = []
    explicit_split_indices: set[int] = set()

    for i, word in enumerate(words):
        parts = str(word).split("\n")
        for p_idx, part in enumerate(parts):
            if p_idx > 0 and tokens:
                explicit_split_indices.add(len(tokens))
            if part:
                tokens.append((i, part))

    if line_breaks:
        for lb in line_breaks:
            try:
                lb_int = int(lb)
                if 0 < lb_int < len(tokens):
                    explicit_split_indices.add(lb_int)
            except (ValueError, TypeError):
                pass

    if not tokens:
        return [[]]

    # Se sono definiti spezzamenti manuali o newlines esplicite, rispettali rigorosamente
    if explicit_split_indices:
        sorted_splits = sorted(explicit_split_indices)
        manual_lines: list[list[tuple[int, str]]] = []
        cur_start = 0
        for s in sorted_splits:
            if s > cur_start and s < len(tokens):
                manual_lines.append(tokens[cur_start:s])
                cur_start = s
        if cur_start < len(tokens):
            manual_lines.append(tokens[cur_start:])
        if manual_lines:
            return manual_lines

    def token_width(token: tuple[int, str]) -> int:
        idx, text = token
        font = semibold_font if is_bold_fn(idx) else light_font
        return _word_w(text, font, letter_spacing)

    def line_width(line: list[tuple[int, str]]) -> int:
        if not line:
            return 0
        return (
            sum(token_width(token) for token in line)
            + space_w * max(0, len(line) - 1)
        )

    def fits(line: list[tuple[int, str]]) -> bool:
        return line_width(line) <= max_width

    # Numero di righe come priorità principale.
    # Tutte le parole devono essere mantenute.
    all_tokens = tokens
    n = len(all_tokens)

    # Se ci sono meno parole delle righe richieste, una parola per riga (massimo 2 righe).
    target_lines = min(min(2, max(1, num_lines)), n)

    if target_lines <= 1:
        return [all_tokens]

    # Se abbiamo 2 righe, ottimizziamo la divisione per un perfetto bilanciamento visivo
    # (evitando che una riga sia enorme e l'altra minuscola).
    if target_lines == 2:
        best_k = None
        best_score = float("inf")

        dangling_articles = {
            "il", "lo", "la", "l'", "i", "gli", "le", "un", "uno", "una", "un'",
            "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
            "del", "dello", "della", "dei", "degli", "delle",
            "al", "allo", "alla", "ai", "agli", "alle",
            "dal", "dallo", "dalla", "dai", "dagli", "dalle",
            "nel", "nello", "nella", "nei", "negli", "nelle",
            "sul", "sullo", "sulla", "sui", "sugli", "sulle",
            "col", "coi"
        }

        can_satisfy_min = (n >= 2 * min_words_per_line)
        can_satisfy_max = (n <= 2 * max_words_per_line)

        for k in range(1, n):
            c1 = k
            c2 = n - k
            w1 = line_width(all_tokens[:k])
            w2 = line_width(all_tokens[k:])

            score = 0.0

            # 1. Rispetto vincoli min/max parole
            if can_satisfy_min:
                if c1 < min_words_per_line:
                    score += (min_words_per_line - c1) * 3000.0
                if c2 < min_words_per_line:
                    score += (min_words_per_line - c2) * 3000.0

            if can_satisfy_max:
                if c1 > max_words_per_line:
                    score += (c1 - max_words_per_line) * 3000.0
                if c2 > max_words_per_line:
                    score += (c2 - max_words_per_line) * 3000.0

            # 2. Rispetto della larghezza massima del canvas
            if w1 > max_width:
                score += 15000.0 + (w1 - max_width) * 10.0
            if w2 > max_width:
                score += 15000.0 + (w2 - max_width) * 10.0

            # 3. Bilanciamento visivo simmetrico: minimizza la differenza di larghezza in pixel
            width_diff = abs(w1 - w2)
            score += width_diff

            # 4. Leggera preferenza per riga superiore bilanciata o lievemente piramidale (w1 >= w2)
            if w1 > w2:
                score += (w1 - w2) * 0.15

            # 5. Evita articoli o preposizioni isolate alla fine della riga 1
            last_word = all_tokens[k - 1][1].lower().strip(".,!?:;\"'()[]{}")
            if last_word in dangling_articles:
                score += 120.0

            # 6. PENALITÀ INVIOLABILE: Mai spezzare parole legate da apostrofo (es. "l'", "'energia", "d'", "un'")
            prev_token_text = all_tokens[k - 1][1]
            next_token_text = all_tokens[k][1]
            if is_apostrophe_bound(prev_token_text, next_token_text):
                score += 5_000_000.0

            if score < best_score:
                best_score = score
                best_k = k

        if best_k is not None and best_score < 1_000_000.0:
            return [all_tokens[:best_k], all_tokens[best_k:]]
        else:
            return [all_tokens]

    # Distribuzione fallback per > 2 righe:
    if n >= target_lines * min_words_per_line:
        counts = [min_words_per_line] * target_lines
        remaining = n - sum(counts)

        while remaining > 0:
            moved = False
            for i in range(target_lines):
                if remaining <= 0:
                    break
                if counts[i] < max_words_per_line:
                    counts[i] += 1
                    remaining -= 1
                    moved = True
            if not moved:
                for i in range(target_lines):
                    if remaining <= 0:
                        break
                    counts[i] += 1
                    remaining -= 1
    else:
        base = n // target_lines
        remainder = n % target_lines
        counts = [
            base + (1 if i < remainder else 0)
            for i in range(target_lines)
        ]

    candidates = []
    pos = 0

    for count in counts:
        candidates.append(all_tokens[pos:pos + count])
        pos += count

    if pos < n:
        candidates[-1].extend(all_tokens[pos:])

    # Manteniamo il numero di righe richiesto.
    # Proviamo solamente a migliorare la larghezza spostando
    # parole tra righe adiacenti.
    changed = True

    while changed:
        changed = False

        for i in range(len(candidates) - 1):
            left = candidates[i]
            right = candidates[i + 1]

            # Se la riga sinistra supera la larghezza, prova a spostare
            # l'ultima parola a destra.
            if len(left) > 1 and not fits(left):
                candidate_left = left[:-1]
                candidate_right = [left[-1]] + right

                if fits(candidate_left):
                    left.pop()
                    right.insert(0, candidate_left[-1])
                    changed = True
                    continue

            # Se la riga destra supera la larghezza, prova a spostare
            # la prima parola a sinistra.
            if len(right) > 1 and not fits(right):
                candidate_left = left + [right[0]]
                candidate_right = right[1:]

                if fits(candidate_left):
                    right_word = right.pop(0)
                    left.append(right_word)
                    changed = True

    # Invariante finale: tutte le parole devono essere presenti
    # esattamente una volta.
    flattened = [token for line in candidates for token in line]

    if flattened != all_tokens:
        raise RuntimeError(
            "Layout subtitle non lossless: una o più parole sono state perse."
        )

    return candidates


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
    light: ImageFont.FreeTypeFont,
    semibold: ImageFont.FreeTypeFont,
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
    rotation: float = 0.0,
    canvas_width: int = BASE_WIDTH,
    canvas_height: int = BASE_HEIGHT,
    max_width_ratio: float = 0.82,
    normal_color: tuple[int, int, int, int] = TEXT_COLOR,
    keyword_color: tuple[int, int, int, int] = TEXT_COLOR,
    min_words_per_line: int = 2,
    max_words_per_line: int = 7,
    num_lines: int = 2,
    active_word_index: int | None = None,
    highlighter_enabled: bool = False,
    highlighter_box_color: tuple[int, int, int, int] = (255, 230, 0, 255),
    highlighter_text_color: tuple[int, int, int, int] = (0, 0, 0, 255),
    highlighter_radius: int = 8,
    highlighter_padding_x: int = 10,
    highlighter_padding_y: int = 4,
    highlighter_stroke: int = 0,
    highlighter_shadow: int = 0,
    line_breaks: list[int] | None = None,
    word_animation: str = "none",
) -> Path:
    scale = canvas_height / BASE_HEIGHT
    center_x = canvas_width / 2.0
    center_y = canvas_height / 2.0

    if capcut_sub_x is not None:
        offset_x = round(float(capcut_sub_x) * CAPCUT_COORD_SCALE * scale)
    elif subtitle_x is not None:
        offset_x = round((subtitle_x - BASE_CENTER_X) * scale)

    if capcut_sub_y is not None:
        # Convenzione CapCut calibrata: 1 unit CapCut = 0.50 px (negativo = verso il basso)
        offset_y = -round(float(capcut_sub_y) * CAPCUT_COORD_SCALE * scale)
    elif subtitle_y is not None:
        offset_y = round((subtitle_y - BASE_CENTER_Y) * scale)

    if all_caps:
        words = [w.upper() for w in words]

    if isinstance(bold_indices, int):
        b_set = {bold_indices} if bold_indices >= 0 else set()
    else:
        b_set = set(bold_indices)

    is_bold_pattern = bool(pattern and pattern.strip().lower() == "bold")
    is_light_pattern = bool(pattern and pattern.strip().lower() == "light")

    img = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    space_w = _w(" ", light) + letter_spacing
    ref_font = semibold if is_bold_pattern else light
    asc, desc = ref_font.getmetrics()

    def _is_bold(idx):
        if is_light_pattern:
            return False
        return is_bold_pattern or (idx in b_set)

    # Coordinate assolute convertite dal centro del canvas
    abs_center_x = round(center_x + offset_x)
    abs_center_y = round(center_y + offset_y)

    max_allowed_w = int(canvas_width * max_width_ratio)
    lines = _layout_lines(
        words=words,
        is_bold_fn=_is_bold,
        light_font=light,
        semibold_font=semibold,
        letter_spacing=letter_spacing,
        space_w=space_w,
        max_width=max_allowed_w,
        min_words_per_line=min_words_per_line,
        max_words_per_line=max_words_per_line,
        num_lines=num_lines,
        line_breaks=line_breaks,
    )

    num_lines = len(lines)
    diff = asc - desc
    baseline_offset = (diff // 2) if (diff % 2 == 0) else round(diff / 2)
    single_line_baseline = abs_center_y + baseline_offset

    if num_lines <= 1:
        first_baseline = single_line_baseline
        line_h = asc + desc
    else:
        # Centra il blocco multi-riga verticalmente attorno ad abs_center_y
        line_gap = max(4, round(asc * 0.25))
        line_h = asc + desc + line_gap
        total_block_h = (num_lines - 1) * line_h + (asc + desc)
        top_y = abs_center_y - (total_block_h // 2)
        first_baseline = top_y + asc

    for line_idx, line_tokens in enumerate(lines):
        line_w = sum(
            _word_w(tok, semibold if _is_bold(tok_idx) else light, letter_spacing)
            for tok_idx, tok in line_tokens
        )
        line_w += space_w * max(0, len(line_tokens) - 1)

        start_x = abs_center_x - (line_w // 2)
        baseline = first_baseline + line_idx * line_h
        start_y = baseline - asc

        cur_x = start_x
        for word_pos, (tok_idx, tok) in enumerate(line_tokens):
            is_word_bold = _is_bold(tok_idx)
            font = semibold if is_word_bold else light
            use_faux = is_bold_pattern or (is_word_bold and light == semibold)
            is_active_word = (active_word_index is not None) and (tok_idx == active_word_index)
            word_w_px = _word_w(tok, font, letter_spacing) + (1 if use_faux else 0)

            word_y = start_y
            eff_fill = keyword_color if is_word_bold else normal_color
            eff_stroke = stroke_width
            eff_shadow = shadow_offset

            if active_word_index is not None:
                if word_animation == "fade":
                    # Karaoke/Creator style: parole non ancora pronunciate hanno opacità ridotta a 35%
                    if tok_idx > active_word_index:
                        eff_fill = (eff_fill[0], eff_fill[1], eff_fill[2], max(10, int(eff_fill[3] * 0.35)))
                        eff_stroke = 0
                        eff_shadow = 0
                elif word_animation == "slide_up" and is_active_word:
                    word_y = start_y - max(1, round(3 * scale))
                elif word_animation == "slide_down" and is_active_word:
                    word_y = start_y + max(1, round(3 * scale))
                elif word_animation in ("pop", "scale") and is_active_word:
                    use_faux = True

            if is_active_word and highlighter_enabled:
                # Disegna rettangolo arrotondato evidenziatore dietro alla parola attiva
                pad_x = max(0, round(highlighter_padding_x * scale))
                pad_y = max(0, round(highlighter_padding_y * scale))
                rad = max(0, round(highlighter_radius * scale))
                box_x0 = cur_x - pad_x
                box_y0 = word_y - pad_y
                box_x1 = cur_x + word_w_px + pad_x
                box_y1 = word_y + (asc + desc) + pad_y
                draw.rounded_rectangle(
                    [box_x0, box_y0, box_x1, box_y1],
                    radius=rad,
                    fill=highlighter_box_color
                )

                # Testo con colore per la parola attiva, con eventuale contorno e ombra dedicati
                eff_hl_stroke = highlighter_stroke if highlighter_stroke > 0 else stroke_width
                eff_hl_shadow = highlighter_shadow if highlighter_shadow > 0 else shadow_offset
                _draw_text(
                    draw, cur_x, word_y, tok, font,
                    fill_color=highlighter_text_color,
                    stroke_width=eff_hl_stroke,
                    stroke_color=(0, 0, 0, 220) if eff_hl_stroke > 0 else (0, 0, 0, 0),
                    shadow_offset=eff_hl_shadow,
                    shadow_color=(0, 0, 0, 160) if eff_hl_shadow > 0 else (0, 0, 0, 0),
                    faux_bold=use_faux,
                    letter_spacing=letter_spacing
                )
            else:
                _draw_text(
                    draw, cur_x, word_y, tok, font,
                    fill_color=eff_fill,
                    stroke_width=eff_stroke,
                    stroke_color=(0, 0, 0, 220) if eff_stroke > 0 else (0, 0, 0, 0),
                    shadow_offset=eff_shadow,
                    shadow_color=(0, 0, 0, min(220, int(60 + eff_shadow * 15))) if eff_shadow > 0 else (0, 0, 0, 0),
                    faux_bold=use_faux,
                    letter_spacing=letter_spacing
                )
            cur_x += word_w_px
            if word_pos < len(line_tokens) - 1:
                cur_x += space_w

    if rotation:
        img = img.rotate(-rotation, resample=Image.BICUBIC, center=(abs_center_x, abs_center_y))

    img.save(out, "PNG")
    return out

def render_watermark(
    semibold: ImageFont.FreeTypeFont,
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
    rotation: float = 0.0,
    canvas_width: int = BASE_WIDTH,
    canvas_height: int = BASE_HEIGHT,
) -> Path:
    scale = canvas_height / BASE_HEIGHT
    center_x = canvas_width / 2.0
    center_y = canvas_height / 2.0

    if capcut_wm_x is not None:
        offset_x = round(float(capcut_wm_x) * CAPCUT_COORD_SCALE * scale)
    elif watermark_x is not None:
        offset_x = round((watermark_x - BASE_CENTER_X) * scale)

    if capcut_wm_y is not None:
        # Convenzione CapCut calibrata: 1 unit CapCut = 0.50 px (negativo = verso il basso)
        offset_y = -round(float(capcut_wm_y) * CAPCUT_COORD_SCALE * scale)
    elif watermark_y is not None:
        offset_y = round((watermark_y - BASE_CENTER_Y) * scale)

    img = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    if not watermark_text or not watermark_text.strip():
        img.save(out, "PNG")
        return out

    draw = ImageDraw.Draw(img)
    wm_w = _w(watermark_text, semibold)
    asc, desc = semibold.getmetrics()

    abs_center_x = round(center_x + offset_x)
    abs_center_y = round(center_y + offset_y)

    x = abs_center_x - (wm_w // 2)
    diff = asc - desc
    baseline_offset = (diff // 2) if (diff % 2 == 0) else round(diff / 2)
    baseline = abs_center_y + baseline_offset
    y = baseline - asc

    _draw_text(
        draw, x, y, watermark_text, semibold,
        fill_color=TEXT_COLOR,
        stroke_width=stroke_width,
        stroke_color=(0, 0, 0, 220) if stroke_width > 0 else (0, 0, 0, 0),
        shadow_offset=shadow_offset,
        shadow_color=(0, 0, 0, 140) if shadow_offset > 0 else (0, 0, 0, 0)
    )
    if rotation:
        img = img.rotate(-rotation, resample=Image.BICUBIC, center=(abs_center_x, abs_center_y))
    img.save(out, "PNG")
    return out

def render_blank(work_dir: Path, canvas_width: int = BASE_WIDTH, canvas_height: int = BASE_HEIGHT) -> Path:
    blank = work_dir / "blank.png"
    Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0)).save(blank, "PNG")
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
    canvas_width: int = BASE_WIDTH,
    canvas_height: int = BASE_HEIGHT,
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
        "shadow_offset": 0,
        "subtitle_style": {
            "normal": {
                "font_family": "Raleway",
                "font_variant": "Light",
                "color": "#FFFFFF",
            },
            "keyword": {
                "font_family": "Raleway",
                "font_variant": "SemiBold",
                "color": "#FFFFFF",
            },
        },
        "keywords": {
            "enabled": True,
            "mode": "automatic",
        },
    }
    if preset:
        # Supporta coordinate e dimensioni native CapCut
        if "capcut_sub_x" in preset and preset["capcut_sub_x"] is not None:
            settings["offset_sub_x"] = round(float(preset["capcut_sub_x"]) * CAPCUT_COORD_SCALE)
        elif "capcut_x" in preset and preset["capcut_x"] is not None:
            settings["offset_sub_x"] = round(float(preset["capcut_x"]) * CAPCUT_COORD_SCALE)
        elif "offset_sub_x" in preset:
            settings["offset_sub_x"] = int(preset["offset_sub_x"])
        elif "subtitle_x" in preset:
            settings["offset_sub_x"] = int(preset["subtitle_x"]) - BASE_CENTER_X

        if "capcut_sub_y" in preset and preset["capcut_sub_y"] is not None:
            # Scala CapCut calibrata: 1 unit CapCut = 0.50 px video
            settings["offset_sub_y"] = -round(float(preset["capcut_sub_y"]) * CAPCUT_COORD_SCALE)
        elif "capcut_y" in preset and preset["capcut_y"] is not None:
            settings["offset_sub_y"] = -round(float(preset["capcut_y"]) * CAPCUT_COORD_SCALE)
        elif "offset_sub_y" in preset:
            settings["offset_sub_y"] = int(preset["offset_sub_y"])
        elif "subtitle_y" in preset:
            settings["offset_sub_y"] = int(preset["subtitle_y"]) - BASE_CENTER_Y

        if "capcut_size" in preset and preset["capcut_size"]:
            sub_scale = float(preset.get("capcut_sub_scale", 100)) / 100.0
            settings["font_size_sub"] = round(float(preset["capcut_size"]) * sub_scale * CAPCUT_SIZE_FACTOR)

        if "capcut_wm_x" in preset and preset["capcut_wm_x"] is not None:
            settings["offset_wm_x"] = round(float(preset["capcut_wm_x"]) * CAPCUT_COORD_SCALE)
        elif "offset_wm_x" in preset:
            settings["offset_wm_x"] = int(preset["offset_wm_x"])
        elif "watermark_x" in preset:
            settings["offset_wm_x"] = int(preset["watermark_x"]) - BASE_CENTER_X

        if "capcut_wm_y" in preset and preset["capcut_wm_y"] is not None:
            settings["offset_wm_y"] = -round(float(preset["capcut_wm_y"]) * CAPCUT_COORD_SCALE)
        elif "offset_wm_y" in preset:
            settings["offset_wm_y"] = int(preset["offset_wm_y"])
        elif "watermark_y" in preset:
            settings["offset_wm_y"] = int(preset["watermark_y"]) - BASE_CENTER_Y

        if "capcut_wm_size" in preset and preset["capcut_wm_size"]:
            wm_scale = float(preset.get("capcut_wm_scale", 100)) / 100.0
            settings["font_size_wm"] = round(float(preset["capcut_wm_size"]) * wm_scale * CAPCUT_SIZE_FACTOR)

        settings["rotation_sub"] = float(preset.get("rotation_sub", 0.0))
        settings["rotation_wm"] = float(preset.get("rotation_wm", 0.0))

        for k in ["font_size_sub", "font_size_wm", "watermark_text", "stroke_width", "shadow_offset", "font_name", "font_family", "pattern", "all_caps", "letter_spacing", "subtitle_style", "keywords", "subtitle_layout", "word_animation", "capitalization_mode"]:
            if k in preset:
                settings[k] = preset[k]

    # Scala per risoluzione effettiva rispetto al canvas logico 1080x1920
    scale = canvas_height / BASE_HEIGHT
    sub_ox = int(round(settings["offset_sub_x"] * scale))
    sub_oy = int(round(settings["offset_sub_y"] * scale))
    wm_ox  = int(round(settings["offset_wm_x"] * scale))
    wm_oy  = int(round(settings["offset_wm_y"] * scale))
    fs_sub = max(1, int(round(settings["font_size_sub"] * scale)))
    fs_wm  = max(1, int(round(settings["font_size_wm"] * scale)))
    stroke_w = max(0, int(round(settings.get("stroke_width", 0) * scale * 1.5)))
    shadow_off = max(0, int(round(settings.get("shadow_offset", 0) * scale * 1.8)))
    letter_spacing = int(round(settings.get("letter_spacing", 0) * scale))
    font_name = settings.get("font_name") or settings.get("font_family") or "Raleway"
    pattern = settings.get("pattern", "")
    all_caps = bool(settings.get("all_caps", False))
    word_animation = str(settings.get("word_animation") or (preset.get("word_animation") if preset else "none") or "none").lower().strip()
    capitalization_mode = str(settings.get("capitalization_mode") or (preset.get("capitalization_mode") if preset else "none") or "none").lower().strip()

    # Layout sottotitoli
    subtitle_layout = settings.get("subtitle_layout") or {}
    min_words_per_line = int(subtitle_layout.get("min_words_per_line", 2))
    max_words_per_line = int(subtitle_layout.get("max_words_per_line", 7))
    num_lines = int(subtitle_layout.get("num_lines", 2))

    # Carica i font separatamente per normal e keyword usando subtitle_style
    _subtitle_style = settings.get("subtitle_style") or {}
    _normal_style = _subtitle_style.get("normal") or {}
    _keyword_style = _subtitle_style.get("keyword") or {}

    normal_family = str(_normal_style.get("font_family") or font_name).strip()
    normal_variant = str(_normal_style.get("font_variant") or "Light").strip()
    keyword_family = str(_keyword_style.get("font_family") or font_name).strip()
    keyword_variant = str(_keyword_style.get("font_variant") or "SemiBold").strip()

    light_sub = load_font_variant(fs_sub, font_name=normal_family, variant=normal_variant)
    semibold_sub = load_font_variant(fs_sub, font_name=keyword_family, variant=keyword_variant)
    _,         semibold_wm  = load_pair(fs_wm, font_name=font_name)

    wm_path = work_dir / "watermark.png"
    render_watermark(
        semibold_wm,
        wm_path,
        settings["watermark_text"],
        offset_x=wm_ox,
        offset_y=wm_oy,
        stroke_width=stroke_w,
        shadow_offset=shadow_off,
        rotation=settings.get("rotation_wm", 0.0),
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )

    blank = render_blank(work_dir, canvas_width=canvas_width, canvas_height=canvas_height)

    # Gestione globale delle keyword.
    # Le selezioni bold_indices vengono comunque conservate nei chunk.
    keywords_config = settings.get("keywords") or {}
    keywords_enabled = bool(keywords_config.get("enabled", True))

    rendered: list[RenderedChunk] = []
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            raw_words = chunk.get("words", [])
            words = [w if isinstance(w, str) else w.get("word", "") for w in raw_words]
            if capitalization_mode and capitalization_mode != "none":
                words = [apply_capitalization(w, capitalization_mode) for w in words]
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
            if capitalization_mode and capitalization_mode != "none":
                words = [apply_capitalization(w, capitalization_mode) for w in words]
            kw = select_keyword(words)
            b_indices = {kw} if kw is not None else set()
            c_start = float(chunk.start)
            c_end = float(chunk.end)

        # Se le keyword sono disabilitate, il renderer non evidenzia
        # nessuna parola. I bold_indices originali restano intatti nei chunk.
        if not keywords_enabled:
            b_indices = set()

        if i > 0 and len(rendered) > 0:
            last_end = rendered[-1].end
            if c_start < last_end:
                c_start = last_end
        if c_end <= c_start:
            c_end = c_start + 0.15

        out = work_dir / f"sub_{i:04d}.png"
        # Colori Normal / Keyword dal nuovo sistema di stile.
        def _parse_color(value, fallback=TEXT_COLOR):
            if isinstance(value, (list, tuple)) and len(value) in (3, 4):
                try:
                    vals = tuple(int(x) for x in value)
                    return vals if len(vals) == 4 else vals + (255,)
                except (TypeError, ValueError):
                    return fallback

            if isinstance(value, str):
                raw_color = value.strip().lstrip("#")
                if len(raw_color) == 6:
                    try:
                        return (
                            int(raw_color[0:2], 16),
                            int(raw_color[2:4], 16),
                            int(raw_color[4:6], 16),
                            255,
                        )
                    except ValueError:
                        pass
                elif len(raw_color) == 8:
                    try:
                        return (
                            int(raw_color[0:2], 16),
                            int(raw_color[2:4], 16),
                            int(raw_color[4:6], 16),
                            int(raw_color[6:8], 16),
                        )
                    except ValueError:
                        pass

            return fallback

        current_subtitle_style = settings.get("subtitle_style") or {}
        current_normal_style = current_subtitle_style.get("normal") or {}
        current_keyword_style = current_subtitle_style.get("keyword") or {}

        normal_color = _parse_color(
            current_normal_style.get("color"),
            TEXT_COLOR,
        )
        keyword_color = _parse_color(
            current_keyword_style.get("color"),
            TEXT_COLOR,
        )

        # Configurazione Highlighter
        highlighter_config = settings.get("highlighter") or (preset.get("highlighter") if preset else {}) or {}
        highlighter_enabled = bool(highlighter_config.get("enabled", False))
        default_hl_box_color = _parse_color(highlighter_config.get("box_color"), fallback=(255, 230, 0, 255))
        default_hl_text_color = _parse_color(highlighter_config.get("text_color"), fallback=(0, 0, 0, 255))
        hl_radius = int(highlighter_config.get("box_radius", 8))
        hl_pad_x = int(highlighter_config.get("box_padding_x", 10))
        hl_pad_y = int(highlighter_config.get("box_padding_y", 4))
        raw_hl_stroke = highlighter_config.get("stroke_width", highlighter_config.get("stroke", 0))
        raw_hl_shadow = highlighter_config.get("shadow_offset", highlighter_config.get("shadow", 0))
        hl_stroke = int(round(float(raw_hl_stroke or 0) * scale))
        hl_shadow = int(round(float(raw_hl_shadow or 0) * scale))

        # Configurazione Stili Speaker
        speaker_styles_config = settings.get("speaker_styles") or (preset.get("speaker_styles") if preset else {}) or {}
        speaker_styles_enabled = bool(speaker_styles_config.get("enabled", False))
        speakers_map = speaker_styles_config.get("speakers") or {}

        chunk_normal_color = normal_color
        chunk_hl_box_color = default_hl_box_color

        if speaker_styles_enabled and isinstance(chunk, dict):
            spk_label = str(chunk.get("speaker") or f"Speaker {(chunk.get('speaker_id', 0) + 1)}")
            spk_conf = speakers_map.get(spk_label) or speakers_map.get(spk_label.lower().replace(" ", "_")) or {}
            if "color" in spk_conf and spk_conf["color"]:
                chunk_normal_color = _parse_color(spk_conf["color"], fallback=normal_color)
            if "highlight_color" in spk_conf and spk_conf["highlight_color"]:
                chunk_hl_box_color = _parse_color(spk_conf["highlight_color"], fallback=default_hl_box_color)

        # Rendering con highlighter o animazione parola per parola (se disponibile e abilitato)
        word_objs = raw_words if isinstance(chunk, dict) else []
        has_word_timings = (
            (highlighter_enabled or word_animation in ("pop", "scale", "fade", "slide_up", "slide_down"))
            and bool(word_objs)
            and all(isinstance(w, dict) and "start" in w and "end" in w for w in word_objs)
            and len(word_objs) > 0
        )

        chunk_line_breaks = chunk.get("line_breaks") if isinstance(chunk, dict) else getattr(chunk, "line_breaks", None)

        if has_word_timings:
            n_w = len(word_objs)
            # Determina una sequenza temporale continua [c_start, c_end] senza buchi (zero-gap)
            w0_start = float(word_objs[0].get("start", c_start))
            if w0_start > c_start + 0.25:
                # Se c'è una pausa iniziale prima della prima parola, mostra il sottotitolo neutro
                out_neutral = work_dir / f"sub_{i:04d}_intro.png"
                render_subtitle(
                    words,
                    b_indices,
                    light_sub,
                    semibold_sub,
                    out_neutral,
                    offset_x=sub_ox,
                    offset_y=sub_oy,
                    stroke_width=stroke_w,
                    shadow_offset=shadow_off,
                    pattern=pattern,
                    all_caps=all_caps,
                    letter_spacing=letter_spacing,
                    rotation=settings.get("rotation_sub", 0.0),
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                    normal_color=chunk_normal_color,
                    keyword_color=keyword_color,
                    min_words_per_line=min_words_per_line,
                    max_words_per_line=max_words_per_line,
                    num_lines=num_lines,
                    active_word_index=None,
                    highlighter_enabled=False,
                    line_breaks=chunk_line_breaks,
                    word_animation=word_animation,
                )
                rendered.append(RenderedChunk(image_path=out_neutral, start=c_start, end=w0_start))
                current_word_t = w0_start
            else:
                # Altrimenti la prima parola è attiva fin dall'inizio del blocco
                current_word_t = c_start

            for w_idx in range(n_w):
                w_info = word_objs[w_idx]
                w_end = float(w_info.get("end", c_end))

                if w_idx < n_w - 1:
                    next_start = float(word_objs[w_idx + 1].get("start", w_end))
                    boundary = (w_end + next_start) / 2.0 if w_end > next_start else next_start
                    frame_end = max(current_word_t + 0.04, boundary)
                else:
                    frame_end = max(current_word_t + 0.04, max(w_end, c_end))

                out_w = work_dir / f"sub_{i:04d}_w{w_idx:02d}.png"
                render_subtitle(
                    words,
                    b_indices,
                    light_sub,
                    semibold_sub,
                    out_w,
                    offset_x=sub_ox,
                    offset_y=sub_oy,
                    stroke_width=stroke_w,
                    shadow_offset=shadow_off,
                    pattern=pattern,
                    all_caps=all_caps,
                    letter_spacing=letter_spacing,
                    rotation=settings.get("rotation_sub", 0.0),
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                    normal_color=chunk_normal_color,
                    keyword_color=keyword_color,
                    min_words_per_line=min_words_per_line,
                    max_words_per_line=max_words_per_line,
                    num_lines=num_lines,
                    active_word_index=w_idx,
                    highlighter_enabled=highlighter_enabled,
                    highlighter_box_color=chunk_hl_box_color,
                    highlighter_text_color=default_hl_text_color,
                    highlighter_radius=hl_radius,
                    highlighter_padding_x=hl_pad_x,
                    highlighter_padding_y=hl_pad_y,
                    highlighter_stroke=hl_stroke,
                    highlighter_shadow=hl_shadow,
                    line_breaks=chunk_line_breaks,
                    word_animation=word_animation,
                )
                rendered.append(RenderedChunk(image_path=out_w, start=current_word_t, end=frame_end))
                current_word_t = frame_end
        else:
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
                letter_spacing=letter_spacing,
                rotation=settings.get("rotation_sub", 0.0),
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                normal_color=chunk_normal_color,
                keyword_color=keyword_color,
                min_words_per_line=min_words_per_line,
                max_words_per_line=max_words_per_line,
                num_lines=num_lines,
                active_word_index=None,
                highlighter_enabled=False,
                line_breaks=chunk_line_breaks,
                word_animation=word_animation,
            )
            rendered.append(RenderedChunk(image_path=out, start=c_start, end=c_end))

    console.log(f"[green]✓ {len(rendered)} frame sottotitolo renderizzati (sub_offset=({sub_ox},{sub_oy}), wm_offset=({wm_ox},{wm_oy}), canvas={canvas_width}x{canvas_height})[/]")
    ffconcat_path = create_ffconcat(rendered, blank, total_duration, work_dir)
    return rendered, ffconcat_path, wm_path
