#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "glyphs.txt"
OUTPUT = ROOT / "sources" / "vector_paths.json"
WIDTH = 12
HEIGHT = 22

# A purpose-built geometric monospace drawing, expressed as editable
# centerlines on Gallant's 12 by 22 coordinate system. Curves are deliberate
# B\u00e9ziers rather than softened bitmap corners. The baseline sits at y=16,
# capitals rise to y=3, the x-height line is y=7, and descenders reach y=20.
#
# A value is either a single SVG path string stroked at the default width, or
# a list of (path, stroke-width multiplier) pairs for glyphs that mix weights.
MODERN_PATHS = {
    0: "M2 3 H10 V16 H2 Z",
    ord("!"): "M6 3 V12 M6 15 V16",
    ord('"'): "M4 3 V7 M8 3 V7",
    ord("#"): "M4 3 L3 16 M9 3 L8 16 M2 8 H10 M2 12 H10",
    ord("$"): "M9.5 5 C8.7 3.7 7.5 3 5.7 3 C3.5 3 2.2 4.2 2.2 6 C2.2 8 3.5 9 6 9.5 C8.7 10 10 11 10 13 C10 15 8.4 16 6 16 C4 16 2.7 15.4 1.8 14 M6 1.5 V17.5",
    ord("%"): "M2 16 L10 3 M3.2 3 C1.7 3 1.4 5.7 3.2 5.7 C5 5.7 4.7 3 3.2 3 M8.8 13.3 C7.3 13.3 7 16 8.8 16 C10.6 16 10.3 13.3 8.8 13.3",
    ord("&"): "M10 16 L4.2 9.3 C2.8 7.8 2 6.8 2 5.5 C2 3.8 3.3 3 5.2 3 C7.2 3 8.4 4 8.4 5.7 C8.4 7.2 7.3 8.4 4.7 10 C2.7 11.2 2 12.2 2 13.5 C2 15.2 3.3 16 5.3 16 C7.7 16 9.1 14.2 10 12",
    ord("'"): "M6 3 V7",
    ord("("): "M8 2 C5.5 5 4.5 8.2 4.5 11 C4.5 14 5.5 17 8 20",
    ord(")"): "M4 2 C6.5 5 7.5 8.2 7.5 11 C7.5 14 6.5 17 4 20",
    ord("*"): "M6 4 V10 M3.4 5.5 L8.6 8.5 M8.6 5.5 L3.4 8.5",
    ord("+"): "M6 6 V14 M2 10 H10",
    ord(","): "M6.5 15 L5.3 18",
    ord("-"): "M3 11 H9",
    ord("."): "M6 15 V16",
    ord("/"): "M2 18 L10 1",
    ord(":"): "M6 8 V9 M6 15 V16",
    ord(";"): "M6 8 V9 M6.5 15 L5.3 18",
    ord("<"): "M9 6 L3 11 L9 16",
    ord("="): "M2 8 H10 M2 13 H10",
    ord(">"): "M3 6 L9 11 L3 16",
    ord("?"): "M2.5 5 C3.3 3.7 4.5 3 6.2 3 C8.6 3 10 4.2 10 6 C10 7.8 9 8.7 7.4 9.7 C6.4 10.3 6 11 6 12 M6 15 V16",
    ord("@"): "M9 15.3 C8 15.8 7 16 5.7 16 C3 16 1.8 14.1 1.8 10.2 C1.8 6 3.4 3.7 6.4 3.7 C9.1 3.7 10.3 5.5 10.3 8.5 V13 H8 V11.5 C7.5 12.7 6.6 13.2 5.6 13.2 C4 13.2 3.2 12 3.2 10 C3.2 7.7 4.3 6.5 5.9 6.5 C7.3 6.5 8 7.4 8 9 V11.5 C8 12.7 8.8 13.2 10.3 13",
    ord("["): "M8 2 H4 V20 H8",
    ord("\\"): "M2 1 L10 18",
    ord("]"): "M4 2 H8 V20 H4",
    ord("^"): "M3 8 L6 3 L9 8",
    ord("_"): "M2 19 H10",
    ord("`"): "M5 2 L7 4",
    ord("{"): "M8 2 H7 C5.5 2 5 3 5 4.5 V8.5 C5 10 4.3 11 3 11 C4.3 11 5 12 5 13.5 V17.5 C5 19 5.5 20 7 20 H8",
    ord("|"): "M6 1 V20",
    ord("}"): "M4 2 H5 C6.5 2 7 3 7 4.5 V8.5 C7 10 7.7 11 9 11 C7.7 11 7 12 7 13.5 V17.5 C7 19 6.5 20 5 20 H4",
    ord("~"): "M2 11 C3 9.5 4.2 9.3 5.5 10.3 C7 11.5 8.2 11.3 10 9.5",
    ord("0"): "M6 3 C3.9 3 2.9 5 2.9 9.5 C2.9 14 3.9 16 6 16 C8.1 16 9.1 14 9.1 9.5 C9.1 5 8.1 3 6 3",
    ord("1"): "M3.5 6 L6 3 V16 M3 16 H9",
    ord("2"): "M2.2 5 C3.2 3.6 4.4 3 6.2 3 C8.6 3 10 4.3 10 6.2 C10 8 9.1 9.2 7.2 10.6 L2 16 H10",
    ord("3"): "M2.4 4.5 C3.4 3.5 4.6 3 6.2 3 C8.5 3 9.8 4.1 9.8 6 C9.8 8.1 8.4 9.3 6 9.3 H4.8 M6 9.3 C8.7 9.3 10 10.5 10 12.7 C10 14.8 8.5 16 6.1 16 C4.3 16 3 15.4 2 14.2",
    ord("4"): "M8 16 V3 L2 12 H10",
    ord("5"): "M9.5 3 H3 L2.5 9 H6.2 C8.7 9 10 10.2 10 12.5 C10 14.8 8.5 16 6 16 C4.2 16 2.8 15.4 2 14.3",
    ord("6"): "M9.5 4 C8.7 3.3 7.6 3 6.3 3 C3.4 3 2 5.2 2 9.7 V12.3 C2 14.7 3.5 16 6 16 C8.5 16 10 14.6 10 12.3 C10 10 8.6 8.7 6.1 8.7 C4 8.7 2.7 9.7 2.4 10.3",
    ord("7"): "M2 3 H10 L4.5 16",
    ord("8"): "M6 3 C3.5 3 2.3 4.1 2.3 6.2 C2.3 8.2 3.7 9.3 6 9.3 C8.3 9.3 9.7 8.2 9.7 6.2 C9.7 4.1 8.5 3 6 3 M6 9.3 C3.3 9.3 2 10.5 2 12.7 C2 14.9 3.4 16 6 16 C8.6 16 10 14.9 10 12.7 C10 10.5 8.7 9.3 6 9.3",
    ord("9"): "M2.5 15 C3.3 15.7 4.4 16 5.7 16 C8.6 16 10 13.8 10 9.3 V6.7 C10 4.3 8.5 3 6 3 C3.5 3 2 4.4 2 6.7 C2 9 3.4 10.3 5.9 10.3 C8 10.3 9.3 9.3 9.6 8.7",
    ord("A"): "M1.8 16 L5.4 3 H6.6 L10.2 16 M3.2 11 H8.8",
    ord("B"): "M2 16 V3 H6 C8.7 3 10 4.1 10 6.2 C10 8.2 8.7 9.4 6 9.4 H2 M6 9.4 C8.8 9.4 10.2 10.6 10.2 12.7 C10.2 14.9 8.8 16 6 16 H2",
    ord("C"): "M10 5 C9 3.6 7.7 3 6 3 C3.2 3 2 5.1 2 9.5 C2 13.9 3.2 16 6 16 C7.7 16 9 15.4 10 14",
    ord("D"): "M2 16 V3 H5.6 C8.7 3 10 5.1 10 9.5 C10 13.9 8.7 16 5.6 16 H2",
    ord("E"): "M10 3 H2 V16 H10 M2 9.3 H8.5",
    ord("F"): "M10 3 H2 V16 M2 9.3 H8.5",
    ord("G"): "M10 5 C9 3.6 7.7 3 6 3 C3.2 3 2 5.1 2 9.5 C2 13.9 3.2 16 6 16 C7.7 16 9 15.4 10 14 V10 H6.7",
    ord("H"): "M2 3 V16 M10 3 V16 M2 9.5 H10",
    ord("I"): "M3 3 H9 M6 3 V16 M3 16 H9",
    ord("J"): "M3 3 H10 V12.3 C10 14.8 8.6 16 6.2 16 C4.1 16 2.8 15.1 2 13.5",
    ord("K"): "M2 3 V16 M10 3 L2.6 10.4 M5.6 9 L10 16",
    ord("L"): "M2 3 V16 H10",
    ord("M"): "M1.5 16 V3 L6 10.2 L10.5 3 V16",
    ord("N"): "M2 16 V3 H3 L9 16 H10 V3",
    ord("O"): "M6 3 C3.2 3 2 5.1 2 9.5 C2 13.9 3.2 16 6 16 C8.8 16 10 13.9 10 9.5 C10 5.1 8.8 3 6 3",
    ord("P"): "M2 16 V3 H6 C8.7 3 10 4.3 10 6.7 C10 9 8.7 10.2 6 10.2 H2",
    ord("Q"): "M6 3 C3.2 3 2 5.1 2 9.5 C2 13.9 3.2 16 6 16 C8.8 16 10 13.9 10 9.5 C10 5.1 8.8 3 6 3 M5.6 16.1 C4.3 16.4 3.2 17 2.8 17.8 C2.55 18.35 3 18.5 3.7 18.15 C4.7 17.65 5.7 17.75 6.7 18.5 C7.9 19.4 9.3 19.2 10.4 18",
    ord("R"): "M2 16 V3 H6 C8.7 3 10 4.3 10 6.7 C10 9 8.7 10.2 6 10.2 H2 M6.7 10.9 L10.2 16",
    ord("S"): "M9.7 4.7 C8.8 3.6 7.6 3 5.8 3 C3.4 3 2.1 4.2 2.1 6 C2.1 8.1 3.5 9.1 6.1 9.6 C8.8 10.1 10 11.1 10 13 C10 15 8.4 16 6 16 C4 16 2.7 15.4 1.8 14",
    ord("T"): "M1.5 3 H10.5 M6 3 V16",
    ord("U"): "M2 3 V12 C2 14.7 3.4 16 6 16 C8.6 16 10 14.7 10 12 V3",
    ord("V"): "M1.8 3 L5.4 16 H6.6 L10.2 3",
    ord("W"): "M1.2 3 L3.2 16 H4.3 L6 8.5 L7.7 16 H8.8 L10.8 3",
    ord("X"): "M2 3 L10 16 M10 3 L2 16",
    ord("Y"): "M1.8 3 L6 9.8 L10.2 3 M6 9.8 V16",
    ord("Z"): "M2 3 H10 L2 16 H10",
    ord("a"): "M9.5 16 V10 C9.5 8 8.2 7 6 7 C4.2 7 3 7.6 2.2 8.7 M9.5 11 H5 C3 11 2 12 2 13.5 C2 15.1 3.2 16 5.1 16 C7.3 16 8.8 14.8 9.2 13.8",
    ord("b"): "M2 3 V16 M2.3 9.2 C2.7 8 4 7 6 7 C8.6 7 10 8.6 10 11.5 C10 14.4 8.6 16 6 16 C4 16 2.7 15 2.3 13.8",
    ord("c"): "M9.5 8.5 C8.7 7.5 7.6 7 6 7 C3.3 7 2 8.7 2 11.5 C2 14.3 3.3 16 6 16 C7.6 16 8.7 15.5 9.5 14.5",
    ord("d"): "M10 3 V16 M9.7 9.2 C9.3 8 8 7 6 7 C3.4 7 2 8.6 2 11.5 C2 14.4 3.4 16 6 16 C8 16 9.3 15 9.7 13.8",
    ord("e"): "M2 11.5 H10 C10 8.6 8.5 7 6 7 C3.3 7 2 8.7 2 11.5 C2 14.3 3.4 16 6.2 16 C7.8 16 9 15.5 9.8 14.5",
    ord("f"): "M3.5 7 H9 M5 16 V6 C5 4 6.1 3 8 3 C8.7 3 9.3 3.1 10 3.5",
    ord("g"): [
        ("M5.6 6.9 C3.5 6.9 2.4 7.9 2.4 9.5 C2.4 11.1 3.5 12.1 5.6 12.1 C7.7 12.1 8.8 11.1 8.8 9.5 C8.8 7.9 7.7 6.9 5.6 6.9", 1.0),
        ("M8.6 7.3 C9.3 7.2 9.9 6.9 10.4 6.4", 0.8),
        ("M4.6 12.15 C3 12.4 2.2 13.3 2.2 14.4 C2.2 15.1 3 15.6 4.5 15.85", 1.0),
        ("M6 15.9 C8.4 15.9 10.3 16.8 10.3 18 C10.3 19.2 8.4 20.1 6 20.1 C3.6 20.1 1.7 19.2 1.7 18 C1.7 16.8 3.6 15.9 6 15.9", 1.0),
    ],
    ord("h"): "M2 3 V16 M2.3 9.2 C2.8 8 4.2 7 6.2 7 C8.7 7 10 8.3 10 10.8 V16",
    ord("i"): "M6 7 V16 M6 3 V4",
    ord("j"): "M7 7 V17 C7 19 6 20 4.2 20 C3.4 20 2.7 19.8 2 19.4 M7 3 V4",
    ord("k"): "M2 3 V16 M9.5 7 L2.6 12.5 M5.8 11 L10 16",
    ord("l"): "M4 3 H6 V13.5 C6 15.2 6.8 16 8.5 16 H10",
    ord("m"): "M1.4 16 V7 M1.7 8.8 C2 7.8 3 7 4.2 7 C5.4 7 6 8 6 9.7 V16 M6.3 8.8 C6.6 7.8 7.6 7 8.8 7 C10 7 10.6 8 10.6 9.7 V16",
    ord("n"): "M2 16 V7 M2.3 9.2 C2.8 8 4.2 7 6.2 7 C8.7 7 10 8.3 10 10.8 V16",
    ord("o"): "M6 7 C3.3 7 2 8.7 2 11.5 C2 14.3 3.3 16 6 16 C8.7 16 10 14.3 10 11.5 C10 8.7 8.7 7 6 7",
    ord("p"): "M2 20 V7 M2.3 9.2 C2.7 8 4 7 6 7 C8.6 7 10 8.6 10 11.5 C10 14.4 8.6 16 6 16 C4 16 2.7 15 2.3 13.8",
    ord("q"): "M10 20 V7 M9.7 9.2 C9.3 8 8 7 6 7 C3.4 7 2 8.6 2 11.5 C2 14.4 3.4 16 6 16 C8 16 9.3 15 9.7 13.8",
    ord("r"): "M2 16 V7 M2.3 9.2 C2.8 8 4.1 7 6 7 C7.4 7 8.5 7.4 9.3 8.3",
    ord("s"): "M9.4 8.3 C8.6 7.4 7.4 7 5.8 7 C3.6 7 2.4 7.9 2.4 9.2 C2.4 10.7 3.6 11.2 6.1 11.7 C8.7 12.2 9.8 12.8 9.8 14.1 C9.8 15.4 8.5 16 6.2 16 C4.4 16 3.1 15.6 2.2 14.7",
    ord("t"): "M3 7 H10 M6 3 V13.5 C6 15.2 6.8 16 8.5 16 H10",
    ord("u"): "M2 7 V12.2 C2 14.7 3.3 16 5.8 16 C7.8 16 9.2 15 9.7 13.8 M10 16 V7",
    ord("v"): "M2 7 L5.5 16 H6.5 L10 7",
    ord("w"): "M1.2 7 L3.2 16 H4.2 L6 10 L7.8 16 H8.8 L10.8 7",
    ord("x"): "M2.3 7 L9.7 16 M9.7 7 L2.3 16",
    ord("y"): "M2 7 L5.5 16 H6.3 M10 7 L6.15 16.9 C5.5 18.6 4.1 20 2 20",
    ord("z"): "M2 7 H10 L2 16 H10",
    # Latin-1 punctuation and symbols, drawn in the same geometric system.
    0xA1: "M6 16 V7 M6 3 V4",
    0xA2: "M9.4 8.6 C8.6 7.6 7.6 7.1 6.1 7.1 C3.5 7.1 2.2 8.6 2.2 11.5 C2.2 14.4 3.5 15.9 6.1 15.9 C7.6 15.9 8.6 15.4 9.4 14.4 M6 4.8 V7.1 M6 15.9 V18.2",
    0xA3: "M9.2 4.4 C8.5 3.5 7.5 3 6.3 3 C4.6 3 3.6 4.2 3.6 6.1 V13.2 C3.6 14.6 3.1 15.5 2.2 16 H10 M2.2 9.5 H7.4",
    0xA4: "M6 6.9 C4.1 6.9 2.9 8.1 2.9 10 C2.9 11.9 4.1 13.1 6 13.1 C7.9 13.1 9.1 11.9 9.1 10 C9.1 8.1 7.9 6.9 6 6.9 M3.8 7.8 L2 6 M8.2 7.8 L10 6 M3.8 12.2 L2 14 M8.2 12.2 L10 14",
    0xA5: "M1.8 3 L6 9.5 L10.2 3 M6 9.5 V16 M2.8 10.7 H9.2 M2.8 13.2 H9.2",
    0xA6: "M6 1.5 V9 M6 12.5 V20",
    0xA7: "M9.1 4.4 C8.4 3.5 7.4 3 6.1 3 C4.3 3 3.2 3.9 3.2 5.2 C3.2 6.6 4.3 7.2 6.3 7.7 C8.4 8.2 9.4 9 9.4 10.4 C9.4 11.7 8.4 12.6 6.9 12.8 M2.9 14.6 C3.6 15.5 4.6 16 5.9 16 C7.7 16 8.8 15.1 8.8 13.8 C8.8 12.4 7.7 11.8 5.7 11.3 C3.6 10.8 2.6 10 2.6 8.6 C2.6 7.3 3.6 6.4 5.1 6.2",
    0xA8: "M4.1 4.9 V5.2 M7.9 4.9 V5.2",
    0xA9: [
        ("M6 4.8 C8.6 4.8 10.7 6.9 10.7 9.5 C10.7 12.1 8.6 14.2 6 14.2 C3.4 14.2 1.3 12.1 1.3 9.5 C1.3 6.9 3.4 4.8 6 4.8", 1.0),
        ("M7.8 7.9 C7.3 7.4 6.7 7.2 6 7.2 C4.7 7.2 3.9 8.1 3.9 9.5 C3.9 10.9 4.7 11.8 6 11.8 C6.7 11.8 7.3 11.6 7.8 11.1", 0.75),
    ],
    0xAB: "M5.6 7.2 L2.8 11 L5.6 14.8 M9.4 7.2 L6.6 11 L9.4 14.8",
    0xAC: "M2 9.5 H10 V13",
    0xAD: "M3 11 H9",
    0xAE: [
        ("M6 4.8 C8.6 4.8 10.7 6.9 10.7 9.5 C10.7 12.1 8.6 14.2 6 14.2 C3.4 14.2 1.3 12.1 1.3 9.5 C1.3 6.9 3.4 4.8 6 4.8", 1.0),
        ("M4.7 12 V7 H6.3 C7.5 7 8.1 7.4 8.1 8.4 C8.1 9.3 7.5 9.8 6.3 9.8 H4.7 M6.6 9.8 L8.2 12", 0.75),
    ],
    0xAF: "M3 3.6 H9",
    0xB0: "M6 3 C4.7 3 4 3.8 4 5 C4 6.2 4.7 7 6 7 C7.3 7 8 6.2 8 5 C8 3.8 7.3 3 6 3",
    0xB1: "M6 5.5 V12.5 M2.2 9 H9.8 M2.2 15.5 H9.8",
    0xB4: "M5.2 5.3 L7.2 3.3",
    0xB5: "M2 20 V7 M2 12.2 C2 14.7 3.3 16 5.8 16 C7.8 16 9.2 15 9.7 13.8 M10 7 V16",
    0xB6: "M9.4 3 H5.2 C3.3 3 2.2 4.1 2.2 5.9 C2.2 7.7 3.3 8.8 5.2 8.8 H6.4 M6.4 3 V16 M9.4 3 V16",
    0xB7: "M6 9.5 V10.5",
    0xB8: "M6 16 C6 17.2 7.8 17.2 7.8 18.4 C7.8 19.4 6.8 20 5.2 20",
    0xBB: "M2.6 7.2 L5.4 11 L2.6 14.8 M6.4 7.2 L9.2 11 L6.4 14.8",
    0xBF: "M6 3 V4 M9.5 14 C8.7 15.3 7.5 16 5.8 16 C3.4 16 2 14.8 2 13 C2 11.2 3 10.3 4.6 9.3 C5.6 8.7 6 8 6 7",
    0xC6: "M10.5 3 H5.8 V16 H10.5 M5.8 9.3 H9.8 M5.8 3 L1 16 M2.7 11.5 H5.8",
    0xD0: "M2 16 V3 H5.6 C8.7 3 10 5.1 10 9.5 C10 13.9 8.7 16 5.6 16 H2 M0.9 9.5 H4.3",
    0xD7: "M2.9 6.9 L9.1 13.1 M9.1 6.9 L2.9 13.1",
    0xD8: "M6 3 C3.2 3 2 5.1 2 9.5 C2 13.9 3.2 16 6 16 C8.8 16 10 13.9 10 9.5 C10 5.1 8.8 3 6 3 M2.3 17.3 L9.7 1.7",
    0xDE: "M2 3 V16 M2 5.9 H6 C8.6 5.9 9.9 7.1 9.9 9.4 C9.9 11.7 8.6 12.9 6 12.9 H2",
    0xDF: "M2 16 V6 C2 4.1 3.2 3 5.1 3 C6.9 3 8.1 4 8.1 5.6 C8.1 6.9 7.4 7.7 6.2 8.4 C8.4 9 9.7 10.1 9.7 12 C9.7 14.4 8.3 16 6.1 16",
    0xE6: "M6 11.5 C6 8.7 5.2 7 3.6 7 C2.1 7 1.3 8.7 1.3 11.5 C1.3 14.3 2.1 16 3.6 16 C5.2 16 6 14.3 6 11.5 M6 11.5 H10.7 C10.7 8.7 9.9 7 8.3 7 C6.8 7 6 8.7 6 11.5 C6 14.3 6.8 16 8.3 16 C9.4 16 10.1 15.5 10.6 14.6",
    0xF0: "M6 9.4 C8.3 9.4 9.6 10.7 9.6 12.7 C9.6 14.9 8.2 16 6 16 C3.8 16 2.4 14.9 2.4 12.7 C2.4 10.7 3.8 9.4 6 9.4 M9.6 12.7 C9.6 8.6 8 5.5 4.9 3.6 M4.3 6.4 L8.5 3.8",
    0xF7: "M2 10 H10 M6 5.8 V6.8 M6 13.2 V14.2",
    0xF8: "M6 7 C3.3 7 2 8.7 2 11.5 C2 14.3 3.3 16 6 16 C8.7 16 10 14.3 10 11.5 C10 8.7 8.7 7 6 7 M3 17.5 L9 5.5",
    0xFE: "M2 3 V20 M2.3 9.2 C2.7 8 4 7 6 7 C8.6 7 10 8.6 10 11.5 C10 14.4 8.6 16 6 16 C4 16 2.7 15 2.3 13.8",
}

# Combining marks as (template, cap top, cap bottom, lowercase top,
# lowercase bottom). Cap marks live in the 0.7-2.0 band above the y=3 cap
# line; lowercase marks live in the 4.6-5.9 band above the y=7 x-height line.
COMBINING_MARKS = {
    "\u0300": ("M5 {top} L7 {bottom}", 0.7, 2.0, 4.6, 5.9),
    "\u0301": ("M5 {bottom} L7 {top}", 0.7, 2.0, 4.6, 5.9),
    "\u0302": ("M3.8 {bottom} L6 {top} L8.2 {bottom}", 0.7, 2.0, 4.6, 5.9),
    "\u0303": ("M3.3 {bottom} C4.2 {top} 5.1 {top} 6 {bottom} C6.9 {low} 7.8 {low} 8.7 {top}", 0.7, 1.9, 4.6, 5.8),
    "\u0308": ("M4.1 {top} V{bottom} M7.9 {top} V{bottom}", 1.2, 1.5, 4.9, 5.2),
    "\u030a": ("M6 {top} C4.4 {top} 4.4 {bottom} 6 {bottom} C7.6 {bottom} 7.6 {top} 6 {top}", 0.3, 2.0, 4.2, 5.9),
    "\u0327": ("M6 16 C6 17.2 7.8 17.2 7.8 18.4 C7.8 19.4 6.8 20 5.2 20", 0, 0, 0, 0),
}

Element = tuple[str, float]

PATH_COMMANDS = {"M", "L", "H", "V", "C", "S", "Q", "T", "Z"}
NUMBER_PATTERN = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)")


def number(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def transform_path(
    path: str,
    scale_x: float,
    scale_y: float,
    offset_x: float,
    offset_y: float,
) -> str:
    tokens: list[str] = []
    command = ""
    x_axis = True
    for token in NUMBER_PATTERN.findall(path):
        if token.isalpha():
            command = token.upper()
            if command not in PATH_COMMANDS or command != token:
                raise ValueError(f"unsupported path command {token!r}")
            x_axis = True
            tokens.append(token)
            continue
        value = float(token)
        if command == "V" or (command not in "HV" and not x_axis):
            tokens.append(number(value * scale_y + offset_y))
        else:
            tokens.append(number(value * scale_x + offset_x))
        if command not in "HV":
            x_axis = not x_axis
    return " ".join(tokens)


# The regular digits sit on the y=16 baseline, span y=3-16, and center on
# x=6. Small forms are the same drawings scaled about the baseline, with a
# lighter absolute stroke that still reads optically heavier at their size.
SMALL_FORM_SOURCES = {
    **{str(digit): MODERN_PATHS[ord(str(digit))] for digit in range(10)},
    "a": MODERN_PATHS[ord("a")],
    "o": MODERN_PATHS[ord("o")],
}

SMALL_SCALE = 0.52
SMALL_STROKE = 0.72
SUPERSCRIPT_BASELINE = 9.4
SUBSCRIPT_BASELINE = 19.4

FRACTION_SCALE = 0.42
FRACTION_STROKE = 0.68
FRACTION_SLASH = ("M3.1 16.6 L8.9 2.4", 0.85)
NUMERATOR_BASELINE = 8.3
NUMERATOR_CENTER = 3.3
DENOMINATOR_CENTER = 8.7
TENTH_SCALE = 0.34

SUPERSCRIPT_DIGITS = {
    0xB9: "1",
    0xB2: "2",
    0xB3: "3",
    0x2070: "0",
    **{0x2074 + index: str(4 + index) for index in range(6)},
}
SUBSCRIPT_DIGITS = {0x2080 + digit: str(digit) for digit in range(10)}
VULGAR_FRACTIONS = {
    0xBC: ("1", "4"),
    0xBD: ("1", "2"),
    0xBE: ("3", "4"),
    0x2150: ("1", "7"),
    0x2151: ("1", "9"),
    0x2152: ("1", "10"),
    0x2153: ("1", "3"),
    0x2154: ("2", "3"),
    0x2155: ("1", "5"),
    0x2156: ("2", "5"),
    0x2157: ("3", "5"),
    0x2158: ("4", "5"),
    0x2159: ("1", "6"),
    0x215A: ("5", "6"),
    0x215B: ("1", "8"),
    0x215C: ("3", "8"),
    0x215D: ("5", "8"),
    0x215E: ("7", "8"),
    0x2189: ("0", "3"),
}


def small_form(source: str, scale: float, center_x: float, baseline: float) -> str:
    return transform_path(
        SMALL_FORM_SOURCES[source],
        scale,
        scale,
        center_x - 6 * scale,
        baseline - 16 * scale,
    )


def fraction_elements(numerator: str, denominator: str | None) -> list[Element]:
    elements = [
        (
            small_form(digit, FRACTION_SCALE, NUMERATOR_CENTER, NUMERATOR_BASELINE),
            FRACTION_STROKE,
        )
        for digit in numerator
    ]
    elements.append(FRACTION_SLASH)
    if denominator is None:
        return elements
    if len(denominator) == 1:
        centers = [DENOMINATOR_CENTER]
        scale = FRACTION_SCALE
    else:
        centers = [7.0, 9.7]
        scale = TENTH_SCALE
    elements.extend(
        (small_form(digit, scale, center, 16), FRACTION_STROKE)
        for digit, center in zip(denominator, centers, strict=True)
    )
    return elements


def derived_paths() -> dict[int, list[Element]]:
    derived: dict[int, list[Element]] = {}
    for codepoint, digit in SUPERSCRIPT_DIGITS.items():
        derived[codepoint] = [
            (small_form(digit, SMALL_SCALE, 6, SUPERSCRIPT_BASELINE), SMALL_STROKE)
        ]
    for codepoint, digit in SUBSCRIPT_DIGITS.items():
        derived[codepoint] = [
            (small_form(digit, SMALL_SCALE, 6, SUBSCRIPT_BASELINE), SMALL_STROKE)
        ]
    for codepoint, (numerator, denominator) in VULGAR_FRACTIONS.items():
        derived[codepoint] = fraction_elements(numerator, denominator)
    derived[0x215F] = fraction_elements("1", None)
    derived[0x2044] = [("M2.4 17.4 L9.6 1.6", 1.0)]
    # Ordinal indicators are the lowercase letters scaled to superscript size.
    derived[0xAA] = [
        (small_form("a", 0.68, 6, SUPERSCRIPT_BASELINE), SMALL_STROKE)
    ]
    derived[0xBA] = [
        (small_form("o", 0.68, 6, SUPERSCRIPT_BASELINE), SMALL_STROKE)
    ]
    return derived


DERIVED_PATHS = derived_paths()


def normalize_elements(value) -> list[Element]:
    if isinstance(value, str):
        return [(value, 1.0)]
    return list(value)


def modern_elements(codepoint: int) -> list[Element] | None:
    direct = MODERN_PATHS.get(codepoint)
    if direct is not None:
        return normalize_elements(direct)
    derived = DERIVED_PATHS.get(codepoint)
    if derived is not None:
        return derived
    decomposition = unicodedata.normalize("NFD", chr(codepoint))
    if len(decomposition) < 2 or ord(decomposition[0]) not in MODERN_PATHS:
        return None
    if any(mark not in COMBINING_MARKS for mark in decomposition[1:]):
        return None

    base = MODERN_PATHS[ord(decomposition[0])]
    if decomposition[0] in "ij" and any(mark != "\u0327" for mark in decomposition[1:]):
        base = "M6 7 V16" if decomposition[0] == "i" else (
            "M7 7 V17 C7 19 6 20 4.2 20 C3.4 20 2.7 19.8 2 19.4"
        )
    uppercase = decomposition[0].isupper()
    elements = normalize_elements(base)
    for mark in decomposition[1:]:
        template, cap_top, cap_bottom, lower_top, lower_bottom = COMBINING_MARKS[mark]
        top = cap_top if uppercase else lower_top
        bottom = cap_bottom if uppercase else lower_bottom
        elements.append(
            (
                template.format(
                    top=number(top),
                    bottom=number(bottom),
                    low=number(bottom + 0.45),
                ),
                1.0,
            )
        )
    return elements


def parse_source() -> dict[int, tuple[str, ...]]:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    glyphs: dict[int, tuple[str, ...]] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"U\+([0-9A-F]{4,6})(?: .*)?", line)
        if not match:
            raise ValueError(f"{SOURCE}:{index}: invalid glyph header")
        codepoint = int(match.group(1), 16)
        glyphs[codepoint] = tuple(lines[index : index + HEIGHT])
        index += HEIGHT
    return glyphs


def render_design(magick: str, elements: list[Element], stroke_width: float) -> bytes:
    path_elements = "".join(
        f'<path d="{path}" stroke-width="{number(stroke_width * width)}"/>'
        for path, width in elements
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="192" height="352" '
        'viewBox="0 0 12 22">'
        '<rect width="12" height="22" fill="white"/>'
        '<g stroke="black" stroke-linecap="square" stroke-linejoin="round" '
        f'fill="none">{path_elements}</g></svg>'
    )
    return subprocess.run(
        [magick, "svg:-", "-threshold", "50%", "pbm:-"],
        input=svg.encode(),
        capture_output=True,
        check=True,
    ).stdout


def trace(
    potrace: str,
    magick: str,
    codepoint: int,
    rows: tuple[str, ...],
    stroke_width: float,
) -> str:
    if not any("#" in row for row in rows):
        return ""

    elements = modern_elements(codepoint)
    if elements is None:
        raise ValueError(
            f"U+{codepoint:04X} is visible but has no designed geometric outline"
        )

    result = subprocess.run(
        [
            potrace,
            "--backend",
            "svg",
            "--output",
            "-",
            "--tight",
            "--unit",
            "4",
            "--turdsize",
            "0",
            "--alphamax",
            "0.8",
            "--opttolerance",
            "0.15",
            "--turnpolicy",
            "minority",
        ],
        input=render_design(magick, elements, stroke_width),
        capture_output=True,
        check=True,
    )
    paths = re.findall(r'<path d="([\s\S]*?)"/>', result.stdout.decode())
    if not paths:
        raise ValueError("Potrace produced no SVG path for a visible glyph")
    return " ".join(
        re.sub(r"\s+", " ", path).strip()
        for path in paths
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--potrace", default="potrace", help="path to Potrace 1.16")
    parser.add_argument("--magick", default="magick", help="path to ImageMagick")
    parser.add_argument("--stroke-width", type=float, default=1.65)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output

    version = subprocess.run(
        [args.potrace, "--version"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()[0]
    paths = {
        f"{codepoint:04X}": trace(
            args.potrace,
            args.magick,
            codepoint,
            rows,
            args.stroke_width,
        )
        for codepoint, rows in parse_source().items()
    }
    payload = {
        "format": 1,
        "tracer": version,
        "settings": {
            "construction": "purpose-built geometric centerlines and derived small forms",
            "supersample": 16,
            "stroke_width": args.stroke_width,
            "unit": 4,
            "alphamax": 0.8,
            "opttolerance": 0.15,
            "turnpolicy": "minority",
        },
        "paths": paths,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    label = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(f"Wrote {label} ({len(paths)} glyphs)")


if __name__ == "__main__":
    main()
