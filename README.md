# bionic-epub

Convert EPUB ebooks into **Bionic Reading** format — guiding your eyes through text with artificial fixation points so you read faster with less effort.

This tool processes your EPUB files offline, inserts `<b>` tags at the right places, and produces a new ebook that works on any e-reader that supports basic HTML bold text (Kindle, Kobo, Apple Books, etc.).

---

## What is Bionic Reading?

When you read, your eyes don't glide smoothly across the page. They jump between **fixation points** — brief pauses where your brain picks up meaning. Bionic Reading bolds the first part of each word to create those fixation points artificially:

| Normal | Bionic |
|--------|--------|
| Reading is fun. | **Readi**ng **i**s **fu**n. |
| Bienvenue à Paris. | **Bienve**nue à **Par**is. |

The effect is subtle but noticeable: your eyes anchor on the bold segments and your brain completes the rest of the word automatically.

---

## Features

- **Accurate fixation algorithm** — word-length lookup tables reverse-engineered from the official Bionic Reading API ([text-vide](https://github.com/Gumball12/text-vide)), not a naive "bold half the word" shortcut
- **Fixation & saccade controls** — match the settings from the Bionic Reader app
- **English & French** — full Unicode support for accented characters (`é`, `ç`, `œ`, …)
- **EPUB in, EPUB out** — preserves structure, images, and CSS; only body text is modified
- **Live preview** — try settings on the first 200 words before converting the whole book
- **Conversion stats** — file sizes, word counts, bold coverage, and more
- **Smart skipping** — leaves `<pre>`, `<code>`, headings, and existing bold text untouched

---

## Installation

Requires **Python 3.11+**.

### Option A — pipx (recommended for daily use)

Install once, run from anywhere:

```bash
pipx install /path/to/bionic-epub
# or, from inside the repo:
pipx install -e .
```

### Option B — virtual environment (for development)

```bash
cd bionic-epub
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Debian/Ubuntu, if `python3 -m venv` fails:

```bash
sudo apt install python3.11-venv
```

---

## Quick start

```bash
# Preview the effect on the first 200 words (no file written)
bionic-reading epub "my-book.epub" --preview

# Convert — output defaults to my-book-bionic.epub
bionic-reading epub "my-book.epub"

# Try a quick text snippet
bionic-reading transform "Le petit prince voyage loin."
```

---

## CLI reference

### `bionic-reading epub`

Convert an EPUB file.

```bash
bionic-reading epub INPUT [OUTPUT] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `OUTPUT` | `{name}-bionic.epub` | Output path (optional) |
| `-f`, `--fixation` | `2` | Bold strength, 1 (heaviest) to 5 (lightest) |
| `-s`, `--saccade` | `10` | Spacing between bold words, 10 (dense) to 50 (sparse) |
| `--preview` | off | Show a sample without writing a file |
| `--preview-words` | `200` | Words to include in the preview |
| `-q`, `--quiet` | off | Only print the output path |

**Examples:**

```bash
# Preview with custom settings
bionic-reading epub book.epub --preview -f 2 -s 10 --preview-words 100

# Full conversion with explicit output
bionic-reading epub book.epub ~/Books/book-bionic.epub -f 2

# Script-friendly (prints path only)
bionic-reading epub book.epub -q
```

After conversion, you'll see a summary like:

```
✓ Bionic Reading conversion complete

  Input               book.epub (956.0 KB)
  Output              book-bionic.epub (963.0 KB)
  Size change         +7.0 KB (+0.7%)
  Fixation            2
  Saccade             10
  Documents           27
  Words bolded        15,285
  Bold coverage       100.0% of words

Written to: /path/to/book-bionic.epub
```

---

### `bionic-reading transform`

Transform a plain-text snippet (useful for testing settings).

```bash
bionic-reading transform "Your text here" [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-f`, `--fixation` | `1` | Bold strength, 1–5 |
| `-s`, `--saccade` | `10` | Spacing, 10–50 |
| `--html` / `--plain` | `--html` | Output `<b>` tags or spaced plain text |
| `--stats` | off | Print stats to stderr |

---

## Understanding the settings

### Fixation (1–5)

Controls **how much** of each word is bolded. The algorithm uses word-length buckets — longer words get more bold characters, but never a fixed percentage.

| Fixation | Feel | Good for |
|----------|------|----------|
| **1** | Heaviest — most letters bolded | Technical docs, dense non-fiction |
| **2** | Strong — good default for EPUBs | General reading |
| **3** | Balanced | Long-form fiction |
| **4** | Light | Leisure reading |
| **5** | Minimal — only first letter or two | Subtle nudge |

Example with fixation 2:

```
"understanding" → <b>under</b>standing   (6 of 13 chars)
"Paris"         → <b>Par</b>is           (3 of 5 chars)
"is"            → <b>i</b>s              (1 of 2 chars)
```

### Saccade (10–50)

Controls **how often** words are bolded. After each bold word, the converter waits for a number of characters (including spaces) before bolding the next one.

| Saccade | Gap | Effect |
|---------|-----|--------|
| **10** | 0 chars | Bold every word (default) |
| **30** | ~20 chars | Moderate rhythm |
| **50** | ~40 chars | Sparse — only occasional anchors |

```bash
# Every word bolded (recommended starting point)
bionic-reading epub book.epub -s 10

# Lighter touch — bold every ~20 characters
bionic-reading epub book.epub -s 30
```

### Recommended workflow

1. **Preview** with your book and preferred settings:
   ```bash
   bionic-reading epub book.epub --preview -f 2 -s 10
   ```
2. Adjust `-f` and `-s` until it feels right.
3. **Convert** without `--preview`:
   ```bash
   bionic-reading epub book.epub
   ```
4. Open the `-bionic.epub` file on your e-reader.

---

## Python API

You can use the library directly in your own scripts:

```python
from pathlib import Path
from bionic_reading import BionicSettings, transform_text, transform_epub

# Plain text
settings = BionicSettings(fixation=2, saccade=10)
print(transform_text("Bienvenue à Paris.", settings))
# → <b>Bienve</b>nue à <b>Par</b>is.

# Full EPUB
result = transform_epub(
    Path("book.epub"),
    Path("book-bionic.epub"),
    settings,
)
print(f"Bolded {result.stats.words_bolded:,} words")
print(f"Output: {result.output_bytes / 1024:.0f} KB")
```

---

## How it works

```
book.epub
    │
    ▼
┌─────────────────────────────────────┐
│  For each XHTML chapter:            │
│  1. Walk the HTML DOM               │
│  2. Skip script/style/pre/code/     │
│     headings/existing bold          │
│  3. For each text node:             │
│     • Apply fixation (word-length   │
│       lookup tables)                │
│     • Apply saccade rhythm          │
│     • Wrap bold part in <b>         │
│  4. Write modified chapter back     │
└─────────────────────────────────────┘
    │
    ▼
book-bionic.epub
```

The fixation tables were reverse-engineered from the [Bionic Reading API](https://bionic-reading.com/) by the [text-vide](https://github.com/Gumball12/text-vide) project and ported to Python.

---

## What gets modified

| Element | Modified? |
|---------|-----------|
| Paragraph text (`<p>`, `<span>`, `<li>`, …) | Yes |
| Inline emphasis (`<em>`, `<i>`) | Yes — bold applied inside |
| Headings (`<h1>`–`<h6>`) | No — left as-is |
| Existing bold (`<b>`, `<strong>`) | No |
| Code blocks (`<pre>`, `<code>`) | No |
| Pure numbers (`12345`) | No |
| Hyphenated words (`well-known`) | Yes — each part separately |
| French accents & ligatures | Yes |

---

## Limitations

- **DRM-protected ebooks cannot be processed.** Strip DRM first (legally, for personal use only in jurisdictions that allow it).
- **Opacity is not supported.** The official Bionic Reader app can fade unbolded letters; this tool uses standard `<b>` tags only. Most e-ink readers don't support opacity anyway.
- **Font matters.** The effect looks best with a clean serif or sans-serif font. Heavily styled publisher CSS may interact unpredictably with the injected bold tags.
- **Already-bionic EPUBs.** Running the converter twice will double-wrap tags. Always start from the original file.

---

## Development

```bash
# Run tests
pytest -v

# Run tests for a specific module
pytest tests/test_saccade.py -v
```

Project layout:

```
bionic-epub/
├── src/bionic_reading/
│   ├── fixation.py      # Word-length lookup tables (fixation 1–5)
│   ├── saccade.py       # Rhythm between bold words
│   ├── transform.py     # Plain-text transformation
│   ├── html.py          # HTML DOM walker
│   ├── epub_io.py       # EPUB read/write
│   ├── preview.py       # --preview command
│   └── cli.py           # Typer CLI
└── tests/
```


## License

MIT
