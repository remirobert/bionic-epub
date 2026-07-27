"""Fixation length: how many leading characters to bold.

- **Fixation 3 (default)** matches the official Bionic Reading *web demo* base
  setting: ``round(0.4 * word_length)``. Validated against public demo samples
  (English prose); see ``tests/fixtures/parity/``.
- **Fixation 1, 2, 4, 5** keep the reverse-engineered boundary tables from
  https://github.com/Gumball12/text-vide (API-oriented). Those levels are not
  re-tuned for web-demo parity in this pass.
"""

from __future__ import annotations

# Website base fixation (level 3): bold prefix ≈ 40% of word length.
WEBSITE_DEFAULT_FIXATION_RATIO = 0.4

# Boundary tables for non-default fixation levels.
# bold length = word_length - bucket_index (see fixation_length).
# Level 3 is intentionally absent: it uses WEBSITE_DEFAULT_FIXATION_RATIO.
FIXATION_BOUNDARIES: dict[int, list[int]] = {
    1: [0, 4, 12, 17, 24, 29, 35, 42, 48],
    2: [1, 2, 7, 10, 13, 14, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, 49],
    4: [
        0, 2, 4, 5, 6, 8, 9, 11, 14, 15, 17, 18, 20, 0, 21, 23, 24, 26, 27, 29, 30,
        32, 33, 35, 36, 38, 39, 41, 42, 44, 45, 47, 48,
    ],
    5: [
        0, 2, 3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 17, 19, 20, 21, 23, 24, 25, 26, 28,
        29, 30, 32, 33, 34, 35, 37, 38, 39, 41, 42, 43, 44, 46, 47, 48,
    ],
}


def fixation_length(word: str, fixation: int = 1) -> int:
    """Return how many leading characters to bold in *word*."""
    if not word:
        return 0

    word_length = len(word)

    # Default level: match official web demo (not the older text-vide table).
    if fixation == 3:
        return max(0, round(word_length * WEBSITE_DEFAULT_FIXATION_RATIO))

    boundaries = FIXATION_BOUNDARIES.get(fixation, FIXATION_BOUNDARIES[1])

    bucket_index = next(
        (index for index, boundary in enumerate(boundaries) if word_length <= boundary),
        -1,
    )
    if bucket_index == -1:
        bold_length = word_length - len(boundaries)
    else:
        bold_length = word_length - bucket_index

    return max(bold_length, 0)
