"""
test_speaker_diarization.py - Test suite per la diarizzazione vocale (Fase 1).
Verifica:
1. Monologo (singolo speaker)
2. Due speaker (cambio A -> B)
3. Alternanza speaker (A -> B -> A)
4. Forzatura target_k = 2 (non collassa a monologo anche con voci vicine)
5. Integrità dei timestamp e compatibilità rendering
"""
import unittest
import numpy as np
import tempfile
import wave
import struct
from pathlib import Path

import speaker_diarizer
from subtitle_renderer import render_all


def _generate_synthetic_wav(
    filepath: Path,
    segments: list[tuple[float, float, float, float]],
    sample_rate: int = 16000,
):
    """
    Genera un file WAV sintetico con toni armonici e formanti distinte.
    segments: lista di (start_sec, end_sec, f0_freq, f1_freq)
    """
    total_duration = max(s[1] for s in segments)
    total_samples = int(total_duration * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)

    for start_t, end_t, f0, f1 in segments:
        idx_start = int(start_t * sample_rate)
        idx_end = min(total_samples, int(end_t * sample_rate))
        n_samples = idx_end - idx_start
        t = np.arange(n_samples) / sample_rate
        # Fondamentale F0 + prima formante + terza armonica
        sig = (
            0.6 * np.sin(2 * np.pi * f0 * t)
            + 0.3 * np.sin(2 * np.pi * f1 * t)
            + 0.1 * np.sin(2 * np.pi * 3 * f0 * t)
        )
        # Ramping per evitare click
        ramp_len = min(200, n_samples // 2)
        if ramp_len > 0:
            ramp = np.linspace(0, 1, ramp_len)
            sig[:ramp_len] *= ramp
            sig[-ramp_len:] *= ramp[::-1]
        audio[idx_start:idx_end] = sig

    # Converti in int16
    audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


class TestSpeakerDiarization(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_single_speaker_monologue(self):
        """Verifica che un singolo speaker sia classificato come monologo (Speaker 1)."""
        wav_file = self.tmp_path / "mono.wav"
        # 3 segmenti dello stesso speaker a 130 Hz
        segments = [
            (0.0, 2.0, 130.0, 600.0),
            (2.2, 4.0, 130.0, 600.0),
            (4.2, 6.0, 130.0, 600.0),
        ]
        _generate_synthetic_wav(wav_file, segments)

        chunks = [
            {"start": 0.0, "end": 2.0, "text": "Ciao sono la prima voce", "words": []},
            {"start": 2.2, "end": 4.0, "text": "Continuo a parlare io", "words": []},
            {"start": 4.2, "end": 6.0, "text": "E concludo il discorso", "words": []},
        ]

        result = speaker_diarizer.diarize_audio(wav_file, chunks, num_speakers="auto")
        speakers = set(c["speaker"] for c in result)
        self.assertEqual(len(speakers), 1)
        self.assertEqual(list(speakers)[0], "Speaker 1")
        # I timestamp devono rimanere intatti
        self.assertEqual(result[0]["start"], 0.0)
        self.assertEqual(result[2]["end"], 6.0)

    def test_two_chunk_monologue_no_false_positive(self):
        """Verifica che un monologo di soli 2 blocchi non generi un falso cambio speaker."""
        wav_file = self.tmp_path / "mono_2chunks.wav"
        # Due segmenti dello stesso speaker con lieve variazione naturale (130 Hz vs 136 Hz)
        segments = [
            (0.0, 2.0, 130.0, 600.0),
            (2.2, 4.0, 136.0, 610.0),
        ]
        _generate_synthetic_wav(wav_file, segments)

        chunks = [
            {"start": 0.0, "end": 2.0, "text": "Prima frase del monologo", "words": []},
            {"start": 2.2, "end": 4.0, "text": "Seconda frase dello stesso interlocutore", "words": []},
        ]

        result = speaker_diarizer.diarize_audio(wav_file, chunks, num_speakers="auto")
        speakers = set(c["speaker"] for c in result)
        self.assertEqual(len(speakers), 1)
        self.assertEqual(list(speakers)[0], "Speaker 1")

    def test_two_speakers_transition_a_to_b(self):
        """Verifica transizione chiara da Speaker A a Speaker B."""
        wav_file = self.tmp_path / "two_speakers.wav"
        # Speaker A (110 Hz) poi Speaker B (210 Hz)
        segments = [
            (0.0, 2.0, 110.0, 500.0),
            (2.1, 4.0, 110.0, 500.0),
            (4.2, 6.2, 210.0, 950.0),
            (6.3, 8.5, 210.0, 950.0),
        ]
        _generate_synthetic_wav(wav_file, segments)

        chunks = [
            {"start": 0.0, "end": 2.0, "text": "Parla lo speaker uno", "words": []},
            {"start": 2.1, "end": 4.0, "text": "Ancora lo speaker uno", "words": []},
            {"start": 4.2, "end": 6.2, "text": "Ora risponde il secondo interlocutore", "words": []},
            {"start": 6.3, "end": 8.5, "text": "Che chiude la risposta", "words": []},
        ]

        result = speaker_diarizer.diarize_audio(wav_file, chunks, num_speakers="auto")
        spk_0 = result[0]["speaker"]
        spk_1 = result[1]["speaker"]
        spk_2 = result[2]["speaker"]
        spk_3 = result[3]["speaker"]

        self.assertEqual(spk_0, "Speaker 1")
        self.assertEqual(spk_1, "Speaker 1")
        self.assertEqual(spk_2, "Speaker 2")
        self.assertEqual(spk_3, "Speaker 2")

    def test_speakers_alternation_a_b_a(self):
        """Verifica sequenza con alternanza: A -> B -> A."""
        wav_file = self.tmp_path / "aba.wav"
        # Speaker A (120 Hz) -> Speaker B (190 Hz) -> Speaker A (120 Hz)
        segments = [
            (0.0, 2.0, 120.0, 520.0),
            (2.2, 4.2, 190.0, 880.0),
            (4.4, 6.5, 120.0, 520.0),
        ]
        _generate_synthetic_wav(wav_file, segments)

        chunks = [
            {"start": 0.0, "end": 2.0, "text": "Prima domanda di A", "words": []},
            {"start": 2.2, "end": 4.2, "text": "Risposta dello speaker B", "words": []},
            {"start": 4.4, "end": 6.5, "text": "Replica finale dello speaker A", "words": []},
        ]

        result = speaker_diarizer.diarize_audio(wav_file, chunks, num_speakers="auto")
        self.assertEqual(result[0]["speaker"], "Speaker 1")
        self.assertEqual(result[1]["speaker"], "Speaker 2")
        self.assertEqual(result[2]["speaker"], "Speaker 1")

    def test_forced_two_speakers_mode(self):
        """Verifica che con target_k=2 forzato, il sistema rispetti la scelta dell'utente."""
        wav_file = self.tmp_path / "forced.wav"
        # Due voci con pitch relativamente vicino (130 Hz vs 148 Hz)
        segments = [
            (0.0, 2.0, 130.0, 550.0),
            (2.1, 4.0, 148.0, 680.0),
        ]
        _generate_synthetic_wav(wav_file, segments)

        chunks = [
            {"start": 0.0, "end": 2.0, "text": "Frase primo interlocutore", "words": []},
            {"start": 2.1, "end": 4.0, "text": "Frase secondo interlocutore", "words": []},
        ]

        result = speaker_diarizer.diarize_audio(wav_file, chunks, num_speakers=2)
        speakers = [c["speaker"] for c in result]
        self.assertIn("Speaker 1", speakers)
        self.assertIn("Speaker 2", speakers)
        self.assertEqual(len(set(speakers)), 2)

    def test_diarized_chunks_rendering_compatibility(self):
        """Verifica che i chunk diarizzati siano renderizzabili senza errori con speaker_styles."""
        preset = {
            "speaker_styles": {
                "enabled": True,
                "speakers": {
                    "Speaker 1": {"color": "#FFFFFF", "highlight_color": "#00F0FF"},
                    "Speaker 2": {"color": "#FFEB3B", "highlight_color": "#FF007A"},
                },
                "muted_speakers": [],
            }
        }
        chunks = [
            {"start": 0.0, "end": 2.0, "speaker": "Speaker 1", "speaker_id": 0, "text": "Ciao Speaker 1", "words": [{"word": "Ciao", "start": 0.0, "end": 0.8}, {"word": "Speaker", "start": 0.9, "end": 1.5}, {"word": "1", "start": 1.5, "end": 2.0}]},
            {"start": 2.5, "end": 4.5, "speaker": "Speaker 2", "speaker_id": 1, "text": "Ciao Speaker 2", "words": [{"word": "Ciao", "start": 2.5, "end": 3.2}, {"word": "Speaker", "start": 3.3, "end": 4.0}, {"word": "2", "start": 4.0, "end": 4.5}]},
        ]
        rendered, ffconcat_path, wm_path = render_all(
            chunks,
            work_dir=self.tmp_path,
            total_duration=5.0,
            preset=preset,
        )
        self.assertGreater(len(rendered), 0)
        self.assertTrue(ffconcat_path.exists())
        self.assertTrue(wm_path.exists())


if __name__ == "__main__":
    unittest.main()
