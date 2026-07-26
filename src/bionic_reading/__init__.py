"""Bionic Reading text transformation (API-accurate fixation algorithm)."""

from bionic_reading.fixation import fixation_length
from bionic_reading.html import transform_html_document, transform_html_tree
from bionic_reading.markers import HtmlBoldMarker, MarkerPair, PlainHtmlBoldMarker, SpaceMarker
from bionic_reading.settings import BionicSettings
from bionic_reading.transform import transform_text, transform_text_spaced, transform_word

__all__ = [
    "BionicSettings",
    "HtmlBoldMarker",
    "MarkerPair",
    "PlainHtmlBoldMarker",
    "SpaceMarker",
    "fixation_length",
    "bionic_output_path",
    "transform_epub",
    "transform_html_document",
    "transform_html_tree",
    "transform_text",
    "transform_text_spaced",
    "transform_word",
]


def transform_epub(*args, **kwargs):
    """Lazy import so plain-text/HTML use works without ebooklib installed."""
    from bionic_reading.epub_io import transform_epub as _transform_epub

    return _transform_epub(*args, **kwargs)


def bionic_output_path(input_path):
    from bionic_reading.paths import bionic_output_path as _bionic_output_path

    return _bionic_output_path(input_path)
