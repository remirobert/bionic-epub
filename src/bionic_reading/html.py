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


def _has_skipped_ancestor(node: NavigableString) -> bool:
    for parent in node.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in SKIP_ANCESTOR_TAGS:
            return True
    return False


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

    for child in list(root.children):
        if isinstance(child, NavigableString):
            if _has_skipped_ancestor(child):
                continue
            parent = child.parent
            if isinstance(parent, Tag) and parent.name in SKIP_CONTAINER_TAGS:
                continue
            _replace_text_node(child, settings, stats, saccade_state)
        elif isinstance(child, Tag):
            transform_html_tree(child, settings, stats, saccade_state)


def transform_html_document(
    html: str,
    settings: BionicSettings | None = None,
    stats: TransformStats | None = None,
    saccade_state: SaccadeState | None = None,
) -> str:
    """Transform an HTML/XHTML document string."""
    config = settings or BionicSettings()
    soup = BeautifulSoup(html, "html.parser")
    root = soup.body if soup.body is not None else soup
    transform_html_tree(root, config, stats, saccade_state)
    return str(soup)
