"""
transcriber.py
Modulo per la trascrizione audio con faster-whisper e raggruppamento
word-level in chunk a singola riga (3-4 parole).
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Iterator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Strutture dati
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class WordToken:
    word: str
    start: float
    end: float
    is_bold: bool = False


@dataclasses.dataclass
class SubtitleChunk:
    words: list[WordToken]
    start: float
    end: float
    bold_indices: list[int] = dataclasses.field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.word for w in self.words)


# ---------------------------------------------------------------------------
# Parametri di chunking
# ---------------------------------------------------------------------------

MAX_WORDS_PER_CHUNK = 4
MAX_CHARS_PER_CHUNK = 26   # soglia morbida sui caratteri del testo (senza spazi tag)
MIN_CHUNK_DURATION = 0.6   # durata minima di un chunk in secondi
GAP_SPLIT_THRESHOLD = 0.5  # pausa > 500ms → forza nuovo chunk


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


def merge_apostrophe_tokens(words: list[WordToken]) -> list[WordToken]:
    """
    Unisce i token spezzati da apostrofi (es. 'l' + ''energia.' -> 'l'energia.', 'l'' + 'energia' -> 'l'energia')
    in un unico WordToken per evitare che vengano separati o spezzati su righe diverse.
    """
    if not words or len(words) < 2:
        return words

    import re
    elision_particles = {
        "l", "d", "c", "s", "m", "t", "v", "un", "all", "dell",
        "nell", "sull", "dall", "quest", "quell", "tutt", "qualch",
        "mezz", "poc", "sant", "com"
    }

    result: list[WordToken] = []
    i = 0
    n = len(words)

    while i < n:
        cur = words[i]
        while i + 1 < n:
            nxt = words[i + 1]
            cur_txt = cur.word.strip()
            nxt_txt = nxt.word.strip()

            ends_with_apos = bool(re.search(r"['’`´]$", cur_txt))
            starts_with_apos = bool(re.search(r"^['’`´]", nxt_txt))
            is_just_apos = bool(re.match(r"^['’`´]+$", cur_txt) or re.match(r"^['’`´]+$", nxt_txt))

            clean_cur = re.sub(r"^[^\w]+|[^\w]+$", "", cur_txt).lower()
            is_particle = clean_cur in elision_particles or len(cur_txt) <= 4

            should_merge = False
            merged_txt = ""

            if ends_with_apos:
                should_merge = True
                merged_txt = cur_txt + re.sub(r"^['’`´]+", "", nxt_txt)
            elif starts_with_apos and is_particle:
                should_merge = True
                merged_txt = cur_txt + nxt_txt
            elif is_just_apos:
                should_merge = True
                merged_txt = cur_txt + nxt_txt

            if should_merge:
                cur = dataclasses.replace(
                    cur,
                    word=merged_txt,
                    end=nxt.end,
                    is_bold=cur.is_bold or nxt.is_bold,
                )
                i += 1
            else:
                break

        result.append(cur)
        i += 1

    return result


# ---------------------------------------------------------------------------
# Caricamento modello
# ---------------------------------------------------------------------------

_MODEL_CACHE: dict[tuple[str, str], Any] = {}

def _load_model(model_size: str, compute_type: str):
    """Carica il modello faster-whisper con cache in RAM e fallback automatico."""
    from faster_whisper import WhisperModel  # import ritardato

    cache_key = (model_size, compute_type)
    if cache_key in _MODEL_CACHE:
        console.log(f"[green]✓ Modello Whisper '{model_size}' già presente in RAM (riutilizzo istantaneo)[/]")
        return _MODEL_CACHE[cache_key]

    bundled_candidates = [
        Path(__file__).resolve().parent / "models" / model_size,
        Path(__file__).resolve().parent.parent / "models" / model_size,
    ]
    target = model_size
    for candidate in bundled_candidates:
        if candidate.exists() and (candidate / "model.bin").exists():
            target = str(candidate)
            console.log(f"[cyan]Trovato modello Whisper integrato:[/] {target}")
            break

    console.log(
        f"[cyan]Caricamento modello Whisper in RAM:[/] {target} "
        f"(compute_type={compute_type})"
    )
    try:
        model = WhisperModel(target, device="cpu", compute_type=compute_type)
        _MODEL_CACHE[cache_key] = model
        console.log("[green]✓ Modello caricato e memorizzato in RAM[/]")
        return model
    except Exception as exc:
        if compute_type != "int8":
            console.log(
                f"[yellow]⚠ {compute_type} non disponibile, fallback a int8[/]"
            )
            return _load_model(model_size, "int8")
        raise RuntimeError(f"Impossibile caricare il modello: {exc}") from exc


# ---------------------------------------------------------------------------
# Trascrizione
# ---------------------------------------------------------------------------

def transcribe(
    audio_path: Path,
    model_size: str = "small",
    compute_type: str = "float16",
    language: str | None = "it",
    translate_to_it: bool = False,
    translation_engine: str = "auto",
    api_key: str | None = None,
) -> list[WordToken]:
    """
    Trascrive il file audio e restituisce la lista di WordToken ordinati.
    Se translate_to_it=True, traduce con contesto le frasi in italiano
    mantenendo la sincronizzazione temporale.

    Args:
        audio_path:         Percorso del file WAV.
        model_size:         Dimensione modello Whisper ('small', 'medium').
        compute_type:       Tipo di calcolo ('float16', 'int8').
        language:           Codice lingua ('it', 'en', None per auto-rilevamento).
        translate_to_it:    Se True, traduce le frasi in italiano con contesto.
        translation_engine: 'gemini', 'free' o 'auto'.
        api_key:            Chiave API Google Gemini (opzionale).

    Returns:
        Lista di WordToken con timestamp word-level.
    """
    model = _load_model(model_size, compute_type)

    console.log(f"[cyan]Trascrizione in corso:[/] {audio_path.name} (lingua={language or 'auto'})")

    whisper_lang = None if (language in (None, "", "auto")) else language

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Trascrizione audio…", total=None)

        segments_gen, info = model.transcribe(
            str(audio_path),
            language=whisper_lang,
            word_timestamps=True,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        # Converti il generatore in lista per poter accedere ai segmenti
        segments = list(segments_gen)

        words: list[WordToken] = []

        detected_lang = getattr(info, "language", "") or ""
        should_translate = (
            translate_to_it
            and detected_lang != "it"
            and language != "it"
        )

        if should_translate:
            from translator import translate_texts_contextual

            seg_list = []
            for s in segments:
                t = s.text.strip()
                if t:
                    seg_list.append((t, s.start, s.end))

            raw_texts = [item[0] for item in seg_list]
            console.log(f"[cyan]Traduzione contestuale in corso ({len(raw_texts)} frasi)...[/]")
            translated_texts = translate_texts_contextual(
                raw_texts,
                engine=translation_engine,
                api_key=api_key,
                src=info.language if info.language else "en",
                dest="it",
            )

            for (orig_text, seg_start, seg_end), trans_text in zip(seg_list, translated_texts):
                w_list = trans_text.split()
                if not w_list:
                    continue
                dur = max(0.3, seg_end - seg_start)
                weights = [max(1, len(w)) for w in w_list]
                total_w = sum(weights)
                cur_t = seg_start
                for w, weight in zip(w_list, weights):
                    w_dur = (weight / total_w) * dur
                    w_s = round(cur_t, 2)
                    w_e = round(min(seg_end, cur_t + w_dur), 2)
                    cur_t += w_dur
                    words.append(WordToken(
                        word=w,
                        start=w_s,
                        end=max(w_s + 0.05, w_e),
                    ))
        else:
            for segment in segments:
                if segment.words:
                    for w in segment.words:
                        cleaned = w.word.strip()
                        if cleaned:
                            words.append(WordToken(
                                word=cleaned,
                                start=w.start,
                                end=w.end,
                            ))
        words = merge_apostrophe_tokens(words)
        progress.update(task, completed=1)

    console.log(
        f"[green]✓ Trascrizione completata:[/] {len(words)} parole "
        f"({info.duration:.1f}s, lingua={info.language})"
    )
    return words


# ---------------------------------------------------------------------------
# Raggruppamento in chunk
# ---------------------------------------------------------------------------

def _chunk_is_full(current_words: list[WordToken], candidate: WordToken) -> bool:
    """Valuta se aggiungere `candidate` supererebbe i limiti del chunk."""
    if len(current_words) >= MAX_WORDS_PER_CHUNK:
        return True
    prospective_text = " ".join(w.word for w in current_words) + " " + candidate.word
    # rimuove la punteggiatura dal conteggio caratteri
    clean = prospective_text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")
    if len(clean.strip()) > MAX_CHARS_PER_CHUNK and len(current_words) >= 2:
        return True
    return False


def group_into_chunks(
    words: list[WordToken],
    min_words_per_line: int | None = None,
    max_words_per_line: int | None = None,
    num_lines: int | None = None,
) -> list[SubtitleChunk]:
    """
    Raggruppa i WordToken in SubtitleChunk, senza sovrapposizioni temporali.
    Se specificati parametri di layout (min_words_per_line, max_words_per_line, num_lines),
    applica direttamente la ri-segmentazione secondo layout.

    Args:
        words: Lista di WordToken in ordine cronologico.
        min_words_per_line: Minimo parole per riga (opzionale).
        max_words_per_line: Massimo parole per riga (opzionale).
        num_lines: Numero massimo di righe per chunk (opzionale).

    Returns:
        Lista di SubtitleChunk ordinata.
    """
    if not words:
        return []

    words = merge_apostrophe_tokens(words)

    if min_words_per_line is not None and max_words_per_line is not None and num_lines is not None:
        return resegment_subtitles(
            words,
            min_words_per_line=min_words_per_line,
            max_words_per_line=max_words_per_line,
            num_lines=num_lines,
        )

    chunks: list[SubtitleChunk] = []
    current: list[WordToken] = []

    for i, word in enumerate(words):
        if not current:
            current.append(word)
            continue

        # Forza nuovo chunk se c'è una pausa lunga
        gap = word.start - current[-1].end
        if gap >= GAP_SPLIT_THRESHOLD:
            chunks.append(SubtitleChunk(
                words=list(current),
                start=current[0].start,
                end=current[-1].end,
            ))
            current = [word]
            continue

        if _chunk_is_full(current, word):
            chunks.append(SubtitleChunk(
                words=list(current),
                start=current[0].start,
                end=current[-1].end,
            ))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(SubtitleChunk(
            words=list(current),
            start=current[0].start,
            end=current[-1].end,
        ))

    # Risolvi eventuali micros-overlap garantendo start < end e nessuna sovrapposizione
    for i in range(len(chunks) - 1):
        if chunks[i].end > chunks[i + 1].start:
            split_point = round((chunks[i].end + chunks[i + 1].start) / 2, 2)
            if split_point > chunks[i].start + 0.1 and split_point < chunks[i + 1].end - 0.1:
                chunks[i] = dataclasses.replace(chunks[i], end=split_point)
                chunks[i + 1] = dataclasses.replace(chunks[i + 1], start=split_point)
            else:
                chunks[i] = dataclasses.replace(
                    chunks[i], end=max(round(chunks[i].start + 0.15, 2), round(chunks[i + 1].start, 2))
                )
                if chunks[i + 1].start < chunks[i].end:
                    chunks[i + 1] = dataclasses.replace(
                        chunks[i + 1], start=chunks[i].end
                    )

    console.log(f"[green]✓ Raggruppamento:[/] {len(chunks)} chunk creati")
    return chunks


# ---------------------------------------------------------------------------
# Ri-segmentazione dinamica basata su parametri layout
# ---------------------------------------------------------------------------

def resegment_subtitles(
    words: list[dict[str, Any] | WordToken],
    min_words_per_line: int = 2,
    max_words_per_line: int = 7,
    num_lines: int = 2,
    gap_split_threshold: float = GAP_SPLIT_THRESHOLD,
) -> list[SubtitleChunk]:
    """
    Ri-segmenta le parole originali in nuovi SubtitleChunk basandosi sui
    parametri di layout specificati.

    Non riesegue Whisper: usa i timestamp word-level originali.

    Args:
        words: Lista di dizionari o WordToken con chiavi 'word', 'start', 'end'.
        min_words_per_line: Minimo parole per riga.
        max_words_per_line: Massimo parole per riga.
        num_lines: Numero massimo di righe per chunk.
        gap_split_threshold: Pausa (secondi) che forza nuovo chunk.

    Returns:
        Lista di SubtitleChunk con start=first_word.start, end=last_word.end.
    """
    if not words:
        return []

    # Normalizza input a WordToken e unifica token con apostrofi
    normalized: list[WordToken] = []
    for w in words:
        if isinstance(w, WordToken):
            normalized.append(w)
        else:
            normalized.append(WordToken(
                word=str(w.get("word", "")),
                start=float(w.get("start", 0.0)),
                end=float(w.get("end", 0.0)),
                is_bold=bool(w.get("is_bold", False)),
            ))
    normalized = merge_apostrophe_tokens(normalized)

    # Prima passa: raggruppa per pause lunghe (GAP_SPLIT_THRESHOLD)
    # Questo preserva le pause naturali dell'audio
    macro_chunks: list[list[WordToken]] = []
    current_macro: list[WordToken] = []

    for w in normalized:
        if not current_macro:
            current_macro.append(w)
            continue

        gap = w.start - current_macro[-1].end
        if gap >= gap_split_threshold:
            macro_chunks.append(current_macro)
            current_macro = [w]
        else:
            current_macro.append(w)

    if current_macro:
        macro_chunks.append(current_macro)

    # Seconda passa: dentro ogni macro-chunk, applica vincoli layout
    # per creare i chunk finali rispettando min/max parole per riga e num_lines
    final_chunks: list[SubtitleChunk] = []

    for macro in macro_chunks:
        if not macro:
            continue

        sub_chunks = _split_macro_by_layout(
            macro,
            min_words_per_line=min_words_per_line,
            max_words_per_line=max_words_per_line,
            num_lines=num_lines,
        )
        final_chunks.extend(sub_chunks)

    # Risolvi eventuali micro-overlap tra chunk finali
    for i in range(len(final_chunks) - 1):
        if final_chunks[i].end > final_chunks[i + 1].start:
            split_point = round((final_chunks[i].end + final_chunks[i + 1].start) / 2, 2)
            if split_point > final_chunks[i].start + 0.1 and split_point < final_chunks[i + 1].end - 0.1:
                final_chunks[i] = dataclasses.replace(final_chunks[i], end=split_point)
                final_chunks[i + 1] = dataclasses.replace(final_chunks[i + 1], start=split_point)
            else:
                final_chunks[i] = dataclasses.replace(
                    final_chunks[i], end=max(round(final_chunks[i].start + 0.15, 2), round(final_chunks[i + 1].start, 2))
                )
                if final_chunks[i + 1].start < final_chunks[i].end:
                    final_chunks[i + 1] = dataclasses.replace(
                        final_chunks[i + 1], start=final_chunks[i].end
                    )

    console.log(f"[green]✓ Ri-segmentazione:[/] {len(final_chunks)} chunk creati")
    return final_chunks


DANGLING_WORDS: set[str] = {
    # Italian articles
    "il", "lo", "la", "l'", "i", "gli", "le", "un", "uno", "una", "un'",
    # Italian prepositions (simple & articulated)
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
    "del", "dello", "della", "dei", "degli", "delle",
    "al", "allo", "alla", "ai", "agli", "alle",
    "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "nel", "nello", "nella", "nei", "negli", "nelle",
    "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "col", "coi",
    # Italian conjunctions & connectors
    "e", "ed", "o", "od", "ma", "se", "perche", "perché", "poiche", "poiché",
    "che", "cui", "mentre", "quando", "come", "quindi", "pero", "però", "pure",
    # Italian clitic pronouns
    "ci", "vi", "ti", "mi", "si", "li",
    # English common equivalents
    "the", "a", "an", "of", "to", "in", "for", "on", "with", "at", "by", "from",
    "and", "but", "or", "that", "which", "my", "your", "his", "her", "our", "their",
}


def _clean_word_for_dangling(w: str) -> str:
    import re
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def _score_split_boundary(words: list[WordToken], cut_idx: int) -> float:
    """
    Calcola il punteggio di appetibilità per effettuare un taglio tra words[cut_idx-1] e words[cut_idx].
    Considera punteggiatura, silenzi audio (gap temporale) e regole sintattiche (anti-dangling).
    """
    import re
    n = len(words)
    if cut_idx <= 0 or cut_idx >= n:
        return 0.0

    w_prev = words[cut_idx - 1]
    w_next = words[cut_idx]
    prev_txt = w_prev.word.strip()
    next_txt = w_next.word.strip()

    # 0. Penalità assoluta: mai spezzare parole legate da apostrofo
    if is_apostrophe_bound(prev_txt, next_txt):
        return -10000.0

    score = 0.0

    # 1. Punteggiatura finale forte (+120) o debole (+65)
    if re.search(r"[.?!]+[\"'\)]*$", prev_txt):
        score += 120.0
    elif re.search(r"[,;:\u2014\-]+[\"'\)]*$", prev_txt):
        score += 65.0

    # 2. Pausa naturale nel parlato (silence gap tra parole)
    gap = getattr(w_next, "start", 0.0) - getattr(w_prev, "end", 0.0)
    if gap > 0.04:
        score += min(100.0, (gap - 0.04) * 150.0)

    # 3. Penalità anti-dangling (non spezzare dopo articoli, preposizioni, congiunzioni)
    if not re.search(r"[.?!,;:\u2014\-]+$", prev_txt):
        cw = _clean_word_for_dangling(prev_txt)
        if cw in DANGLING_WORDS:
            score -= 80.0

    return score


def _split_macro_by_layout(
    words: list[WordToken],
    min_words_per_line: int,
    max_words_per_line: int,
    num_lines: int,
) -> list[SubtitleChunk]:
    """
    Divide un macro-chunk in sottotitoli rispettando i vincoli di layout.
    Utilizza programmazione dinamica e scoring multi-criterio (punteggiatura,
    gap audio, coerenza sintattica e rispetto rigoroso di min/max parole).
    """
    if not words:
        return []

    min_w = max(1, int(min_words_per_line))
    max_w = max(min_w, int(max_words_per_line))
    n_lines = min(2, max(1, int(num_lines)))
    n = len(words)

    # Caso 1: min == max (modalità rigida a parole fisse)
    if min_w == max_w:
        target = n_lines * max_w
        chunk_count = (n + target - 1) // target
        chunks: list[SubtitleChunk] = []
        pos = 0
        for _ in range(chunk_count):
            size = min(target, n - pos)
            chunk_words = words[pos : pos + size]
            b_indices = [i for i, w in enumerate(chunk_words) if getattr(w, "is_bold", False)]
            chunks.append(SubtitleChunk(
                words=list(chunk_words),
                start=chunk_words[0].start,
                end=chunk_words[-1].end,
                bold_indices=b_indices,
            ))
            pos += size
        return chunks

    s_max = n_lines * max_w
    s_min = max(1, min_w)
    ideal_min = n_lines * min_w if n_lines > 1 else min_w
    mid = (ideal_min + s_max) / 2.0

    # Se tutte le parole entrano comodamente nella capacità massima del chunk
    if n <= s_max:
        return [SubtitleChunk(
            words=list(words),
            start=words[0].start,
            end=words[-1].end,
            bold_indices=[i for i, w in enumerate(words) if getattr(w, "is_bold", False)],
        )]

    # Programmazione dinamica per trovare il partizionamento ottimale globale
    # dp[i] = miglior punteggio per il prefisso words[:i]
    dp = [-float("inf")] * (n + 1)
    parent = [-1] * (n + 1)
    dp[0] = 0.0

    for i in range(1, n + 1):
        for s in range(1, s_max + 1):
            j = i - s
            if j < 0:
                break
            if dp[j] == -float("inf"):
                continue

            if i < n:
                if s < s_min:
                    continue
                rem = n - i
                rem_penalty = 0.0
                if rem < s_min:
                    rem_penalty = -100.0
            else:
                rem_penalty = 0.0
                if s < s_min:
                    rem_penalty = -50.0 * (s_min - s)

            cut_s = _score_split_boundary(words, i) if i < n else 0.0
            len_s = -abs(s - mid) * 2.5
            total = dp[j] + cut_s + len_s + rem_penalty
            if total > dp[i]:
                dp[i] = total
                parent[i] = j

    # Ricostruzione dei tagli
    if dp[n] != -float("inf"):
        cuts = []
        curr = n
        while curr > 0:
            cuts.append(curr)
            curr = parent[curr]
        cuts.append(0)
        cuts.reverse()
    else:
        # Fallback di sicurezza in caso di impossibilità teorica di partizionamento
        import math
        chunk_count = math.ceil(n / s_max)
        base_size = n // chunk_count
        rem = n % chunk_count
        chunk_sizes = [base_size + (1 if k < rem else 0) for k in range(chunk_count)]
        cuts = [0]
        acc = 0
        for sz in chunk_sizes:
            acc += sz
            cuts.append(acc)

    chunks = []
    for k in range(len(cuts) - 1):
        chunk_words = words[cuts[k] : cuts[k + 1]]
        if not chunk_words:
            continue
        b_indices = [idx for idx, w in enumerate(chunk_words) if getattr(w, "is_bold", False)]
        chunks.append(SubtitleChunk(
            words=list(chunk_words),
            start=chunk_words[0].start,
            end=chunk_words[-1].end,
            bold_indices=b_indices,
        ))

    return chunks
