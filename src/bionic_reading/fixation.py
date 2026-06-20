"""Fixation length lookup tables reverse-engineered from the Bionic Reading API.

Source: https://github.com/Gumball12/text-vide
"""

from __future__ import annotations

# Each list maps word length to a bucket; bold length = word_length - bucket_index.
FIXATION_BOUNDARIES: dict[int, list[int]] = {
    1: [0, 4, 12, 17, 24, 29, 35, 42, 48],
    2: [1, 2, 7, 10, 13, 14, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, 49],
    3: [
        1, 2, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39,
        41, 43, 45, 47, 49,
    ],
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
    boundaries = FIXATION_BOUNDARIES.get(fixation, FIXATION_BOUNDARIES[1])

    bucket_index = next((index for index, boundary in enumerate(boundaries) if word_length <= boundary), -1)
    if bucket_index == -1:
        bold_length = word_length - len(boundaries)
    else:
        bold_length = word_length - bucket_index

    return max(bold_length, 0)
