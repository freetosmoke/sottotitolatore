"""
test_silence_removal.py - Test suite per il modulo silence_remover (Fase 2).
Verifica:
1. Safety padding: preservazione delle pause brevi (< 2 * padding)
2. Taglio corretto di silenzi reali con margine di sicurezza
3. Protezione dei confini di parola (word-boundary protection)
4. Risincronizzazione e rimappatura coerente di timestamp e word timestamps
5. Test end-to-end con file audio/video reale generato con FFmpeg
"""
import unittest
import tempfile
import subprocess
from pathlib import Path

from bootstrap_manager import get_ffmpeg_path
import silence_remover


class TestSilenceRemoval(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_short_natural_pauses_preserved(self):
        """Le pause brevi (< 2 * padding, es. 200ms con padding 120ms) non devono essere tagliate."""
        total_duration = 10.0
        # Silenzio breve di 0.20s (tra 2.0s e 2.2s)
        silences = [(2.0, 2.2)]
        padding_sec = 0.12

        keeps = silence_remover.calculate_keep_intervals(
            total_duration,
            silences,
            padding_sec=padding_sec,
        )

        # L'intero intervallo da 0 a 10s deve rimanere continuo senza tagli
        self.assertEqual(len(keeps), 1)
        self.assertEqual(keeps[0], (0.0, 10.0))

    def test_long_silence_cut_with_safety_padding(self):
        """Un silenzio lungo (1.5s) viene rimosso lasciando il margine di padding ai bordi."""
        total_duration = 10.0
        # Silenzio da 3.0s a 4.5s (durata 1.5s)
        silences = [(3.0, 4.5)]
        padding_sec = 0.12

        keeps = silence_remover.calculate_keep_intervals(
            total_duration,
            silences,
            padding_sec=padding_sec,
        )

        # Due segmenti: da 0.0 a 3.12 (3.0 + padding) e da 4.38 (4.5 - padding) a 10.0
        self.assertEqual(len(keeps), 2)
        self.assertAlmostEqual(keeps[0][0], 0.0, places=2)
        self.assertAlmostEqual(keeps[0][1], 3.12, places=2)
        self.assertAlmostEqual(keeps[1][0], 4.38, places=2)
        self.assertAlmostEqual(keeps[1][1], 10.0, places=2)

    def test_word_boundary_protection(self):
        """Se un silenzio entra in contatto con parole note, le parole non vengono tagliate."""
        total_duration = 8.0
        silences = [(2.0, 4.0)]  # Silenzio teorico
        speech_chunks = [
            {
                "start": 0.5, "end": 2.2, "text": "parola che finisce a 2.2",
                "words": [{"word": "parola", "start": 1.8, "end": 2.2}]
            },
            {
                "start": 3.8, "end": 6.0, "text": "parola che inizia a 3.8",
                "words": [{"word": "parola", "start": 3.8, "end": 4.2}]
            }
        ]

        keeps = silence_remover.calculate_keep_intervals(
            total_duration,
            silences,
            padding_sec=0.10,
            speech_chunks=speech_chunks,
        )

        # Il primo segmento keep deve finire almeno dopo 2.2s (la parola)
        self.assertGreaterEqual(keeps[0][1], 2.2)
        # Il secondo segmento keep deve iniziare al massimo a 3.8s
        self.assertLessEqual(keeps[1][0], 3.8)

    def test_timestamp_remapping_continuity(self):
        """Verifica la rimappatura coerente dei chunk e delle singole parole senza sovrapposizioni."""
        keep_intervals = [(0.0, 3.0), (5.0, 8.0)]  # Rimosso intervallo 3.0 - 5.0 (2.0s)
        chunks = [
            {
                "start": 1.0,
                "end": 2.5,
                "text": "prima frase",
                "words": [
                    {"word": "prima", "start": 1.0, "end": 1.6},
                    {"word": "frase", "start": 1.7, "end": 2.5},
                ],
            },
            {
                "start": 5.5,
                "end": 7.0,
                "text": "seconda frase",
                "words": [
                    {"word": "seconda", "start": 5.5, "end": 6.1},
                    {"word": "frase", "start": 6.2, "end": 7.0},
                ],
            },
        ]

        remapped = silence_remover.remap_chunks_and_words(chunks, keep_intervals)
        self.assertEqual(len(remapped), 2)
        # Primo chunk invariato
        self.assertAlmostEqual(remapped[0]["start"], 1.0, places=2)
        self.assertAlmostEqual(remapped[0]["end"], 2.5, places=2)
        # Secondo chunk anticipato di 2.0s (da 5.5 a 3.5)
        self.assertAlmostEqual(remapped[1]["start"], 3.5, places=2)
        self.assertAlmostEqual(remapped[1]["end"], 5.0, places=2)
        self.assertAlmostEqual(remapped[1]["words"][0]["start"], 3.5, places=2)

    def test_ffmpeg_real_silence_detection_and_cut(self):
        """Crea un file video/audio con parlato e silenzio con FFmpeg ed esegue il taglio reale."""
        test_video = self.tmp_path / "test_silence.mp4"
        out_compact = self.tmp_path / "compact.mp4"

        # Genera video sintetico: 2s suono + 2s silenzio + 2s suono (totale 6s)
        ffmpeg = get_ffmpeg_path()
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=6:r=25",
            "-f", "lavfi", "-i", "sine=f=440:d=2",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=2",
            "-f", "lavfi", "-i", "sine=f=440:d=2",
            "-filter_complex", "[1:a][2:a][3:a]concat=n=3:v=0:a=1[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            str(test_video),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"FFmpeg error: {r.stderr}")

        # Rileva il silenzio (atteso tra ~2.0s e ~4.0s)
        detected = silence_remover.detect_silence_segments(
            test_video,
            min_silence_duration=0.4,
            noise_threshold_db=-38.0,
        )
        self.assertGreaterEqual(len(detected), 1)
        s_start, s_end = detected[0]
        self.assertTrue(1.8 <= s_start <= 2.2)
        self.assertTrue(3.8 <= s_end <= 4.2)

        # Calcola segmenti keep ed esegue compattamento fisico reale
        keeps = silence_remover.calculate_keep_intervals(6.0, detected, padding_sec=0.10)
        self.assertEqual(len(keeps), 2)

        out_path, comp_dur = silence_remover.cut_and_compact_video_audio(
            test_video,
            keeps,
            out_compact,
            use_hw=False,
            quality="fast",
        )
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)
        # La durata compattata deve essere inferiore ai 6s originali (circa 4.2s con padding)
        self.assertTrue(3.8 <= comp_dur <= 4.6)


if __name__ == "__main__":
    unittest.main()
