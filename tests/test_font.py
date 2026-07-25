from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TTF = ROOT / "dist" / "SunGallant-Regular.ttf"
WOFF2 = ROOT / "dist" / "SunGallant-Regular.woff2"
GLYPH_SOURCE = ROOT / "sources" / "glyphs.txt"


def source_rows(codepoint: str) -> list[str]:
    block = GLYPH_SOURCE.read_text(encoding="utf-8").split(f"U+{codepoint} ", 1)[1]
    return block.split("\n\n", 1)[0].splitlines()[1:]


class FontTests(unittest.TestCase):
    def test_expected_outputs_exist(self) -> None:
        self.assertTrue(TTF.is_file())
        self.assertTrue(WOFF2.is_file())

    def test_vendored_source_is_pinned(self) -> None:
        source = ROOT / "sources" / "netbsd-gallant12x22.h"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(digest, "8fd73eda8a698c9157f7e56da461c9cb0e74db3554fc58562dff28c322ccbb46")

    def test_font_is_outline_only(self) -> None:
        font = TTFont(TTF)
        self.assertIn("glyf", font)
        for bitmap_table in ("EBDT", "EBLC", "EBSC", "CBDT", "CBLC", "sbix"):
            self.assertNotIn(bitmap_table, font)

    def test_metrics_preserve_the_12_by_22_grid(self) -> None:
        font = TTFont(TTF)
        self.assertEqual(font["head"].unitsPerEm, 1408)
        self.assertEqual(font["hhea"].ascent, 1088)
        self.assertEqual(font["hhea"].descent, -320)
        self.assertEqual({advance for advance, _ in font["hmtx"].metrics.values()}, {768})
        self.assertEqual(font["post"].isFixedPitch, 1)

    def test_version_metadata(self) -> None:
        font = TTFont(TTF)
        version = font["name"].getName(5, 3, 1)
        self.assertIsNotNone(version)
        self.assertEqual(version.toUnicode(), "Version 0.1.1")
        self.assertAlmostEqual(font["head"].fontRevision, 0.101, places=3)

    def test_character_coverage(self) -> None:
        font = TTFont(TTF)
        cmap = font.getBestCmap()
        expected = {
            *range(0x20, 0x7F),
            *range(0xA0, 0x100),
            0x2044,
            0x2070,
            *range(0x2074, 0x207A),
            *range(0x2080, 0x208A),
            *range(0x2150, 0x2160),
            0x2189,
        }
        self.assertEqual(set(cmap), expected)

    def test_extended_numbers_remain_monospaced(self) -> None:
        font = TTFont(TTF)
        cmap = font.getBestCmap()
        codepoints = {
            0x2044,
            0x2070,
            *range(0x2074, 0x207A),
            *range(0x2080, 0x208A),
            *range(0x2150, 0x2160),
            0x2189,
        }
        for codepoint in codepoints:
            with self.subTest(codepoint=f"U+{codepoint:04X}"):
                name = cmap[codepoint]
                glyph = font["glyf"][name]
                self.assertGreater(glyph.numberOfContours, 0)
                self.assertGreaterEqual(glyph.xMin, 0)
                self.assertLessEqual(glyph.xMax, 12 * 64)
                self.assertEqual(font["hmtx"][name][0], 12 * 64)

    def test_visible_glyphs_have_real_contours(self) -> None:
        font = TTFont(TTF)
        glyphs = font["glyf"]
        self.assertGreater(glyphs["A"].numberOfContours, 0)
        self.assertEqual(glyphs["space"].numberOfContours, 0)

    def test_narrow_glyphs_are_optically_balanced(self) -> None:
        font = TTFont(TTF)
        glyphs = font["glyf"]
        for name in ("I", "i", "l", "f"):
            with self.subTest(glyph=name):
                width = glyphs[name].xMax - glyphs[name].xMin
                self.assertGreaterEqual(width, 8 * 64)
                self.assertEqual(font["hmtx"][name][0], 12 * 64)
        self.assertNotIn("kern", font)
        self.assertNotIn("GPOS", font)

    def test_lowercase_serifs_remain_distinct_from_capital_i(self) -> None:
        capital_i = source_rows("0049")
        lowercase_i = source_rows("0069")
        lowercase_l = source_rows("006C")
        self.assertEqual(capital_i[3], "..########..")
        self.assertEqual(lowercase_i[7], "...####.....")
        self.assertEqual(lowercase_l[2], "...####.....")
        self.assertEqual(lowercase_i[16], "..########..")
        self.assertEqual(lowercase_l[16], "..########..")

    def test_optical_capital_serifs_do_not_touch_adjacent_capitals(self) -> None:
        capitals = {
            chr(codepoint): source_rows(f"{codepoint:04X}")
            for codepoint in range(ord("A"), ord("Z") + 1)
        }
        for left_name, left_rows in capitals.items():
            for right_name, right_rows in capitals.items():
                touching_rows = [
                    row
                    for row in range(22)
                    if left_rows[row][-1] == "#" and right_rows[row][0] == "#"
                ]
                with self.subTest(pair=left_name + right_name):
                    self.assertEqual(touching_rows, [])

    def test_structural_capital_edges_are_preserved(self) -> None:
        capital_g = source_rows("0047")
        capital_q = source_rows("0051")
        self.assertEqual(capital_g[11], ".##....#####")
        self.assertEqual(capital_q[18], "..#...###..#")

    def test_woff2_decodes_as_the_same_font(self) -> None:
        ttf = TTFont(TTF)
        woff2 = TTFont(WOFF2)
        self.assertEqual(woff2.flavor, "woff2")
        self.assertEqual(woff2.getBestCmap(), ttf.getBestCmap())
        self.assertEqual(woff2.getGlyphOrder(), ttf.getGlyphOrder())

    def test_build_is_reproducible(self) -> None:
        original_ttf = TTF.read_bytes()
        original_woff2 = WOFF2.read_bytes()
        subprocess.run([sys.executable, ROOT / "scripts" / "build_font.py"], check=True)
        self.assertEqual(TTF.read_bytes(), original_ttf)
        self.assertEqual(WOFF2.read_bytes(), original_woff2)

    def test_user_install_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = {**os.environ, "SUN_GALLANT_FONT_DIR": directory}
            command = [sys.executable, ROOT / "scripts" / "install_font.py"]
            subprocess.run(command, check=True, env=environment)
            installed = Path(directory) / TTF.name
            self.assertEqual(installed.read_bytes(), TTF.read_bytes())
            subprocess.run([*command, "--remove"], check=True, env=environment)
            self.assertFalse(installed.exists())


if __name__ == "__main__":
    unittest.main()
