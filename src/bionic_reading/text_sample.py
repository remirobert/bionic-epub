"""Extract readable text samples from EPUBs for preview."""

from __future__ import annotations

import re
from pathlib import Path

import regex
from bs4 import BeautifulSoup

# Tags excluded from readable-text extraction (mirrors html.py).
SKIP_TAGS = frozenset(
    {
        "script",
        "style",
        "head",
        "title",
        "meta",
        "pre",
        "code",
        "kbd",
        "samp",
        "noscript",
        "svg",
        "math",
    }
)

_WORD = regex.compile(r"\S+", regex.UNICODE)
# Plain <b> / </b> (also tolerates classed open tags from older output).
_TAG = re.compile(r"</?b(?:\s[^>]*)?>")


def take_words(text: str, limit: int) -> tuple[str, int]:
    """Return up to *limit* words and the number of words included."""
    if limit <= 0:
        return "", 0
    words = _WORD.findall(text)
    sample = words[:limit]
    return " ".join(sample), len(sample)


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def extract_readable_text(html: str) -> str:
    """Pull visible paragraph text from an HTML/XHTML fragment."""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.body if soup.body is not None else soup
    for tag in root.find_all(list(SKIP_TAGS)):
        tag.decompose()
    return normalize_whitespace(root.get_text(separator=" ", strip=True))


def extract_epub_text_sample(input_path: Path, word_limit: int = 200) -> tuple[str, int]:
    """Read an EPUB and return the first *word_limit* words of readable body text."""
    import ebooklib
    from ebooklib import epub

    book = epub.read_epub(str(input_path), options={"ignore_ncx": True})
    collected: list[str] = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode("utf-8")
        chunk = extract_readable_text(content)
        if not chunk:
            continue
        words = _WORD.findall(chunk)
        collected.extend(words)
        if len(collected) >= word_limit:
            break

    sample, count = take_words(" ".join(collected), word_limit)
    return sample, count


def strip_bold_tags(text: str) -> str:
    return _TAG.sub("", text)
