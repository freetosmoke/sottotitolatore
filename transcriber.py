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


@dataclasses.dataclass
class SubtitleChunk:
    words: list[WordToken]
    start: float
    end: float

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


def group_into_chunks(words: list[WordToken]) -> list[SubtitleChunk]:
    """
    Raggruppa i WordToken in SubtitleChunk a singola riga, senza
    sovrapposizioni temporali.

    Args:
        words: Lista di WordToken in ordine cronologico.

    Returns:
        Lista di SubtitleChunk ordinata.
    """
    if not words:
        return []

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

    # Normalizza input a WordToken
    normalized: list[WordToken] = []
    for w in words:
        if isinstance(w, WordToken):
            normalized.append(w)
        else:
            normalized.append(WordToken(
                word=str(w.get("word", "")),
                start=float(w.get("start", 0.0)),
                end=float(w.get("end", 0.0)),
            ))

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


def _split_macro_by_layout(
    words: list[WordToken],
    min_words_per_line: int,
    max_words_per_line: int,
    num_lines: int,
) -> list[SubtitleChunk]:
    """
    Divide un macro-chunk in sottotitoli rispettando i vincoli di layout.
    Priorità (come _layout_lines):
    1. num_lines (hard constraint)
    2. min_words_per_line
    3. max_words_per_line
    """
    if not words:
        return []

    min_w = max(1, int(min_words_per_line))
    max_w = max(min_w, int(max_words_per_line))
    n_lines = max(1, int(num_lines))

    n = len(words)

    # Massimo parole per chunk basato su layout: n_lines * max_w
    layout_max_words = n_lines * max_w

    # Se tutte le parole stanno in un chunk rispettando i vincoli, restituisci chunk singolo
    if n <= layout_max_words:
        return [SubtitleChunk(
            words=list(words),
            start=words[0].start,
            end=words[-1].end,
        )]

    # Altrimenti, dobbiamo dividere in più chunk
    # Ogni chunk può contenere al massimo layout_max_words parole
    chunks: list[SubtitleChunk] = []
    pos = 0

    while pos < n:
        # Quante parole possiamo mettere in questo chunk?
        remaining = n - pos
        chunk_size = min(layout_max_words, remaining)

        # Ma se le parole rimanenti dopo questo chunk sarebbero troppo poche
        # (meno di min_w * num_lines ma > 0), aggiustiamo
        remaining_after = remaining - chunk_size
        if 0 < remaining_after < min_w * n_lines:
            # Ridistribuiamo per evitare chunk finale troppo piccolo
            chunk_size = remaining - (min_w * n_lines)
            if chunk_size < min_w:
                chunk_size = min(layout_max_words, remaining)

        chunk_words = words[pos:pos + chunk_size]
        chunks.append(SubtitleChunk(
            words=list(chunk_words),
            start=chunk_words[0].start,
            end=chunk_words[-1].end,
        ))

        pos += chunk_size

    return chunks
