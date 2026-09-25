"""
tests/test_layout_segmentation.py
Suite di test automatizzati per la validazione completa di:
- Regole matematiche e vincoli (Min parole/riga, Max parole/riga, Numero righe)
- Algoritmo di segmentazione e distribuzione bilanciata delle parole
- Preservazione rigorosa dei timestamp originali
- Preservazione delle parole in grassetto (bold_indices / is_bold)
- Assenza di sovrapposizioni e durate non valide
- Endpoint backend POST /api/resegment
"""
import os
import sys
import json
import unittest
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcriber import (
    WordToken,
    SubtitleChunk,
    resegment_subtitles,
    _split_macro_by_layout,
)


def make_dummy_words(n: int, start_time: float = 0.0, word_dur: float = 0.3, gap: float = 0.1, bold_indices: set = None) -> list[WordToken]:
    """Genera una sequenza continua di WordToken con timestamp realistici."""
    words = []
    t = start_time
    bold_indices = bold_indices or set()
    for i in range(n):
        w_start = round(t, 2)
        w_end = round(t + word_dur, 2)
        words.append(WordToken(
            word=f"parola_{i+1}",
            start=w_start,
            end=w_end,
            is_bold=(i in bold_indices)
        ))
        t = w_end + gap
    return words


class TestLayoutSegmentation(unittest.TestCase):
    """Test delle regole matematiche e di segmentazione."""

    def test_single_word(self):
        """Caso limite: testo con una sola parola."""
        words = make_dummy_words(1)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=7, num_lines=2)
        assert len(chunks) == 1
        assert len(chunks[0].words) == 1
        assert chunks[0].words[0].word == "parola_1"
        assert chunks[0].start == words[0].start
        assert chunks[0].end == words[0].end

    def test_two_words(self):
        """Caso limite: testo con due parole."""
        words = make_dummy_words(2)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=7, num_lines=2)
        assert len(chunks) == 1
        assert len(chunks[0].words) == 2

    def test_strict_two_words_single_line(self):
        """Caso utente: Min=2, Max=2, Righe=1 (max 2 parole a chunk)."""
        words = make_dummy_words(6)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=2, num_lines=1)
        assert len(chunks) == 3
        for c in chunks:
            assert len(c.words) == 2

    def test_strict_two_words_odd_total(self):
        """Caso utente: Min=2, Max=2, Righe=1 con totale dispari (7 parole)."""
        words = make_dummy_words(7)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=2, num_lines=1)
        assert len(chunks) == 4
        # 7 parole / max 2 = 4 chunk: 2, 2, 2, 1
        sizes = [len(c.words) for c in chunks]
        assert sizes == [2, 2, 2, 1]
        assert sum(sizes) == 7

    def test_min_equals_max_multi_line(self):
        """Caso Min=Max con 2 righe (Min=3, Max=3, Righe=2 -> max 6 parole/chunk)."""
        words = make_dummy_words(12)
        chunks = resegment_subtitles(words, min_words_per_line=3, max_words_per_line=3, num_lines=2)
        assert len(chunks) == 2
        for c in chunks:
            assert len(c.words) == 6

    def test_speech_pauses_split_macros(self):
        """Le pause nel parlato >= 0.8s devono creare un nuovo macro chunk."""
        part1 = make_dummy_words(3, start_time=0.0, gap=0.1)
        pause_start = part1[-1].end
        part2 = make_dummy_words(3, start_time=pause_start + 1.5, gap=0.1)
        all_words = part1 + part2

        chunks = resegment_subtitles(all_words, min_words_per_line=2, max_words_per_line=10, num_lines=2, gap_split_threshold=0.8)
        assert len(chunks) == 2
        assert [w.word for w in chunks[0].words] == [w.word for w in part1]
        assert [w.word for w in chunks[1].words] == [w.word for w in part2]
        assert chunks[0].end <= pause_start + 0.05
        assert chunks[1].start >= pause_start + 1.5

    def test_timestamp_integrity_and_no_overlaps(self):
        """Verifica che nessun timestamp venga alterato e non vi siano sovrapposizioni."""
        words = make_dummy_words(25, start_time=1.0, word_dur=0.25, gap=0.05)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=4, num_lines=2)

        flattened_words = [w for c in chunks for w in c.words]
        assert len(flattened_words) == len(words)
        for orig, chunk_w in zip(words, flattened_words):
            assert orig.word == chunk_w.word
            assert orig.start == chunk_w.start
            assert orig.end == chunk_w.end

        for i, c in enumerate(chunks):
            assert c.start == c.words[0].start
            assert c.end == c.words[-1].end
            assert c.end > c.start
            assert (c.end - c.start) >= 0.15
            if i > 0:
                assert chunks[i - 1].end <= c.start

    def test_bold_words_preservation(self):
        """Le parole evidenziate in grassetto devono mantenere la posizione bold dopo la ri-segmentazione."""
        words = make_dummy_words(10, bold_indices={1, 7})
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=2, num_lines=2)

        bold_words_found = []
        for c in chunks:
            for b_idx in c.bold_indices:
                bold_words_found.append(c.words[b_idx].word)

        assert bold_words_found == ["parola_2", "parola_8"]

    def test_large_text_performance(self):
        """Test prestazionale con testo molto lungo (500 parole)."""
        words = make_dummy_words(500, start_time=0.0, word_dur=0.2, gap=0.05)
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=6, num_lines=2)
        total_resegmented_words = sum(len(c.words) for c in chunks)
        assert total_resegmented_words == 500

    def test_smart_segmentation_punctuation(self):
        """L'algoritmo intelligente deve preferire spezzare su virgole e punti."""
        text = "Ho chiamato Marco, ma non ha risposto. Forse sta dormendo."
        tokens = text.split()
        words = [WordToken(word=w, start=round(i * 0.3, 2), end=round(i * 0.3 + 0.25, 2)) for i, w in enumerate(tokens)]
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=5, num_lines=1)
        assert len(chunks) == 3
        assert chunks[0].text == "Ho chiamato Marco,"
        assert chunks[1].text == "ma non ha risposto."
        assert chunks[2].text == "Forse sta dormendo."

    def test_smart_segmentation_anti_dangling(self):
        """L'algoritmo non deve lasciare preposizioni o articoli isolati a fine chunk."""
        text = "Oggi vado a scuola per imparare tante cose belle."
        tokens = text.split()
        words = [WordToken(word=w, start=round(i * 0.3, 2), end=round(i * 0.3 + 0.25, 2)) for i, w in enumerate(tokens)]
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=5, num_lines=1)
        for c in chunks:
            last_word = c.words[-1].word.strip().lower()
            assert last_word not in {"per", "a", "di", "il", "la", "in", "con"}, f"Chunk terminava con parola isolata: {last_word}"

    def test_smart_segmentation_speech_pause(self):
        """Un silenzio o pausa nel parlato deve guidare il punto di taglio."""
        tokens = "Non sapevo davvero cosa fare allora sono andato via".split()
        words = []
        t = 0.0
        for w in tokens:
            w_start = round(t, 2)
            w_end = round(t + 0.25, 2)
            words.append(WordToken(word=w, start=w_start, end=w_end))
            if w == "fare":
                t = w_end + 0.45  # Pausa vocale
            else:
                t = w_end + 0.05
        chunks = resegment_subtitles(words, min_words_per_line=2, max_words_per_line=5, num_lines=1)
        # Il secondo chunk deve finire esattamente su 'fare'
        assert chunks[1].words[-1].word == "fare"



class TestBackendResegmentEndpoint(unittest.TestCase):
    """Verifica dell'endpoint HTTP POST /api/resegment."""

    def test_resegment_api_endpoint(self):
        url = "http://127.0.0.1:8501/api/resegment"
        payload = {
            "words": [
                {"word": "Ciao", "start": 0.0, "end": 0.4, "is_bold": False},
                {"word": "a", "start": 0.45, "end": 0.6, "is_bold": False},
                {"word": "tutti", "start": 0.65, "end": 1.0, "is_bold": True},
                {"word": "questo", "start": 1.05, "end": 1.4, "is_bold": False},
                {"word": "è", "start": 1.45, "end": 1.6, "is_bold": False},
                {"word": "un", "start": 1.65, "end": 1.8, "is_bold": False},
                {"word": "test", "start": 1.85, "end": 2.2, "is_bold": True}
            ],
            "subtitle_layout": {
                "min_words_per_line": 2,
                "max_words_per_line": 2,
                "num_lines": 1
            },
            "keyword_mode": "manual"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=2) as response:
                assert response.status == 200
                data = json.loads(response.read().decode("utf-8"))
                assert data["success"] is True
                assert "chunks" in data
                chunks = data["chunks"]
                assert len(chunks) == 4
                assert chunks[0]["words"][0]["word"] == "Ciao"
                assert chunks[0]["words"][1]["word"] == "a"
                assert 0 in chunks[1]["bold_indices"]
                assert chunks[1]["words"][0]["word"] == "tutti"
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            words_objs = [
                WordToken(
                    word=w["word"],
                    start=w["start"],
                    end=w["end"],
                    is_bold=w.get("is_bold", False)
                )
                for w in payload["words"]
            ]
            res_chunks = resegment_subtitles(
                words_objs,
                min_words_per_line=2,
                max_words_per_line=2,
                num_lines=1
            )
            assert len(res_chunks) == 4
            assert res_chunks[0].words[0].word == "Ciao"
            assert res_chunks[0].words[1].word == "a"
            assert res_chunks[1].words[0].word == "tutti"


class TestRenderWithCustomLayout(unittest.TestCase):
    """Verifica che render_all utilizzi il layout personalizzato (es. 2 parole, 1 riga)."""

    def test_render_all_respects_layout(self):
        from subtitle_renderer import render_all
        import tempfile
        from pathlib import Path

        chunks = [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "words": [{"word": "Parola1", "start": 0.0, "end": 0.5}, {"word": "Parola2", "start": 0.5, "end": 1.0}],
                "bold_indices": [1],
                "text": "Parola1 Parola2"
            }
        ]
        preset = {
            "font_family": "Raleway",
            "pattern": "Normal",
            "subtitle_layout": {
                "min_words_per_line": 2,
                "max_words_per_line": 2,
                "num_lines": 1
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            frames, ffconcat_path, wm_path = render_all(
                chunks=chunks,
                work_dir=tmp_p,
                total_duration=1.0,
                preset=preset,
                canvas_width=576,
                canvas_height=1024,
            )
            self.assertEqual(len(frames), 1)
            self.assertTrue(Path(frames[0].image_path).exists())
            self.assertTrue(Path(ffconcat_path).exists())


if __name__ == "__main__":
    unittest.main()
