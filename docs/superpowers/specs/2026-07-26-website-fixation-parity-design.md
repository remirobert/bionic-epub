# Website fixation parity (default `-f 3`)

## Goal

Make the **default** bionic transform match the official [Bionic Reading web demo](https://bionic-reading.com/) base settings more closely (Fixation middle / “3”, Saccade 10).

## Findings

Compared English samples from the public demo against this project’s reverse-engineered tables (`text-vide`):

| Approach | Exact bold-length match (Harry Potter sample, 168 tokens) |
|----------|-----------------------------------------------------------|
| Table fixation 3 (old default) | ~41% |
| Table fixation 4 | ~76% |
| **`round(0.4 × n)`** | **~97%** (residual: single-letter initials) |

Official demo bold length is almost purely a function of word length:

| len | bold |
|-----|------|
| 1 | 0 (usually; initials sometimes 1) |
| 2–3 | 1 |
| 4–6 | 2 |
| 7–8 | 3 |
| 9–10 | 4 |

That is exactly `round(0.4 * n)` (with `min_bold_word_length = 2` leaving lone `a` unbolded).

Old table f=3 systematically over-bolded by **+1** character for lengths ≥ 5 (`**Har**ry` vs official `**Ha**rry`).

## Decision

1. **Fixation 3** → `round(0.4 * word_length)` (website default parity).
2. **Fixation 1, 2, 4, 5** → keep existing boundary tables (not re-tuned this pass).
3. **`min_bold_word_length = 2`** unchanged (skips single-letter clitics; known gap vs website initials `J`/`K`/`A`).
4. **Golden fixtures** under `tests/fixtures/parity/` + scorer requiring ≥ 95% exact match.

## Out of scope

- Retuning fixation 1/2/4/5 for demo parity  
- Saccade values other than 10  
- Opacity / visual styling  
- Changing apostrophe or hyphen tokenization  

## Success criteria

- Default (`fixation=3`) exact match ≥ 95% on parity fixtures  
- Existing non-default `-f` behavior unchanged except via shared helpers  
- Tests green  

## Implementation

- `src/bionic_reading/fixation.py` — special-case `fixation == 3`  
- `tests/fixtures/parity/*.json` — demo samples  
- `tests/test_website_parity.py` — formula + fixture scorer  
- README note on default meaning  
