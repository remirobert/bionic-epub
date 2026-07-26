from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarkerPair:
    """Wraps the bold (fixation) portion of a word."""

    prefix: str
    suffix: str

    def wrap(self, text: str) -> str:
        if not text:
            return ""
        return f"{self.prefix}{text}{self.suffix}"


def HtmlBoldMarker() -> MarkerPair:
    """Default production marker: plain ``<b>…</b>``."""
    return MarkerPair("<b>", "</b>")


def SpaceMarker() -> MarkerPair:
    """Visual separator: trailing space after the bold segment."""
    return MarkerPair("", " ")
