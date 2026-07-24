# bionic-epub

Turn any EPUB into **Bionic Reading** format — the first part of each word is bolded so your eyes fixate faster. Works on Kindle, Kobo, Apple Books, and any reader that supports bold text.

| Normal | Bionic |
|--------|--------|
| Reading is fun. | **Readi**ng **i**s **fu**n. |

## Install

Requires Python 3.11+.

```bash
pipx install .
```

## Use

```bash
bionic-epub my-book.epub
```

Creates `my-book-bionic.epub` next to the original.

Preview first:

```bash
bionic-epub my-book.epub --preview
```

## Options

| Flag | What it does |
|------|--------------|
| `-o path.epub` | Custom output path |
| `-f 1–5` | Bold strength (default `3`) |
| `-s 10–50` | How often words are bolded (default `10` = every word) |
| `--preview` | Try it on the first 200 words, no file written |
| `--force` | Re-convert even if the file already has a bionic-epub marker |

## Notes

- DRM-protected books won't work — use an unprotected copy.
- **Don't run it twice on the same file.** Always start from the **original** EPUB. Converted files carry a `<meta name="bionic-epub" content="1">` marker; a second run refuses by default. `--force` overrides that and **risks double-bold** (stacked `<b>` tags). There is no safe “strip previous bionic then re-apply.”
- Soft hyphens (U+00AD) and zero-width characters (ZWSP/ZWNJ/ZWJ/BOM) are stripped from body text so words stay one fixation token. Stripping ZWJ can split emoji ZWJ sequences (e.g. family emoji).
- Mid-word italic, links, or styled spans (`<i>`, `<a>`, `class`/`style` spans) are **not** unwrapped; bold may still break inside those words.
- Headings, code blocks, and existing bold text are left alone.
- Hyphen-minus compounds (`well-known`) stay separate tokens around `-` (intentional).

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## License

MIT