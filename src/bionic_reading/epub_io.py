"""EPUB read/write pipeline."""

from __future__ import annotations

from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from bionic_reading.html import transform_html_tree
from bionic_reading.saccade import SaccadeState
from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformResult, TransformStats


def _transform_document_item(item: epub.EpubItem, settings: BionicSettings, stats: TransformStats) -> None:
    content = item.get_content().decode("utf-8")
    soup = BeautifulSoup(content, "html.parser")
    root = soup.body if soup.body is not None else soup
    saccade_state = SaccadeState()
    transform_html_tree(root, settings, stats, saccade_state)
    item.set_content(str(soup).encode("utf-8"))
    stats.documents_processed += 1


def transform_epub(
    input_path: Path,
    output_path: Path,
    settings: BionicSettings | None = None,
) -> TransformResult:
    """Read an EPUB, apply Bionic Reading to document HTML, and write a new EPUB."""
    config = settings or BionicSettings()
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    input_bytes = input_path.stat().st_size

    book = epub.read_epub(str(input_path), options={"ignore_ncx": True})
    stats = TransformStats()

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        _transform_document_item(item, config, stats)

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
