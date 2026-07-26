# Fontlog

## 0.1.2

- Corrected every glyph's TrueType left side bearing to match its actual
  horizontal inset while preserving the 12-pixel monospace advance.
- Restored the pinned original Gallant glyph shapes and retired the separate
  `Sun Gallant Classic` family.

## 0.1.1

- Added a separate `Sun Gallant Classic` family that preserves the pinned
  Gallant bitmap while retaining the same outline-only TTF and WOFF2 formats.
- Inset the outer serif tips of boundary-reaching capitals by one pixel to
  prevent adjacent capitals from joining, without adding kerning or changing
  the 12-pixel advance.

## 0.1.0

- Seeded Basic Latin and Latin-1 from the independently licensed NetBSD
  Gallant console bitmap.
- Added deterministic bitmap-to-outline generation.
- Added desktop TTF and web WOFF2 outputs.
- Added current-user installation, uninstallation, tests, specimen, and CI.
- Optically widened the serifs of `I`, `i`, `l`, and `f` while preserving the
  original 12-pixel monospace advance.
- Added complete superscript and subscript decimal digits, the fraction slash,
  and the full Unicode set of precomposed vulgar fractions.
