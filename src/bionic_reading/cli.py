"""CLI for Bionic Reading text and EPUB conversion."""

from __future__ import annotations

from pathlib import Path

import typer

from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformResult, TransformStats
from bionic_reading.transform import transform_text

app = typer.Typer(
    name="bionic-reading",
    help="Apply Bionic Reading fixation to plain text or EPUB files.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _settings(fixation: int, saccade: int, html: bool) -> BionicSettings:
    from bionic_reading.markers import HtmlBoldMarker, SpaceMarker

    return BionicSettings(
        fixation=fixation,
        saccade=saccade,
        marker=HtmlBoldMarker() if html else SpaceMarker(),
    )


def _print_summary(result: TransformResult, *, quiet: bool) -> None:
    if quiet:
        typer.echo(result.output_path)
        return

    label_width = max(len(label) for label, _ in result.lines())
    typer.echo("")
    typer.secho("✓ Bionic Reading conversion complete", fg=typer.colors.GREEN, bold=True)
    typer.echo("")
    for label, value in result.lines():
        typer.echo(f"  {label:<{label_width}}  {value}")
    typer.echo("")
    typer.secho(f"Written to: {result.output_path}", fg=typer.colors.CYAN)


def _print_text_stats(stats: TransformStats, fixation: int, saccade: int, *, quiet: bool) -> None:
    if quiet:
        return
    result = TransformResult(
        settings_fixation=fixation,
        settings_saccade=saccade,
        stats=stats,
    )
    rows = [
        row for row in result.lines()
        if row[0] not in {"Input", "Output", "Size change", "Documents", "Text nodes changed"}
    ]
    label_width = max(len(label) for label, _ in rows)
    typer.echo("", err=True)
    typer.secho("Stats", fg=typer.colors.BLUE, bold=True, err=True)
    for label, value in rows:
        typer.echo(f"  {label:<{label_width}}  {value}", err=True)


@app.command("transform")
def transform_command(
    text: str = typer.Argument(..., help="Plain text to transform."),
    fixation: int = typer.Option(1, "--fixation", "-f", min=1, max=5, help="Fixation strength (1=heaviest, 5=lightest)."),
    saccade: int = typer.Option(
        10,
        "--saccade",
        "-s",
        min=10,
        max=50,
        help="Gap between bold words (10 = dense, 50 = sparse).",
    ),
    html: bool = typer.Option(True, "--html/--plain", help="Wrap fixation in <b> tags."),
    stats: bool = typer.Option(False, "--stats", help="Print conversion stats to stderr."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress informational output."),
) -> None:
    """Transform a text snippet and print the result."""
    settings = _settings(fixation, saccade, html)
    transform_stats = TransformStats() if stats else None
    output = transform_text(text, settings, transform_stats)
    typer.echo(output)
    if stats and transform_stats is not None:
        _print_text_stats(transform_stats, fixation, saccade, quiet=quiet)


@app.command("epub")
def epub_command(
    input: Path = typer.Argument(..., exists=True, dir_okay=False, help="Input EPUB file."),
    output: Path | None = typer.Argument(
        None,
        dir_okay=False,
        help="Output EPUB file (default: same name with '-bionic' before the extension).",
    ),
    fixation: int = typer.Option(2, "--fixation", "-f", min=1, max=5, help="Fixation strength (1=heaviest, 5=lightest)."),
    saccade: int = typer.Option(
        10,
        "--saccade",
        "-s",
        min=10,
        max=50,
        help="Gap between bold words (10 = dense, 50 = sparse).",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only print the output path."),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Preview the first words of the EPUB without writing output.",
    ),
    preview_words: int = typer.Option(
        200,
        "--preview-words",
        min=1,
        help="Number of words to show with --preview.",
    ),
) -> None:
    """Convert an EPUB by inserting Bionic Reading bold tags into body text."""
    from bionic_reading.epub_io import transform_epub
    from bionic_reading.paths import bionic_output_path
    from bionic_reading.preview import print_epub_preview

    settings = _settings(fixation, saccade, html=True)

    if preview:
        print_epub_preview(input, settings, word_limit=preview_words)
        return

    destination = output or bionic_output_path(input)
    if not quiet:
        typer.echo(f"Converting {input.name} → {destination.name} …")

    result = transform_epub(input, destination, settings)
    _print_summary(result, quiet=quiet)


if __name__ == "__main__":
    app()
