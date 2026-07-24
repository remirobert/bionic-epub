# Quality Hardening Pack — Design

**Date:** 2026-07-24  
**Status:** Approved for implementation planning  
**Scope:** Reading-quality improvements for `bionic-epub` (CLI, EPUB-only)

## Problem

Converted books often *look* wrong even when the fixation algorithm is correct:

1. **Broken mid-word bold** — Microsoft Word / Calibre EPUBs wrap accented letters in separate `<span lang="…">` nodes. Fixation runs per text node, so a word like *éléments* becomes discontinuous bold. (Language-only span unwrap is already landed; soft hyphens and zero-width characters remain.)
2. **Noisy short tokens** — At default fixation (3), single-letter tokens (`l`, `y`, `à`, `d` before elisions) get fully bolded.
3. **Double conversion** — Re-running the tool on a bionic file stacks `<b>` tags and degrades text.
4. **Weak bold on e-readers** — Plain `<b>` is sometimes low-contrast on Kindle/Kobo without CSS weight help.
5. **Regressions** — Quality bugs reappear without golden fixtures for messy real-world HTML.

## Goals

- Continuous bold prefixes for whole words after normalizing Word-style fragmentation and invisible break characters.
- Safe default: refuse (or no-op) when input was already produced by bionic-epub, with `--force` escape hatch.
- Visibly reliable bold via `<b class="bionic">` plus a small injected stylesheet.
- Fewer useless single-letter bold runs (especially French elisions).
- Automated tests so these behaviors do not regress.

### Success criteria

| Criterion | Observable result |
|-----------|-------------------|
| Word-export French | `éléments` → single continuous fixation prefix (e.g. `<b class="bionic">éléme</b>nts`) |
| Soft hyphen | `planète` with U+00AD mid-word still one token for fixation |
| Min length | Words of length 1 are never wrapped in bionic markers |
| Idempotency | Second run without `--force` skips transform and warns |
| CSS | Converted HTML includes bionic class markers and stylesheet rules for `font-weight: 700` |
| CI | New unit/fixture tests pass in `pytest` |

## Non-goals

- PDF, AZW/Kindle source, DOCX, or other formats
- GUI, web app, or Calibre plugin
- Pixel-perfect parity with the proprietary Bionic Reading API
- Per-chapter or interactive settings UI
- Merging text *across* real presentational markup (`<i>`, `<a>`, styled spans) mid-word
- Strip-and-reapply of arbitrary existing bold (too unsafe)
- Poetry-specific modes, dictionary-based morphology, German compound splitting

## Approach

**Normalize pipeline + focused hardening** (not a rewrite, not ad-hoc one-off patches only).

```
EPUB item HTML
    → BeautifulSoup parse
    → normalize_html_tree()          # formal pre-stage
    → walk text nodes → transform_text
    → ensure_bionic_css()            # marker + stylesheet
    → serialize → write EPUB
```

## Architecture

### Pipeline stages

1. **Parse** — existing BeautifulSoup usage in `html.py` / `epub_io.py`.
2. **Normalize** — `normalize_html_tree(root)` run once on the document root before any fixation.
3. **Detect already-bionic** — if any content document has the marker and `skip_if_bionic` is true, abort the whole book (no output written) unless `--force`.
4. **Transform** — existing text-node walk + `transform_text` (fixation + saccade), with min word length gate.
5. **Mark + style** — inject conversion marker and CSS; use classed bold markers.
6. **Write** — existing ebooklib path.

### Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `html.py` | Normalize, walk, replace text nodes, CSS/marker inject orchestration for a tree |
| `transform.py` | Plain-text fixation; enforce `min_bold_word_length` |
| `markers.py` | Default marker becomes `<b class="bionic">` … `</b>` (or settings-driven) |
| `settings.py` | `min_bold_word_length`, `bold_style`, `skip_if_bionic` (see Settings) |
| `epub_io.py` | Call normalize/transform path; handle book-level already-bionic policy; optional stats |
| `cli.py` | Expose `--force`; keep other quality defaults implicit |
| Tests + `tests/fixtures/` | HTML snippets for Word spans, soft hyphens, already-bionic, French sample |

No new third-party dependencies.

If normalize helpers grow past a maintainable size in `html.py`, extract `normalize.py` without changing behavior.

## Normalize rules (ordered)

Run on the tree root (body preferred, else soup):

1. **Unwrap language-only spans** — `<span>` whose attributes are a subset of `{lang, xml:lang}` only. (Already implemented.)
2. **Strip break junk from text nodes** — remove:
   - soft hyphen U+00AD
   - zero-width space U+200B
   - zero-width non-joiner U+200C
   - zero-width joiner U+200D
   - BOM U+FEFF  
   Only from `NavigableString` nodes outside skip containers (same skip set as transform).
3. **`root.smooth()`** — merge adjacent strings so words are single text nodes again.

**Do not unwrap** spans that have `class`, `style`, `id`, or any non-language attribute.

**Known limit:** mid-word `<i>`, `<a>`, or styled `<span>` still split tokens. Out of scope for this pack.

## Idempotency

### Marker

On successful conversion, mark **each transformed HTML document** with:

```html
<meta name="bionic-epub" content="1" />
```

in `<head>` (create `<head>` if missing). Detection uses only this meta name/content pair—not bold-density heuristics.

### Behavior

| Input | Default | With `--force` |
|-------|---------|----------------|
| No marker in any content doc | Transform all docs | Transform all docs |
| Marker in **any** content doc | Abort: stderr message, exit code `1`, **no output file written** | Transform again (user accepts risk of double-bold) |

**Do not** implement “strip previous bionic bold then re-apply” in this pack. Original author bold and bionic bold are not reliably distinguishable without our marker.

## Bold rendering

### Marker HTML

Default wrap:

```html
<b class="bionic">…</b>
```

### CSS inject (when `bold_style` is `b+css`, the default)

Ensure once per HTML document in `<head>` (create head if missing):

```css
b.bionic {
  font-weight: 700;
}
```

Optionally scope under body marker; class on `b` is enough.

### Fallback

`bold_style="b"` keeps plain `<b>` without class/CSS for debugging or minimal markup.

## Skip and token rules

### Structural skips (unchanged)

- Containers: `script`, `style`, `head`, `title`, `meta`, `pre`, `code`, `kbd`, `samp`, `noscript`, `svg`, `math`
- Ancestors: `b`, `strong`, `h1`–`h6`

### Min bold word length

- Default `min_bold_word_length = 2`
- Words shorter than this are never wrapped (fixation length forced to 0)
- Improves French elision display: `l'homme` → `l'<b class="bionic">hom</b>me` (not bold `l`)

### French / Unicode

- Apostrophe (ASCII and U+2019) remains a non-word boundary (current regex) — intentional
- Soft hyphen / ZW stripped in normalize so they do not split words
- Hyphen-minus compounds remain separate tokens around `-` — intentional; document in README
- No morphological dictionary

## Settings and CLI

| Setting | Default | CLI |
|---------|---------|-----|
| `fixation` | 3 | `-f` (existing) |
| `saccade` | 10 | `-s` (existing) |
| `min_bold_word_length` | 2 | Not exposed in v1 (hardcoded default) |
| `bold_style` | `b+css` | Not exposed in v1 (hardcoded default) |
| `skip_if_bionic` | `true` | Inverted by `--force` |

YAGNI: only `--force` is new user-facing surface for this pack. Internal settings fields may exist for tests.

## Error handling and UX

- Already-bionic without `--force`: stderr message explaining to use the original EPUB or pass `--force`; **exit code `1`**; **no output file written**.
- Preview mode (`--preview`): same detection—refuse preview without `--force` (exit code `1`); with `--force`, preview as today.
- Stats for skipped docs: not required for v1.

## Testing

### Unit

- Normalize: language spans (existing), soft hyphen removal, ZW removal, smooth merge
- Min word length: `"a"` and `"à"` never bolded at fixation 2–3
- Idempotency: marked HTML is not re-transformed without force
- Marker: output contains `b.bionic` and CSS rule when default style is on
- French: `l'homme` / `l’homme` produce unbolded `l` + bolded prefix on `homme`

### Fixtures

Under `tests/fixtures/quality/` (or equivalent):

- Word-style split *éléments* paragraph
- Soft-hyphen mid-word sample
- Minimal already-bionic HTML with meta marker
- Clean control paragraph (no normalize needed)

Assertions prefer stable substrings over full-document equality (BeautifulSoup serialization variance).

### EPUB

Existing EPUB round-trip tests remain green; add one small EPUB case with marker detection if practical.

## Implementation order

1. Formalize normalize entrypoint; add soft-hyphen / ZW strip + tests  
2. `min_bold_word_length` default 2 in transform path + tests  
3. Bionic marker + skip / `--force` + tests  
4. `b.bionic` marker + CSS inject + tests  
5. Fixture suite + README notes (limits: mid-word `<i>`/`<a>`, no double-run without `--force`)

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Unwrapping spans loses language metadata | Only unwrap lang-only spans; document/html `lang` usually remains |
| CSS ignored on some devices | Keep real `<b>`; CSS is enhancement |
| False positive already-bionic | Use our explicit meta marker only, not heuristic bold density |
| False negative (old bionic files without marker) | README: start from original; `--force` still dangerous on unmarked bionic files |
| Serialization changes EPUB diffs | Tests use substring checks; accept larger output from CSS |

## Future work (out of this pack)

- Cross-node tokenization through transparent or presentational inline tags  
- `epub:type` / landmark skips (TOC, landmarks)  
- Exposed CLI for min-word-length and bold-style  
- Side-by-side HTML preview for tuning  
- Larger golden corpus and optional API parity snapshots  
- Other formats
