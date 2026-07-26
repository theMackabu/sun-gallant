# Contributing

Glyph work happens in `sources/glyphs.txt`. Keep every glyph at exactly 12
columns by 22 rows and use only `#` and `.`.

The original Gallant character range must continue to match
`sources/netbsd-gallant12x22.h` exactly. Characters added by this project live
in the same editable source.

Before opening a change:

```sh
make test
make serve
```

Inspect the affected characters at 22px and 44px in the specimen. Pay special
attention to the baseline, adjacent box-drawing characters, punctuation, and
accent placement.

New scripts and glyphs must be compatible with the repository's BSD 3-Clause
license. Do not copy glyphs from unrelated font projects unless their
provenance and license are explicitly compatible and documented.
