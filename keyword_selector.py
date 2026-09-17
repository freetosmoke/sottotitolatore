"""
keyword_selector.py
Modulo per la selezione automatica della parola chiave in ogni chunk
tramite logica euristica con stopword italiane.
"""
from __future__ import annotations

import re
import string

# ---------------------------------------------------------------------------
# Stopword italiane (articoli, preposizioni, congiunzioni, ausiliari, pronomi)
# ---------------------------------------------------------------------------

ITALIAN_STOPWORDS: frozenset[str] = frozenset({
    # articoli determinativi
    "il", "lo", "la", "i", "gli", "le",
    # articoli indeterminativi
    "un", "uno", "una", "un'",
    # preposizioni semplici
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
    # preposizioni articolate più comuni
    "del", "dello", "della", "dei", "degli", "delle",
    "al", "allo", "alla", "ai", "agli", "alle",
    "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "nel", "nello", "nella", "nei", "negli", "nelle",
    "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "col", "coi",
    # congiunzioni
    "e", "ed", "o", "oppure", "ma", "però", "se", "che",
    "perché", "perche", "quindi", "dunque", "però", "anzi",
    "mentre", "quando", "come", "anche", "pure", "né", "ne",
    "sia", "benché", "sebbene", "affinché",
    # pronomi / particelle
    "non", "mi", "ti", "ci", "vi", "si", "lo", "la", "li", "le",
    "ne", "me", "te", "lui", "lei", "noi", "voi", "loro", "essi",
    "questo", "questa", "questi", "queste", "quello", "quella",
    "quelli", "quelle", "che", "chi", "cui",
    # ausiliari / verbi molto comuni
    "ho", "hai", "ha", "abbiamo", "avete", "hanno",
    "sono", "sei", "è", "siamo", "siete",
    "era", "ero", "erano", "eri", "eravamo", "eravate",
    "fu", "fui", "furono",
    "sarò", "sarai", "sarà", "saremo", "sarete", "saranno",
    "avevo", "aveva", "avevamo", "avevate", "avevano",
    "fare", "fatto", "fare",
    "essere", "avere",
    # avverbi generici
    "molto", "poco", "più", "meno", "già", "ancora", "sempre",
    "mai", "qui", "qua", "lì", "là", "così", "allora", "poi",
    "però", "invece", "proprio", "quasi", "solo", "soltanto",
    "anche", "pure", "appena", "ormai", "ecco",
})

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def _clean_word(word: str) -> str:
    """Rimuove punteggiatura e porta in minuscolo."""
    return _PUNCT_RE.sub("", word).lower().strip()


def select_keyword(words: list[str]) -> int | None:
    """
    Seleziona l'indice della parola chiave più significativa nella lista.

    Strategia:
    1. Filtra le stopword.
    2. Tra i candidati, sceglie la parola con il maggior numero di caratteri.
    3. In caso di parità, preferisce quella con posizione più centrale.

    Args:
        words: Lista di parole del chunk (con punteggiatura originale).

    Returns:
        Indice (0-based) della parola chiave, o None se tutte sono stopword.
    """
    candidates: list[tuple[int, str, int]] = []  # (idx, cleaned, len)
    for idx, w in enumerate(words):
        cleaned = _clean_word(w)
        if cleaned and cleaned not in ITALIAN_STOPWORDS:
            candidates.append((idx, cleaned, len(cleaned)))

    if not candidates:
        return None

    # Ordina per lunghezza decrescente, poi per posizione centrale
    mid = len(words) / 2.0
    candidates.sort(key=lambda t: (-t[2], abs(t[0] - mid)))
    return candidates[0][0]


def apply_bold_tag(words: list[str]) -> str:
    """
    Costruisce la stringa di testo del chunk applicando il tag ASS grassetto
    \\b600 alla parola chiave selezionata e ripristinando \\b300 subito dopo.

    Args:
        words: Lista di parole del chunk (con punteggiatura originale).

    Returns:
        Stringa formattata con tag ASS inline.
    """
    kw_idx = select_keyword(words)

    if kw_idx is None:
        return " ".join(words)

    parts: list[str] = []
    for i, w in enumerate(words):
        if i == kw_idx:
            parts.append(r"{\b600}" + w + r"{\b300}")
        else:
            parts.append(w)

    return " ".join(parts)
