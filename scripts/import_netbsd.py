#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

WIDTH = 12
HEIGHT = 22
BYTES_PER_ROW = 2
SOURCE_MARKER = "static u_char gallant12x22_data[] = {"


def parse_header(path: Path) -> list[list[int]]:
    source = path.read_text(encoding="utf-8")
    try:
        body = source.split(SOURCE_MARKER, 1)[1].split("};", 1)[0]
    except IndexError as exc:
        raise ValueError(f"could not find Gallant bitmap array in {path}") from exc

    raw = bytes(int(value, 16) for value in re.findall(r"0x([0-9a-fA-F]{2})", body))
    expected = 256 * HEIGHT * BYTES_PER_ROW
    if len(raw) != expected:
        raise ValueError(f"expected {expected} bitmap bytes, found {len(raw)}")

    glyphs: list[list[int]] = []
    bytes_per_glyph = HEIGHT * BYTES_PER_ROW
    for codepoint in range(256):
        start = codepoint * bytes_per_glyph
        data = raw[start : start + bytes_per_glyph]
        rows = [(data[index] << 8) | data[index + 1] for index in range(0, len(data), 2)]
        glyphs.append(rows)
    return glyphs


def glyph_name(codepoint: int) -> str:
    if codepoint == 0:
        return ".notdef"
    try:
        return unicodedata.name(chr(codepoint))
    except ValueError:
        return f"UNNAMED-{codepoint:04X}"


def render_source(glyphs: list[list[int]]) -> str:
    lines = [
        "# Sun Gallant editable glyph source",
        "",
    ]
    codepoints = [0, *range(0x20, 0x7F), *range(0xA0, 0x100)]
    for codepoint in codepoints:
        lines.append(f"U+{codepoint:04X} {glyph_name(codepoint)}")
        for packed_row in glyphs[codepoint]:
            row = packed_row >> 4
            lines.append(
                "".join("#" if row & (1 << (WIDTH - column - 1)) else "." for column in range(WIDTH))
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("sources/netbsd-gallant12x22.h"),
        help="vendored NetBSD header",
    )
    parser.add_argument(
        "--output",
        default="sources/glyphs.txt",
        help="output path, or - for stdout",
    )
    args = parser.parse_args()

    rendered = render_source(parse_header(args.input))
    if args.output == "-":
        sys.stdout.write(rendered)
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()

