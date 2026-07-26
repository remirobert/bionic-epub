"""Transform HTML/XHTML text nodes while preserving document structure."""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

from bionic_reading.saccade import SaccadeState
from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformStats
from bionic_reading.transform import transform_text

# Never modify content inside these elements.
SKIP_CONTAINER_TAGS = frozenset(
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

# Text inside these tags is already emphasized; leave it unchanged.
SKIP_ANCESTOR_TAGS = frozenset({"b", "strong", "h1", "h2", "h3", "h4", "h5", "h6"})

# Microsoft Word / Calibre exports often wrap individual accented letters in
# <span lang="…"> with no other attributes. Those split real words across text
# nodes and break continuous bionic bold if left in place.
_LANGUAGE_ONLY_ATTRS = frozenset({"lang", "xml:lang"})

# Soft hyphens and zero-width characters split convertible words for fixation.
# Strip them from eligible text nodes during normalize (before smooth).
# U+00AD soft hyphen, U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ, U+FEFF BOM.
# Note: stripping U+200D (ZWJ) is intentional for token integrity; it may
# split emoji ZWJ sequences (e.g. family emoji) into separate code points.
_BREAK_JUNK_CHARS = "\u00ad\u200b\u200c\u200d\ufeff"
_BREAK_JUNK_TABLE = str.maketrans("", "", _BREAK_JUNK_CHARS)


def _has_skipped_ancestor(node: NavigableString) -> bool:
    for parent in node.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in SKIP_ANCESTOR_TAGS:
            return True
    return False


def _is_language_only_span(tag: Tag) -> bool:
    if tag.name != "span":
        return False
    return set(tag.attrs) <= _LANGUAGE_ONLY_ATTRS


def _unwrap_language_only_spans(root: Tag) -> None:
    """Remove spans that only carry language attributes (no visual styling)."""
    for span in list(root.find_all("span")):
        if _is_language_only_span(span):
            span.unwrap()


def _strip_break_junk_from_text_nodes(root: Tag) -> None:
    """Remove soft hyphens and zero-width junk from eligible text nodes.

    Same skip rules as transform: skip containers and emphasized/heading
    ancestors. Only pure ``NavigableString`` text is rewritten (not Comment
    or CData subclasses, which ``isinstance(..., NavigableString)`` would
    also match).
    """
    if root.name in SKIP_CONTAINER_TAGS:
        return

    for child in list(root.children):
        # Exact type check: Comment/CData subclass NavigableString; rewriting
        # them with replace_with would demote comments to visible body text.
        if type(child) is NavigableString:
            if _has_skipped_ancestor(child):
                continue
            parent = child.parent
            if isinstance(parent, Tag) and parent.name in SKIP_CONTAINER_TAGS:
                continue
            original = str(child)
            if not original:
                continue
            cleaned = original.translate(_BREAK_JUNK_TABLE)
            if cleaned != original:
                child.replace_with(cleaned)
        elif isinstance(child, Tag):
            _strip_break_junk_from_text_nodes(child)


def _normalize_text_boundaries(root: Tag) -> None:
    """Normalize the HTML tree so whole words are single continuous text nodes.

    Ordered steps:

    1. Unwrap language-only spans (``lang`` / ``xml:lang`` only) that Word and
       similar exporters insert mid-word.
    2. Strip soft hyphens (U+00AD) and zero-width junk (U+200B–U+200D, U+FEFF)
       from eligible text nodes so they cannot split fixation tokens.
    3. ``root.smooth()`` merges adjacent strings into single text nodes.

    Word-generated EPUBs commonly produce markup like::

        <span lang="FR">é</span><span lang="FR">l</span><span lang="FR">é</span>
        <span lang="FR">ments</span>

    or soft-hyphenated forms like ``plan\\u00adète``. Each fragment would
    otherwise receive its own fixation bold. After normalize, words are
    continuous again before transformation.
    """
    _unwrap_language_only_spans(root)
    _strip_break_junk_from_text_nodes(root)
    root.smooth()


# Public alias matching the design entrypoint name.
normalize_html_tree = _normalize_text_boundaries

# Idempotency marker written into each transformed HTML document's <head>.
BIONIC_META_NAME = "bionic-epub"
BIONIC_META_CONTENT = "1"


def _ensure_head(soup: BeautifulSoup) -> Tag:
    """Return ``<head>``, creating it under ``<html>`` (or document root) if missing."""
    head = soup.head
    if head is not None:
        return head

    head = soup.new_tag("head")
    html_tag = soup.find("html")
    if html_tag is not None:
        html_tag.insert(0, head)
    else:
        soup.insert(0, head)
    return head


def has_bionic_marker(soup: BeautifulSoup | Tag) -> bool:
    """Return True if the document has the bionic-epub meta marker.

    Detection uses only ``name="bionic-epub"`` and ``content="1"``.
    """
    return (
        soup.find("meta", attrs={"name": BIONIC_META_NAME, "content": BIONIC_META_CONTENT})
        is not None
    )


def ensure_bionic_marker(soup: BeautifulSoup) -> None:
    """Inject ``<meta name="bionic-epub" content="1" />`` into ``<head>``.

    Creates ``<head>`` when missing (under ``<html>`` if present, else at the
    document root). No-op when the marker is already present so force re-runs
    do not stack duplicate metas.
    """
    if has_bionic_marker(soup):
        return

    head = _ensure_head(soup)
    meta = soup.new_tag("meta", attrs={"name": BIONIC_META_NAME, "content": BIONIC_META_CONTENT})
    head.append(meta)


def _replace_text_node(
    node: NavigableString,
    settings: BionicSettings,
    stats: TransformStats | None,
    saccade_state: SaccadeState | None,
) -> None:
    original = str(node)
    if not original:
        return

    node_stats = TransformStats() if stats is not None else None
    transformed = transform_text(original, settings, node_stats, saccade_state)
    if transformed == original:
        return

    if stats is not None and node_stats is not None:
        stats.merge(node_stats)
        stats.text_nodes_changed += 1

    fragment = BeautifulSoup(transformed, "html.parser")
    replacement = fragment.contents
    if not replacement:
        return

    if len(replacement) == 1:
        node.replace_with(replacement[0])
    else:
        node.replace_with(*replacement)


def _walk_text_nodes(
    root: Tag,
    settings: BionicSettings,
    stats: TransformStats | None,
    saccade_state: SaccadeState,
) -> None:
    if root.name in SKIP_CONTAINER_TAGS:
        return

    for child in list(root.children):
        # Exact type check so Comment/CData are not treated as body text.
        if type(child) is NavigableString:
            if _has_skipped_ancestor(child):
                continue
            parent = child.parent
            if isinstance(parent, Tag) and parent.name in SKIP_CONTAINER_TAGS:
                continue
            _replace_text_node(child, settings, stats, saccade_state)
        elif isinstance(child, Tag):
            _walk_text_nodes(child, settings, stats, saccade_state)


def transform_html_tree(
    root: Tag,
    settings: BionicSettings,
    stats: TransformStats | None = None,
    saccade_state: SaccadeState | None = None,
) -> None:
    """Apply Bionic Reading to all eligible text nodes under *root*."""
    if saccade_state is None:
        saccade_state = SaccadeState()

    if root.name in SKIP_CONTAINER_TAGS:
        return

    # Merge Word-style mid-word language spans before fixation is applied.
    _normalize_text_boundaries(root)
    _walk_text_nodes(root, settings, stats, saccade_state)


def transform_html_document(
    html: str,
    settings: BionicSettings | None = None,
    stats: TransformStats | None = None,
    saccade_state: SaccadeState | None = None,
) -> str:
    """Transform an HTML/XHTML document string and stamp the bionic-epub marker."""
    config = settings or BionicSettings()
    soup = BeautifulSoup(html, "html.parser")
    root = soup.body if soup.body is not None else soup
    transform_html_tree(root, config, stats, saccade_state)
    ensure_bionic_marker(soup)
    return str(soup)
