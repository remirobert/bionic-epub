"""Plain-text Bionic Reading transformation."""

from __future__ import annotations

import regex

from bionic_reading.fixation import fixation_length
from bionic_reading.markers import MarkerPair, SpaceMarker
from bionic_reading.saccade import SaccadeState
from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformStats

# Must contain at least one letter; pure numbers are skipped.
CONVERTIBLE_WORD = regex.compile(r"(\p{L}|\p{Nd})*\p{L}(\p{L}|\p{Nd})*")


def transform_word(
    word: str,
    settings: BionicSettings,
    stats: TransformStats | None = None,
    saccade_state: SaccadeState | None = None,
) -> str:
    """Apply fixation to a single convertible token."""
    saccade_skipped = False
    bold_len = 0

    if saccade_state is not None and saccade_state.should_skip_word(word):
        saccade_skipped = True
    else:
        bold_len = fixation_length(word, settings.fixation)
        if bold_len > 0 and saccade_state is not None:
            saccade_state.on_word_bolded(settings.saccade)

    if stats is not None:
        stats.record_word(word, bold_len, saccade_skipped=saccade_skipped)

    if bold_len <= 0:
        return word

    bold_part = word[:bold_len]
    rest = word[bold_len:]
    return settings.marker.wrap(bold_part) + rest


def transform_text(
    text: str,
    settings: BionicSettings | None = None,
    stats: TransformStats | None = None,
    saccade_state: SaccadeState | None = None,
) -> str:
    """Transform plain text using Bionic Reading fixation rules."""
    if not text:
        return ""

    config = settings or BionicSettings()
    state = saccade_state if saccade_state is not None else SaccadeState()
    parts: list[str] = []
    last_index = 0

    for match in CONVERTIBLE_WORD.finditer(text):
        start, end = match.span()
        word = match.group(0)

        gap = text[last_index:start]
        if gap:
            state.consume(len(gap))
        parts.append(gap)

        saccade_skipped = False
        bold_len = 0
        if state.should_skip_word(word):
            saccade_skipped = True
        else:
            bold_len = fixation_length(word, config.fixation)
            if bold_len > 0:
                state.on_word_bolded(config.saccade)

        if stats is not None:
            stats.record_word(word, bold_len, saccade_skipped=saccade_skipped)

        if bold_len > 0:
            parts.append(config.marker.wrap(word[:bold_len]))
        parts.append(word[bold_len:])

        last_index = end

    parts.append(text[last_index:])
    return "".join(parts)


def transform_text_spaced(text: str, fixation: int = 1, saccade: int = 10) -> str:
    """Transform with space markers (visual debugging / parity checks)."""
    return transform_text(text, BionicSettings(fixation=fixation, saccade=saccade, marker=SpaceMarker()))
