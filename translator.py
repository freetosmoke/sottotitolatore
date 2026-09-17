"""
translator.py
Modulo per la traduzione contestuale dall'inglese all'italiano per sottotitoli video.
Supporta:
1. Motore AI Avanzato (Google Gemini API): traduzione colloquiale, contestuale,
   non letterale, specializzata per Reel/TikTok/Shorts.
2. Motore Gratuito Web (MyMemory / Google Web Fallback): a livello di frase intera
   senza necessità di API Key.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("translator")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Motore 1: Google Gemini API (AI Contestuale Avanzata)
# ---------------------------------------------------------------------------

def _translate_with_gemini(texts: list[str], api_key: str) -> list[str] | None:
    """
    Traduce una lista di frasi/segmenti con Google Gemini usando il contesto globale
    del video e un prompt specifico per sottotitoli social non letterali.
    """
    if not api_key or not texts:
        return None

    # Utilizza gemini-1.5-flash (o gemini-2.0-flash se disponibile)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = (
        "Sei un copywriter e traduttore professionista per sottotitoli video (Instagram Reels, TikTok, YouTube Shorts).\n"
        "Traduci la seguente lista di frasi/segmenti video dall'inglese all'italiano.\n\n"
        "REGOLE TASSATIVE:\n"
        "1. La traduzione NON deve essere letterale o parola per parola, ma naturale, fluida, incisiva e parlata.\n"
        "2. Mantieni il significato logico e adatta modi di dire, espressioni idiomatiche e slang con le frasi comunemente usate in italiano nel linguaggio parlato moderno.\n"
        "3. Tieni conto del contesto globale dell'intero discorso per rendere la narrazione coesa.\n"
        "4. Restituisci ESCLUSIVAMENTE un JSON valido con la chiave 'translations', contenente un array di stringhe della stessa lunghezza dell'input.\n\n"
        f"Input frasi inglesi:\n{json.dumps(texts, ensure_ascii=False)}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
            candidate = resp_body.get("candidates", [])[0]
            content_text = candidate.get("content", {}).get("parts", [])[0].get("text", "")
            parsed = json.loads(content_text)
            translations = parsed.get("translations", [])
            if isinstance(translations, list) and len(translations) == len(texts):
                return [str(t).strip() for t in translations]
    except Exception as exc:
        logger.warning(f"Errore traduzione Gemini: {exc}. Fallback a motore gratuito.")
        return None

    return None


# ---------------------------------------------------------------------------
# Motore 2: Web Free (MyMemory + Fallback)
# ---------------------------------------------------------------------------

def _translate_sentence_mymemory(text: str, src: str = "en", dest: str = "it") -> str:
    """Traduzione di una singola frase con l'API gratuita MyMemory."""
    clean = text.strip()
    if not clean:
        return ""
    if src.lower() == dest.lower():
        return clean
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean)}&langpair={src}|{dest}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        status = str(data.get("responseStatus", ""))
        if status != "200":
            return clean
        res = data.get("responseData", {}).get("translatedText", "")
        if (
            res
            and not res.startswith("MYMEMORY WARNING")
            and "PLEASE SELECT TWO DISTINCT LANGUAGES" not in res.upper()
            and not res.upper().startswith("INVALID")
        ):
            return res.strip()
    return clean


def _translate_sentence_google_web(text: str, src: str = "en", dest: str = "it") -> str:
    """Fallback tramite endpoint web Google Translate."""
    clean = text.strip()
    if not clean:
        return ""
    if src.lower() == dest.lower():
        return clean
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest}&dt=t&q={urllib.parse.quote(clean)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        translated = "".join(part[0] for part in res[0] if part and part[0])
        return translated.strip()


def _translate_with_free_web(texts: list[str], src: str = "en", dest: str = "it") -> list[str]:
    """
    Traduzione per una lista di frasi a livello di frase intera
    mantenendo la struttura e il contesto grammaticale.
    """
    if src.lower() == dest.lower():
        return texts
    results: list[str] = []
    for t in texts:
        if not t.strip():
            results.append("")
            continue
        try:
            tr = _translate_sentence_mymemory(t, src, dest)
            results.append(tr)
        except Exception:
            try:
                tr = _translate_sentence_google_web(t, src, dest)
                results.append(tr)
            except Exception as e:
                logger.error(f"Errore traduzione frase '{t}': {e}")
                results.append(t)  # fallback testo originale
    return results


# ---------------------------------------------------------------------------
# Interfaccia Principale
# ---------------------------------------------------------------------------

def translate_texts_contextual(
    texts: list[str],
    engine: str = "auto",
    api_key: str | None = None,
    src: str = "en",
    dest: str = "it",
) -> list[str]:
    """
    Traduce contestualmente una lista di testi dall'inglese all'italiano.

    Args:
        texts: Lista di frasi / testi di segmenti o chunk.
        engine: 'gemini', 'free' o 'auto'.
        api_key: Chiave API Google Gemini (opzionale).
        src: Lingua di partenza (default 'en').
        dest: Lingua di arrivo (default 'it').

    Returns:
        Lista di testi tradotti in italiano.
    """
    if not texts:
        return []
    if src.lower() == dest.lower():
        return texts

    # 1. Prova con Gemini se disponibile o richiesto
    if api_key and engine in ("gemini", "ai", "auto"):
        res = _translate_with_gemini(texts, api_key)
        if res and len(res) == len(texts):
            return res

    # 2. Se Gemini non è configurato o ha fallito, usa il motore gratuito
    return _translate_with_free_web(texts, src=src, dest=dest)


def translate_chunks_data(
    chunks_data: list[dict[str, Any]],
    engine: str = "auto",
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """
    Traduce in italiano una lista di chunk già strutturati, preservando
    i timestamp start ed end di ciascun chunk e ricalcolando le parole interne.
    """
    from keyword_selector import select_keyword

    if not chunks_data:
        return []

    # Estrai i testi
    original_texts = [c.get("text") or " ".join(w.get("word", "") for w in c.get("words", [])) for c in chunks_data]

    # Traduci con contesto
    translated_texts = translate_texts_contextual(original_texts, engine=engine, api_key=api_key)

    new_chunks = []
    for orig_chunk, trans_text in zip(chunks_data, translated_texts):
        start = float(orig_chunk.get("start", 0.0))
        end = float(orig_chunk.get("end", start + 1.0))
        dur = max(0.2, end - start)

        words_raw = trans_text.split()
        if not words_raw:
            words_raw = ["..."]

        # Distribuisci il tempo tra le parole italiane proporzionalmente alla lunghezza
        char_weights = [max(1, len(w)) for w in words_raw]
        total_w = sum(char_weights)

        cur_time = start
        word_tokens = []
        for w, weight in zip(words_raw, char_weights):
            w_dur = (weight / total_w) * dur
            w_start = round(cur_time, 2)
            w_end = round(min(end, cur_time + w_dur), 2)
            cur_time += w_dur
            word_tokens.append({
                "word": w,
                "start": w_start,
                "end": max(w_start + 0.05, w_end),
            })

        # Bolding automatico della keyword principale in italiano
        words_list = [w["word"] for w in word_tokens]
        kw_idx = select_keyword(words_list)
        bold_indices = [kw_idx] if (kw_idx is not None and kw_idx >= 0) else []

        new_chunks.append({
            "id": orig_chunk.get("id", 0),
            "start": start,
            "end": end,
            "words": word_tokens,
            "bold_indices": bold_indices,
            "text": " ".join(words_list),
        })

    return new_chunks
