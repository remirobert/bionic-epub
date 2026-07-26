from dataclasses import dataclass

# Class applied to bionic fixation wrappers when bold_style is b+css.
BIONIC_BOLD_CLASS = "bionic"


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
    """Default production marker: ``<b class="bionic">…</b>``."""
    return MarkerPair(f'<b class="{BIONIC_BOLD_CLASS}">', "</b>")


def PlainHtmlBoldMarker() -> MarkerPair:
    """Plain ``<b>`` without class (``bold_style='b'`` / minimal tests)."""
    return MarkerPair("<b>", "</b>")


def marker_for_bold_style(bold_style: str) -> MarkerPair:
    """Return the HTML marker pair for a *bold_style* setting value."""
    if bold_style == "b":
        return PlainHtmlBoldMarker()
    if bold_style == "b+css":
        return HtmlBoldMarker()
    raise ValueError("bold_style must be 'b' or 'b+css'")


def SpaceMarker() -> MarkerPair:
    """Visual separator: trailing space after the bold segment."""
    return MarkerPair("", " ")
