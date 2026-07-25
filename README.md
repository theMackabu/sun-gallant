# Sun Gallant

An independent, open-source outline revival of the 12×22 console font seen on Sun workstations.

Unlike bitmap-strike TTF conversions, Sun Gallant generates ordinary TrueType outlines. The resulting TTF installs like a modern desktop font and the WOFF2 works as a webfont.

The distribution includes two families: **Sun Gallant**, with a restrained optical pass for modern readability, and **Sun Gallant Classic**, which preserves the vendored Gallant bitmap exactly for its original character set.

This project is not affiliated with or endorsed by Sun Microsystems or Oracle.

## Build

You need Python 3.10 or newer and `make`. The first build creates an isolated virtual environment and installs a pinned FontTools release:

```sh
make
```

Outputs:

```text
dist/SunGallant-Regular.ttf
dist/SunGallant-Regular.woff2
dist/SunGallantClassic-Regular.ttf
dist/SunGallantClassic-Regular.woff2
```

Run the complete validation suite with:

```sh
make test
```

Builds are deterministic: identical source and dependencies produce identical font binaries.

## Install

Install the TTF for your current macOS or Linux user:

```sh
make install
```

Remove it again with:

```sh
make uninstall
```

On Windows, build the font and install `dist/SunGallant-Regular.ttf` from Explorer.

Applications that were already running may need to be restarted before the font appears.

## Web

```css
@font-face {
  font-family: 'Sun Gallant';
  src: url('SunGallant-Regular.woff2') format('woff2');
  font-style: normal;
  font-weight: 400;
}

@font-face {
  font-family: 'Sun Gallant Classic';
  src: url('SunGallantClassic-Regular.woff2') format('woff2');
  font-style: normal;
  font-weight: 400;
}
```

The original design is a 12×22 grid. It is pixel-perfect at a CSS font size of 22px and integer multiples such as 44px.

## How it works

The canonical editable revival source is `sources/glyphs.txt`. Each glyph is a 12×22 ASCII grid, where `#` is filled and `.` is empty. The Classic build replaces the original Gallant character range with the bitmaps reconstructed directly from the pinned NetBSD source; characters added by this project are shared by both families.

The builder:

1. validates every glyph and the declared character coverage;
2. finds the exterior boundary of connected pixels;
3. merges collinear edges into compact clockwise TrueType contours;
4. preserves the original 17-pixel ascent, 5-pixel descent, and 12-pixel monospace advance;
5. writes an outline-only TTF and derives WOFF2 from it.

## Coverage

Version 0.1 contains Basic Latin, Latin-1, complete decimal superscript and subscript sets, the Unicode fraction slash, and every precomposed vulgar fraction: 226 encoded glyphs plus `.notdef`.

## License and provenance

Sun Gallant is distributed under the BSD 3-Clause License. The bitmap seed is
derived from NetBSD's `gallant12x22.h`, whose University of California license
is preserved verbatim in the vendored source.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the pinned upstream
revision and checksum.
