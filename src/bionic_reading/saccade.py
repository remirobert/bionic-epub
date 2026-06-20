"""Saccade rhythm — spacing between bold fixation points."""

from __future__ import annotations

from dataclasses import dataclass

# Official Bionic Reading API uses saccade values 10–50.
SACCADE_MIN = 10
SACCADE_MAX = 50


@dataclass
class SaccadeState:
    """Tracks how far the reader's eye must travel before the next bold word.

    Lower saccade values (10) bold nearly every word. Higher values (50) leave
    longer gaps between bolded words. The gap after each bold word is
    ``saccade - SACCADE_MIN`` characters (including spaces and punctuation).
    """

    remaining: int = 0

    def consume(self, length: int) -> None:
        if length > 0:
            self.remaining -= length

    def should_skip_word(self, word: str) -> bool:
        """Advance the rhythm and return True if this word should stay unbolded."""
        self.consume(len(word))
        return self.remaining > 0

    def on_word_bolded(self, saccade: int) -> None:
        self.remaining = saccade - SACCADE_MIN

    def reset(self) -> None:
        self.remaining = 0
