from dataclasses import dataclass, field

from bionic_reading.markers import HtmlBoldMarker, MarkerPair, marker_for_bold_style


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
    # "b+css" (default): <b class="bionic"> + injected stylesheet.
    # "b": plain <b> without class or CSS (tests / minimal markup).
    bold_style: str = "b+css"

    def __post_init__(self) -> None:
        if self.fixation not in range(1, 6):
            raise ValueError("fixation must be between 1 and 5")
        if self.saccade not in range(10, 51):
            raise ValueError("saccade must be between 10 and 50")
        if self.min_bold_word_length < 1:
            raise ValueError("min_bold_word_length must be >= 1")
        try:
            style_marker = marker_for_bold_style(self.bold_style)
        except ValueError as exc:
            raise ValueError("bold_style must be 'b' or 'b+css'") from exc
        # When the caller left the default classed marker, align it with bold_style
        # (e.g. bold_style="b" → plain <b>). Custom markers are left alone.
        if self.marker == HtmlBoldMarker():
            object.__setattr__(self, "marker", style_marker)
