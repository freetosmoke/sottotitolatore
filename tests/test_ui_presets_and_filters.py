"""
Unit tests for Phase C: UI/UX features, 5 Complete Presets, Video Filter Rendering, and Font Categorization.
"""

import json
import os
import shutil
import tempfile
import unittest
import numpy as np

import font_manager
import video_renderer
import web_app


class TestUiPresetsAndFilters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_presets_structure(self):
        """Verify the 5 complete presets exist and have all required fields."""
        expected_ids = ["preset_clean", "preset_social", "preset_bold", "preset_minimal", "preset_creator"]
        for pid in expected_ids:
            self.assertIn(pid, web_app.SYSTEM_PRESET_IDS, f"Missing system preset {pid}")
            preset = next((p for p in web_app.DEFAULT_PRESETS if p["id"] == pid), None)
            self.assertIsNotNone(preset, f"Preset {pid} not found in DEFAULT_PRESETS")
            
            # Check typography & style
            self.assertIn("subtitle_style", preset)
            self.assertIn("normal", preset["subtitle_style"])
            self.assertIn("keyword", preset["subtitle_style"])
            self.assertIn("color", preset["subtitle_style"]["normal"])
            self.assertIn("color", preset["subtitle_style"]["keyword"])
            
            # Check layout
            self.assertIn("subtitle_layout", preset)
            self.assertIn("num_lines", preset["subtitle_layout"])
            self.assertIn("min_words_per_line", preset["subtitle_layout"])
            self.assertIn("max_words_per_line", preset["subtitle_layout"])
            
            # Check Phase B & C features
            self.assertIn("word_animation", preset)
            self.assertIn("capitalization_mode", preset)
            self.assertIn("stroke_width", preset)
            self.assertIn("shadow_offset", preset)
            self.assertIn("video_filter", preset)

    def test_normalize_preset(self):
        """Verify normalize_preset preserves and defaults new fields."""
        raw = {
            "name": "Custom Test",
            "font_name": "Montserrat",
            "word_animation": "pop",
            "capitalization_mode": "uppercase",
            "video_filter": "vibrant"
        }
        normalized = web_app.normalize_preset(raw)
        self.assertEqual(normalized["word_animation"], "pop")
        self.assertEqual(normalized["capitalization_mode"], "uppercase")
        self.assertEqual(normalized["video_filter"], "vibrant")
        self.assertEqual(normalized["stroke_width"], 0.0)
        self.assertEqual(normalized["shadow_offset"], 0.0)

    def test_font_catalog_categories(self):
        """Verify all fonts in FONT_CATALOG have valid style_category."""
        valid_categories = {"Minimal", "Bold", "Creator", "Elegant", "Corporate", "Custom"}
        self.assertGreater(len(font_manager.FONT_CATALOG), 25)
        for font in font_manager.FONT_CATALOG:
            cat = font.get("style_category")
            self.assertIsNotNone(cat, f"Font {font.get('family')} missing style_category")
            self.assertIn(cat, valid_categories, f"Invalid category {cat} for {font.get('family')}")

    def test_video_filter_ffmpeg_filters(self):
        """Verify filter string mappings in video_renderer."""
        # Test synthetic video generation and burn_subtitles with video_filter
        input_mp4 = os.path.join(self.temp_dir, "synth_filter.mp4")
        out_bw_cinema = os.path.join(self.temp_dir, "out_bw_cinema.mp4")
        out_vibrant = os.path.join(self.temp_dir, "out_vibrant.mp4")

        # Generate a small 1-second video with sound using ffmpeg
        ffmpeg_bin = video_renderer._get_bin("ffmpeg")
        cmd = (
            f'"{ffmpeg_bin}" -y -f lavfi -i testsrc=duration=1:size=320x240:rate=25 '
            f'-f lavfi -i sine=frequency=440:duration=1 -c:v libx264 -c:a aac -pix_fmt yuv420p "{input_mp4}"'
        )
        self.assertEqual(os.system(cmd), 0)

        from pathlib import Path
        from subtitle_renderer import render_all

        chunks = [{"start": 0.1, "end": 0.9, "text": "Test video filter", "words": [{"word": "Test", "start": 0.1, "end": 0.4}, {"word": "filter", "start": 0.5, "end": 0.9}]}]
        render_dir = Path(self.temp_dir) / "sub_frames"
        render_dir.mkdir(exist_ok=True)
        _, ffconcat_path, wm_path = render_all(
            chunks=chunks,
            work_dir=render_dir,
            total_duration=1.0,
            canvas_width=320,
            canvas_height=240
        )

        # 1. Test B&W Cinema filter
        res1 = video_renderer.burn_subtitles(
            video_path=Path(input_mp4),
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=Path(out_bw_cinema),
            video_filter="bw_cinema"
        )
        self.assertTrue(Path(out_bw_cinema).exists())
        self.assertGreater(Path(out_bw_cinema).stat().st_size, 1000)

        # 2. Test Vibrant Pop filter
        res2 = video_renderer.burn_subtitles(
            video_path=Path(input_mp4),
            ffconcat_path=ffconcat_path,
            watermark_path=wm_path,
            output_path=Path(out_vibrant),
            video_filter="vibrant"
        )
        self.assertTrue(Path(out_vibrant).exists())
        self.assertGreater(Path(out_vibrant).stat().st_size, 1000)

    def test_index_html_phase_c_elements(self):
        """Verify HTML markup contains all required Phase C elements."""
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_static", "index.html")
        self.assertTrue(os.path.exists(html_path))
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # RGB Color Picker Modal and trigger buttons
        self.assertIn('id="modal-color-picker"', content)
        self.assertIn('id="slider-rgb-r"', content)
        self.assertIn('id="color-picker-favorites-container"', content)
        self.assertIn('btn-open-color-picker', content)

        # Video Filter Cards
        self.assertIn('id="video-filter-cards"', content)
        self.assertIn('data-filter="bw_cinema"', content)
        self.assertIn('data-filter="vibrant"', content)

        # Font Browser Modal
        self.assertIn('id="modal-font-browser"', content)
        self.assertIn('id="font-browser-search"', content)
        self.assertIn('id="font-browser-grid"', content)
        self.assertIn('id="btn-open-font-browser"', content)

        # Shortcuts Modal & Timeline buttons
        self.assertIn('id="modal-shortcuts-cheatsheet"', content)
        self.assertIn('id="btn-open-shortcuts"', content)
        self.assertIn('id="btn-tl-undo"', content)
        self.assertIn('id="btn-tl-redo"', content)
        self.assertIn('id="btn-tl-shortcuts"', content)


if __name__ == "__main__":
    unittest.main()
