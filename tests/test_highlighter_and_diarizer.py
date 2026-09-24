"""
tests/test_highlighter_and_diarizer.py
Test unitari per:
1. Effetto Highlighter parola per parola (subtitle_renderer)
2. Diarizzazione Speaker multi-interlocutore (speaker_diarizer)
"""
import wave
import tempfile
from pathlib import Path
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subtitle_renderer
import speaker_diarizer


def test_highlighter_rendering():
    print("--- Test Highlighter Rendering ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)

        chunks = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "CIAO MONDO VIRALE",
                "words": [
                    {"word": "CIAO", "start": 0.0, "end": 0.6},
                    {"word": "MONDO", "start": 0.6, "end": 1.2},
                    {"word": "VIRALE", "start": 1.2, "end": 2.0},
                ],
                "bold_indices": [1],
                "speaker": "Speaker 1",
            },
            {
                "id": 1,
                "start": 2.0,
                "end": 4.0,
                "text": "RISULTATI STRAORDINARI",
                "words": [
                    {"word": "RISULTATI", "start": 2.0, "end": 3.0},
                    {"word": "STRAORDINARI", "start": 3.0, "end": 4.0},
                ],
                "bold_indices": [0],
                "speaker": "Speaker 2",
            }
        ]

        preset = {
            "font_name": "Raleway",
            "highlighter": {
                "enabled": True,
                "box_color": "#FFE600",
                "text_color": "#000000",
                "box_radius": 8,
                "box_padding_x": 10,
                "box_padding_y": 4,
            },
            "speaker_styles": {
                "enabled": True,
                "speakers": {
                    "Speaker 1": {
                        "color": "#FFFFFF",
                        "highlight_color": "#FFE600",
                    },
                    "Speaker 2": {
                        "color": "#00F0FF",
                        "highlight_color": "#FF007A",
                    }
                }
            }
        }

        rendered, ffconcat_path, wm_path = subtitle_renderer.render_all(
            chunks=chunks,
            work_dir=work_dir,
            total_duration=4.0,
            preset=preset,
            canvas_width=1080,
            canvas_height=1920,
        )

        print(f"Frame generati: {len(rendered)}")
        assert len(rendered) >= 5, f"Dovrebbero esserci almeno 5 frame per le 5 parole, trovati: {len(rendered)}"
        assert ffconcat_path.exists(), "ffconcat.txt non generato"
        assert wm_path.exists(), "watermark.png non generato"

        for r in rendered:
            assert r.image_path.exists(), f"Frame {r.image_path} non esiste"
            assert r.end > r.start, f"Timing non valido per {r}"

        print("✓ Test Highlighter Rendering superato con successo!")


def test_speaker_diarizer():
    print("--- Test Speaker Diarization ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "test_dialogue.wav"

        # Genera audio con 2 voci a frequenza diversa (Voce 1: 130 Hz maschio, Voce 2: 240 Hz femmina)
        sr = 16000
        dur_total = 6.0
        t = np.linspace(0, dur_total, int(sr * dur_total), endpoint=False)

        # Segmenti:
        # 0.0 - 2.5s: Voce 1 (130 Hz + armoniche)
        # 2.5 - 3.0s: Silenzio
        # 3.0 - 5.5s: Voce 2 (240 Hz + armoniche)
        signal = np.zeros_like(t)

        m1 = (t >= 0.1) & (t <= 2.4)
        signal[m1] = 0.5 * np.sin(2 * np.pi * 130 * t[m1]) + 0.25 * np.sin(2 * np.pi * 260 * t[m1])

        m2 = (t >= 3.1) & (t <= 5.4)
        signal[m2] = 0.5 * np.sin(2 * np.pi * 240 * t[m2]) + 0.25 * np.sin(2 * np.pi * 480 * t[m2])

        # Converti a 16-bit PCM
        samples_int16 = (signal * 32767).astype(np.int16)

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(samples_int16.tobytes())

        chunks = [
            {"id": 0, "start": 0.2, "end": 1.2, "text": "Prima frase speaker uno"},
            {"id": 1, "start": 1.3, "end": 2.3, "text": "Seconda frase speaker uno"},
            {"id": 2, "start": 3.2, "end": 4.2, "text": "Prima risposta speaker due"},
            {"id": 3, "start": 4.3, "end": 5.3, "text": "Seconda risposta speaker due"},
        ]

        result = speaker_diarizer.diarize_audio(wav_path, chunks, num_speakers=2)

        print("Risultato Diarizzazione:")
        for c in result:
            print(f"  [{c['start']:.1f}s - {c['end']:.1f}s] {c['speaker']} (id={c['speaker_id']}): {c['text']}")

        assert result[0]["speaker"] == result[1]["speaker"], "I primi due blocchi devono avere lo stesso speaker"
        assert result[2]["speaker"] == result[3]["speaker"], "Gli ultimi due blocchi devono avere lo stesso speaker"
        assert result[0]["speaker"] != result[2]["speaker"], "Le due voci diverse devono avere speaker distinti"

        print("✓ Test Speaker Diarization superato con successo!")


def test_single_speaker_monologue():
    print("--- Test Single Speaker Monologue Detection ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "monologue.wav"
        sr = 16000
        dur_total = 6.0
        t = np.linspace(0, dur_total, int(sr * dur_total), endpoint=False)

        signal = np.zeros_like(t)
        for st, en in [(0.2, 1.2), (1.5, 2.5), (3.0, 4.0), (4.3, 5.3)]:
            m = (t >= st) & (t <= en)
            signal[m] = 0.5 * np.sin(2 * np.pi * 130 * t[m]) + 0.25 * np.sin(2 * np.pi * 260 * t[m])

        samples_int16 = (signal * 32767).astype(np.int16)
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(samples_int16.tobytes())

        chunks = [
            {"id": 0, "start": 0.2, "end": 1.2, "text": "Prima frase singolo speaker"},
            {"id": 1, "start": 1.5, "end": 2.5, "text": "Seconda frase singolo speaker"},
            {"id": 2, "start": 3.0, "end": 4.0, "text": "Terza frase singolo speaker"},
            {"id": 3, "start": 4.3, "end": 5.3, "text": "Quarta frase singolo speaker"},
        ]

        result = speaker_diarizer.diarize_audio(wav_path, chunks, num_speakers="auto")
        speakers = set(c["speaker"] for c in result)
        assert len(speakers) == 1, f"Atteso 1 solo speaker in monologo, trovati: {speakers}"
        assert result[0]["speaker"] == "Speaker 1"
        print("✓ Test Single Speaker Monologue Detection superato con successo!")


def test_apostrophe_handling():
    print("--- Test Apostrophe Handling & Non-Splitting Intelligence ---")
    from transcriber import WordToken, merge_apostrophe_tokens
    from subtitle_renderer import _layout_lines, load_font_variant

    # 1. Test unione token Whisper con apostrofo
    tokens = [
        WordToken(word="l", start=2.23, end=2.35),
        WordToken(word="'energia.", start=2.35, end=2.75, is_bold=True),
        WordToken(word="c'", start=2.8, end=2.9),
        WordToken(word="è", start=2.9, end=3.1),
    ]
    merged = merge_apostrophe_tokens(tokens)
    assert len(merged) == 2, f"Attesi 2 token dopo l'unione apostrofi, ottenuti: {len(merged)}"
    assert merged[0].word == "l'energia.", f"Atteso 'l'energia.', ottenuto: {merged[0].word}"
    assert merged[0].is_bold is True, "Il grassetto doveva essere ereditato"
    assert merged[1].word == "c'è", f"Atteso 'c'è', ottenuto: {merged[1].word}"
    print("  ✓ merge_apostrophe_tokens ha unificato 'l' + ''energia.' e 'c'' + 'è'")

    # 2. Test layout con token legati da apostrofo (non devono mai essere spezzati su 2 righe)
    font_reg = load_font_variant(size=36, font_name="Montserrat", variant="Regular")
    font_bold = load_font_variant(size=36, font_name="Montserrat", variant="Bold")

    # Caso A: solo ["l", "'energia."] con num_lines=2
    # L'algoritmo non deve separare 'l' da ''energia.' -> deve produrre 1 riga
    lines_a = _layout_lines(
        words=["l", "'energia."],
        is_bold_fn=lambda idx: idx == 1,
        light_font=font_reg,
        semibold_font=font_bold,
        letter_spacing=0,
        space_w=10,
        max_width=500,
        min_words_per_line=2,
        max_words_per_line=3,
        num_lines=2,
    )
    assert len(lines_a) == 1, f"Attesa 1 riga per token indivisibili con apostrofo, ottenute: {len(lines_a)}"
    assert [t[1] for t in lines_a[0]] == ["l", "'energia."]
    print("  ✓ _layout_lines non separa 'l' e ''energia.' su due righe")

    # Caso B: frase con apostrofo in mezzo: ["QUESTO", "È", "L'", "ENERGIA"]
    # Taglio k=2 (QUESTO È / L' ENERGIA) deve essere scelto; k=3 (QUESTO È L' / ENERGIA) vietato
    lines_b = _layout_lines(
        words=["QUESTO", "È", "L'", "ENERGIA"],
        is_bold_fn=lambda idx: False,
        light_font=font_reg,
        semibold_font=font_bold,
        letter_spacing=0,
        space_w=10,
        max_width=500,
        min_words_per_line=2,
        max_words_per_line=3,
        num_lines=2,
    )
    assert len(lines_b) == 2, f"Attese 2 righe, ottenute: {len(lines_b)}"
    r1 = [t[1] for t in lines_b[0]]
    r2 = [t[1] for t in lines_b[1]]
    assert r1 == ["QUESTO", "È"], f"Riga 1 errata: {r1}"
    assert r2 == ["L'", "ENERGIA"], f"Riga 2 errata: {r2}"
    print("  ✓ _layout_lines mantiene 'L'' ed 'ENERGIA' sulla stessa riga (Riga 2)")

    print("✓ Test Apostrophe Handling superato con successo!")


if __name__ == "__main__":
    test_highlighter_rendering()
    test_speaker_diarizer()
    test_single_speaker_monologue()
    test_apostrophe_handling()
    print("\n🎉 TUTTI I TEST DI HIGHLIGHTER E DIARIZZAZIONE COMPLETATI CON SUCCESSO!")
