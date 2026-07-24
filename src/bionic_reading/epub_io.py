"""EPUB read/write pipeline."""

from __future__ import annotations

from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from bionic_reading.html import (
    BIONIC_META_CONTENT,
    BIONIC_META_NAME,
    ensure_bionic_marker,
    has_bionic_marker,
    transform_html_tree,
)
from bionic_reading.saccade import SaccadeState
from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformResult, TransformStats

ALREADY_BIONIC_MESSAGE = (
    "This EPUB already appears to have been converted by bionic-epub. "
    "Use the original EPUB, or pass --force to convert again."
)


class AlreadyBionicError(Exception):
    """Raised when an EPUB already carries the bionic-epub meta marker."""

    def __init__(self, message: str = ALREADY_BIONIC_MESSAGE) -> None:
        super().__init__(message)


def _ensure_toc_link_uids(toc: list, next_uid: int = 0) -> int:
    """Assign navPoint ids to ebooklib Link entries missing uid.

    EPUB3 nav parsing creates ``Link`` objects without ids; ebooklib then crashes
    while regenerating the legacy NCX on write.
    """
    for item in toc:
        if isinstance(item, tuple):
            _, children = item
            next_uid = _ensure_toc_link_uids(children, next_uid)
        elif isinstance(item, epub.Link) and item.uid is None:
            item.uid = f"navPoint-{next_uid}"
            next_uid += 1
    return next_uid


def _item_raw_html(item: epub.EpubItem) -> str:
    """Return stored HTML bytes as text without EpubHtml head rebuild.

    ``EpubHtml.get_content()`` rebuilds ``<head>`` from ``item.metas`` only, so
    markers present in on-disk HTML after a prior conversion would be lost.
    Prefer the raw ``content`` attribute when detecting markers on re-read.
    """
    raw = item.content
    if raw is None:
        raw = item.get_content()
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return raw


def document_has_bionic_marker(html: str) -> bool:
    """Return True if *html* contains the bionic-epub meta marker."""
    soup = BeautifulSoup(html, "html.parser")
    return has_bionic_marker(soup)


def book_has_bionic_marker(book: epub.EpubBook) -> bool:
    """Return True if any content document in *book* has the bionic-epub marker.

    Checks raw HTML (on-disk / ``item.content``) and in-memory ``item.metas`` so
    both re-read EPUBs and books stamped only via ``add_meta`` are detected.
    """
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if _item_has_bionic_meta(item) or document_has_bionic_marker(_item_raw_html(item)):
            return True
    return False


def epub_has_bionic_marker(input_path: Path) -> bool:
    """Read an EPUB from disk and check for the bionic-epub marker."""
    book = epub.read_epub(str(input_path), options={"ignore_ncx": True})
    return book_has_bionic_marker(book)


def _item_has_bionic_meta(item: epub.EpubItem) -> bool:
    metas = getattr(item, "metas", None)
    if not metas:
        return False
    return any(
        m.get("name") == BIONIC_META_NAME and str(m.get("content")) == BIONIC_META_CONTENT
        for m in metas
    )


def _stamp_bionic_marker(item: epub.EpubItem, soup: BeautifulSoup) -> None:
    """Ensure the bionic-epub marker is emitted for *item* on write.

    ebooklib's ``EpubHtml.get_content()`` rebuilds ``<head>`` from ``item.metas``
    (and title/links), discarding any ``<meta>`` we inject into the BeautifulSoup
    tree. Register the marker via ``add_meta`` for ``EpubHtml`` items, and also
    stamp the soup so non-rebuilding document types keep it in the body content.
    """
    ensure_bionic_marker(soup)
    if isinstance(item, epub.EpubHtml) and not _item_has_bionic_meta(item):
        item.add_meta(name=BIONIC_META_NAME, content=BIONIC_META_CONTENT)


def _transform_document_item(item: epub.EpubItem, settings: BionicSettings, stats: TransformStats) -> None:
    content = item.get_content().decode("utf-8")
    soup = BeautifulSoup(content, "html.parser")
    root = soup.body if soup.body is not None else soup
    saccade_state = SaccadeState()
    transform_html_tree(root, settings, stats, saccade_state)
    _stamp_bionic_marker(item, soup)
    item.set_content(str(soup).encode("utf-8"))
    stats.documents_processed += 1


def transform_epub(
    input_path: Path,
    output_path: Path,
    settings: BionicSettings | None = None,
) -> TransformResult:
    """Read an EPUB, apply Bionic Reading to document HTML, and write a new EPUB.

    If any content document already has the bionic-epub marker and
    ``settings.skip_if_bionic`` is True (the default), raises
    :class:`AlreadyBionicError` and writes nothing.
    """
    config = settings or BionicSettings()
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    input_bytes = input_path.stat().st_size

    book = epub.read_epub(str(input_path), options={"ignore_ncx": True})
    stats = TransformStats()

    if config.skip_if_bionic and book_has_bionic_marker(book):
        raise AlreadyBionicError()

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        _transform_document_item(item, config, stats)

    _ensure_toc_link_uids(book.toc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)
    output_bytes = output_path.stat().st_size

    return TransformResult(
        input_path=input_path,
        output_path=output_path,
        input_bytes=input_bytes,
        output_bytes=output_bytes,
        settings_fixation=config.fixation,
        settings_saccade=config.saccade,
        stats=stats,
    )
