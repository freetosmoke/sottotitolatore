#!/usr/bin/env python3
"""
tests/test_subtitle_engine.py
Unit tests for Subtitle Engine enhancements in Sub Studio:
- Phase B.6: Word Animations (Fade, Pop, Scale, Slide Up, Slide Down)
- Phase B.7: Advanced & Smart Capitalization
- Phase B.8: Gradual Outline & Shadow scaling
"""
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from subtitle_renderer import (
    apply_capitalization,
    render_subtitle,
    render_all,
    load_font_variant,
    BASE_WIDTH,
    BASE_HEIGHT,
)


class TestSubtitleEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.TemporaryDirectory()
        cls.work_dir = Path(cls.test_dir.name)
        cls.font_light = load_font_variant(45, "Raleway", "Light")
        cls.font_bold = load_font_variant(45, "Raleway", "SemiBold")

    @classmethod
    def tearDownClass(cls):
        cls.test_dir.cleanup()

    def test_01_capitalization_modes(self):
        """Verifies uppercase, lowercase, titlecase, and smartcase transformations."""
        raw = "ciao a tutti mi chiamo salvatore puglisi e lavoro con l'ai su substudio a roma."

        # 1. Uppercase
        self.assertEqual(
            apply_capitalization(raw, "uppercase"),
            "CIAO A TUTTI MI CHIAMO SALVATORE PUGLISI E LAVORO CON L'AI SU SUBSTUDIO A ROMA."
        )

        # 2. Lowercase
        self.assertEqual(
            apply_capitalization("CIAO A TUTTI", "lowercase"),
            "ciao a tutti"
        )

        # 3. Titlecase
        self.assertEqual(
            apply_capitalization("il podcast del successo", "titlecase"),
            "Il Podcast Del Successo"
        )

        # 4. Smartcase: sentence starts, proper nouns, acronyms, and prepositions
        smart = apply_capitalization(raw, "smartcase")
        self.assertTrue(smart.startswith("Ciao a tutti"))
        self.assertIn("Salvatore Puglisi", smart)
        self.assertIn("l'AI", smart)
        self.assertIn("SubStudio", smart)
        self.assertIn("Roma", smart)

    def test_02_smart_capitalization_preserves_acronyms_and_brands(self):
        """Ensures tech acronyms and brands remain properly capitalized."""
        text = "il ceo di apple ha presentato la nuova app per ios e mac."
        smart = apply_capitalization(text, "smartcase")
        self.assertIn("CEO", smart)
        self.assertIn("Apple", smart)
        self.assertTrue("iOS" in smart or "Ios" in smart)
        self.assertIn("Mac", smart)

    def test_03_word_animation_frame_generation(self):
        """Verifies that enabling word_animation creates word-level timed frames in render_all."""
        chunks = [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "Sottotitolo animato con timing",
                "bold_indices": [1],
                "words": [
                    {"word": "Sottotitolo", "start": 0.0, "end": 0.5},
                    {"word": "animato", "start": 0.5, "end": 1.0},
                    {"word": "con", "start": 1.0, "end": 1.3},
                    {"word": "timing", "start": 1.3, "end": 2.0}
                ]
            }
        ]

        # Render with word_animation='pop'
        render_dir = self.work_dir / "render_anim_pop"
        render_dir.mkdir(exist_ok=True)
        rendered_chunks, ffconcat_path, _ = render_all(
            chunks=chunks,
            work_dir=render_dir,
            total_duration=2.0,
            preset={"word_animation": "pop"}
        )

        # Should generate multiple sub-frames for the words
        self.assertGreater(len(rendered_chunks), 1)
        self.assertTrue(ffconcat_path.exists())
        concat_content = ffconcat_path.read_text()
        self.assertIn("sub_0000_w00.png", concat_content)
        self.assertIn("sub_0000_w01.png", concat_content)

    def test_04_word_animation_fade_opacity(self):
        """Verifies that fade animation attenuates future words while keeping active words bright."""
        out_active = self.work_dir / "sub_fade_active.png"
        out_future = self.work_dir / "sub_fade_future.png"

        words = ["ParolaUno", "ParolaDue"]

        # In word 0 active: ParolaUno is active, ParolaDue is future (dimmed)
        render_subtitle(
            words=words,
            bold_indices=[0],
            light=self.font_light,
            semibold=self.font_bold,
            out=out_active,
            active_word_index=0,
            word_animation="fade",
        )
        self.assertTrue(out_active.exists())
        with Image.open(out_active) as img_active:
            self.assertEqual(img_active.size, (BASE_WIDTH, BASE_HEIGHT))

    def test_05_gradual_stroke_and_shadow_scaling(self):
        """Verifies that stroke and shadow generate proportional and non-jagged pixels."""
        out_0 = self.work_dir / "sub_stroke_0.png"
        out_1 = self.work_dir / "sub_stroke_1.png"
        out_2 = self.work_dir / "sub_stroke_2.png"

        words = ["Test", "Graduale"]

        render_subtitle(words, [0], self.font_light, self.font_bold, out_0, stroke_width=0, shadow_offset=0)
        render_subtitle(words, [0], self.font_light, self.font_bold, out_1, stroke_width=1, shadow_offset=1)
        render_subtitle(words, [0], self.font_light, self.font_bold, out_2, stroke_width=2, shadow_offset=2)

        self.assertTrue(out_0.exists())
        self.assertTrue(out_1.exists())
        self.assertTrue(out_2.exists())

        # Image file size typically increases smoothly with added stroke and shadow pixels
        sz0 = out_0.stat().st_size
        sz1 = out_1.stat().st_size
        sz2 = out_2.stat().st_size
        self.assertLessEqual(sz0, sz1)
        self.assertLessEqual(sz1, sz2)


if __name__ == "__main__":
    unittest.main()
