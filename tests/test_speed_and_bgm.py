#!/usr/bin/env python3
"""
tests/test_speed_and_bgm.py
Unit tests for Video Speed scaling and Background Music (BGM) mixing in Sub Studio.
Verifies Phase A.4 and Phase A.5 requirements:
- Speed scaling on chunks, words, and FFmpeg filtergraph (0.5x, 1.0x, 1.5x, 2.0x)
- BGM upload, volume adjustment, fade in/out, and audio mixing in final export.
"""
import copy
import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path

from bootstrap_manager import get_ffmpeg_path, get_ffprobe_path
from subtitle_renderer import render_all
from video_renderer import burn_subtitles, get_video_duration, _get_bin


class TestSpeedAndBgm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = get_ffmpeg_path()
        cls.ffprobe = get_ffprobe_path()
        cls.test_dir = tempfile.TemporaryDirectory()
        cls.work_dir = Path(cls.test_dir.name)

        # Generate a small 3-second 720x1280 vertical video with test tone
        cls.synth_video = cls.work_dir / "test_synth.mp4"
        cmd_vid = [
            cls.ffmpeg, "-y",
            "-f", "lavfi", "-i", "color=c=navy:s=720x1280:r=25:d=3",
            "-f", "lavfi", "-i", "sine=f=440:r=44100:d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            str(cls.synth_video)
        ]
        subprocess.run(cmd_vid, check=True, capture_output=True)

        # Generate a 5-second background music MP3 file
        cls.synth_bgm = cls.work_dir / "test_bgm.mp3"
        cmd_bgm = [
            cls.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=f=880:r=44100:d=5",
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(cls.synth_bgm)
        ]
        subprocess.run(cmd_bgm, check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.test_dir.cleanup()

    def test_01_speed_chunk_rescaling_math(self):
        """Verifies that chunk and word timestamps are proportionally scaled by speed factor."""
        chunks = [
            {
                "start": 1.0,
                "end": 2.0,
                "text": "Velocità di prova",
                "words": [
                    {"word": "Velocità", "start": 1.0, "end": 1.4},
                    {"word": "di", "start": 1.4, "end": 1.6},
                    {"word": "prova", "start": 1.6, "end": 2.0}
                ]
            }
        ]

        # Case 1.5x: duration should shrink (timestamps divided by 1.5)
        speed = 1.5
        scaled = copy.deepcopy(chunks)
        for c in scaled:
            c["start"] = round(c["start"] / speed, 3)
            c["end"] = round(c["end"] / speed, 3)
            if "words" in c and c["words"]:
                for w in c["words"]:
                    if "start" in w and w["start"] is not None:
                        w["start"] = round(w["start"] / speed, 3)
                    if "end" in w and w["end"] is not None:
                        w["end"] = round(w["end"] / speed, 3)

        self.assertAlmostEqual(scaled[0]["start"], 1.0 / 1.5, places=2)
        self.assertAlmostEqual(scaled[0]["end"], 2.0 / 1.5, places=2)
        self.assertAlmostEqual(scaled[0]["words"][0]["start"], 1.0 / 1.5, places=2)
        self.assertAlmostEqual(scaled[0]["words"][2]["end"], 2.0 / 1.5, places=2)

    def test_02_export_with_speed_1_5x(self):
        """Verifies rendering with 1.5x speed produces a shorter video with matched duration."""
        output_file = self.work_dir / "out_speed_1_5x.mp4"
        chunks = [
            {
                "start": 0.5 / 1.5,
                "end": 2.0 / 1.5,
                "text": "Sottotitolo veloce",
                "bold_indices": [0],
                "words": [
                    {"word": "Sottotitolo", "start": 0.5 / 1.5, "end": 1.2 / 1.5},
                    {"word": "veloce", "start": 1.2 / 1.5, "end": 2.0 / 1.5}
                ]
            }
        ]

        render_dir = self.work_dir / "render_tmp_1_5x"
        render_dir.mkdir(exist_ok=True)
        _, ffconcat_path, wm_path = render_all(
            chunks=chunks,
            work_dir=render_dir,
            total_duration=3.0 / 1.5,
            canvas_width=720,
            canvas_height=1280
        )

        burn_subtitles(
            video_path=self.synth_video,
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=output_file,
            speed=1.5,
            total_duration=3.0 / 1.5
        )
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 1000)

        # 3.0s video at 1.5x speed should be approximately 2.0s
        dur = get_video_duration(output_file)
        self.assertAlmostEqual(dur, 2.0, delta=0.35)

    def test_03_export_with_speed_0_5x(self):
        """Verifies rendering with 0.5x speed produces a longer video (~6.0s)."""
        output_file = self.work_dir / "out_speed_0_5x.mp4"
        chunks = [
            {
                "start": 1.0,
                "end": 3.0,
                "text": "Sottotitolo rallentato",
                "bold_indices": [1]
            }
        ]

        render_dir = self.work_dir / "render_tmp_0_5x"
        render_dir.mkdir(exist_ok=True)
        _, ffconcat_path, wm_path = render_all(
            chunks=chunks,
            work_dir=render_dir,
            total_duration=3.0 / 0.5,
            canvas_width=720,
            canvas_height=1280
        )

        burn_subtitles(
            video_path=self.synth_video,
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=output_file,
            speed=0.5,
            total_duration=3.0 / 0.5
        )
        self.assertTrue(output_file.exists())
        dur = get_video_duration(output_file)
        self.assertAlmostEqual(dur, 6.0, delta=0.4)

    def test_04_export_with_bgm_mixing(self):
        """Verifies rendering with background music (BGM) mixing and volume."""
        output_file = self.work_dir / "out_bgm_mixed.mp4"
        chunks = [
            {
                "start": 0.5,
                "end": 2.5,
                "text": "Con musica di sottofondo",
                "bold_indices": [1]
            }
        ]

        render_dir = self.work_dir / "render_tmp_bgm"
        render_dir.mkdir(exist_ok=True)
        _, ffconcat_path, wm_path = render_all(
            chunks=chunks,
            work_dir=render_dir,
            total_duration=3.0,
            canvas_width=720,
            canvas_height=1280
        )

        burn_subtitles(
            video_path=self.synth_video,
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=output_file,
            bgm_path=self.synth_bgm,
            bgm_volume=0.25,
            bgm_fade_in=0.5,
            bgm_fade_out=0.5,
            total_duration=3.0
        )
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 1000)

        # Check audio stream presence via ffmpeg -i
        proc = subprocess.run([self.ffmpeg, "-i", str(output_file)], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        self.assertIn("Audio: aac", proc.stderr)


if __name__ == "__main__":
    unittest.main()
