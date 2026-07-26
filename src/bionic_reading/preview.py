"""Terminal preview of Bionic Reading output."""

from __future__ import annotations

import re
from pathlib import Path

import typer

from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformStats, format_count
from bionic_reading.text_sample import extract_epub_text_sample, strip_bold_tags
from bionic_reading.transform import transform_text

# Match plain <b>…</b> and classed <b class="bionic">…</b>.
_BOLD_SEGMENT = re.compile(r"(<b(?:\s[^>]*)?>.*?</b>)", re.DOTALL)
_BOLD_INNER = re.compile(r"^<b(?:\s[^>]*)?>|</b>$")


def _echo_bionic(html: str) -> None:
    """Print HTML with <b> tags rendered as terminal bold."""
    pos = 0
    for match in _BOLD_SEGMENT.finditer(html):
        if match.start() > pos:
            typer.echo(html[pos : match.start()], nl=False)
        segment = match.group(0)
        inner = _BOLD_INNER.sub("", segment)
        typer.echo(typer.style(inner, bold=True), nl=False)
        pos = match.end()
    typer.echo(html[pos:])


def print_epub_preview(
    input_path: Path,
    settings: BionicSettings,
    *,
    word_limit: int = 200,
) -> None:
    """Show original vs bionic text from the start of an EPUB.

    Refuses (exit code 1) when the EPUB already has the bionic-epub marker and
    ``settings.skip_if_bionic`` is True. Pass ``--force`` (sets
    ``skip_if_bionic=False``) to preview anyway.
    """
    from bionic_reading.epub_io import ALREADY_BIONIC_MESSAGE, epub_has_bionic_marker

    if settings.skip_if_bionic and epub_has_bionic_marker(input_path):
        typer.secho(ALREADY_BIONIC_MESSAGE, fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    sample, word_count = extract_epub_text_sample(input_path, word_limit)
    if word_count == 0:
        typer.secho("No readable text found in EPUB.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    stats = TransformStats()
    bionic = transform_text(sample, settings, stats)

    typer.echo("")
    typer.secho(f"Preview — {input_path.name}", bold=True)
    typer.echo(
        f"  Fixation {settings.fixation} · Saccade {settings.saccade} · "
        f"{format_count(word_count)} word{'s' if word_count != 1 else ''}"
    )
    typer.echo("")

    typer.secho("Original", fg=typer.colors.BLUE, bold=True)
    typer.echo(sample)
    typer.echo("")

    typer.secho("Bionic", fg=typer.colors.GREEN, bold=True)
    _echo_bionic(bionic)
    typer.echo("")

    typer.secho("Preview stats", fg=typer.colors.BLUE, bold=True)
    typer.echo(f"  Words bolded            {format_count(stats.words_bolded)}")
    if stats.words_saccade_skipped:
        typer.echo(f"  Words skipped (saccade) {format_count(stats.words_saccade_skipped)}")
    typer.echo(f"  Bold tags               {format_count(stats.bold_tags)}")
    typer.echo("")
    typer.secho("No file written. Run without --preview to convert the full EPUB.", fg=typer.colors.CYAN)
