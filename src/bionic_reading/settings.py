from dataclasses import dataclass, field

from bionic_reading.markers import HtmlBoldMarker, MarkerPair


@dataclass(frozen=True, slots=True)
class BionicSettings:
    """Runtime options mirroring the Bionic Reading app/API."""

    fixation: int = 3
    saccade: int = 10
    marker: MarkerPair = field(default_factory=HtmlBoldMarker)
    min_bold_word_length: int = 2
    # When True, refuse to re-convert books that already carry the bionic-epub marker.
    # CLI --force sets this to False.
    skip_if_bionic: bool = True

    def __post_init__(self) -> None:
        if self.fixation not in range(1, 6):
            raise ValueError("fixation must be between 1 and 5")
        if self.saccade not in range(10, 51):
            raise ValueError("saccade must be between 10 and 50")
        if self.min_bold_word_length < 1:
            raise ValueError("min_bold_word_length must be >= 1")
