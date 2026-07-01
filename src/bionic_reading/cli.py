"""CLI for Bionic Reading EPUB conversion."""

from __future__ import annotations

from pathlib import Path

import typer

from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformResult


def _settings(fixation: int, saccade: int) -> BionicSettings:
    from bionic_reading.markers import HtmlBoldMarker

    return BionicSettings(
        fixation=fixation,
        saccade=saccade,
        marker=HtmlBoldMarker(),
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


def main(
    epub: Path = typer.Argument(..., exists=True, dir_okay=False, help="EPUB file to convert."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        dir_okay=False,
        help="Output path (default: same name with '-bionic' before the extension).",
    ),
    fixation: int = typer.Option(3, "--fixation", "-f", min=1, max=5, help="Bold strength (1–5)."),
    saccade: int = typer.Option(
        10,
        "--saccade",
        "-s",
        min=10,
        max=50,
        help="Spacing between bold words (10 = every word, 50 = sparse).",
    ),
    preview: bool = typer.Option(False, "--preview", help="Preview the first words without writing a file."),
    preview_words: int = typer.Option(200, "--preview-words", min=1, help="Words to show with --preview."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only print the output path."),
) -> None:
    """Convert an EPUB to Bionic Reading format."""
    from bionic_reading.epub_io import transform_epub
    from bionic_reading.paths import bionic_output_path
    from bionic_reading.preview import print_epub_preview

    settings = _settings(fixation, saccade)

    if preview:
        print_epub_preview(epub, settings, word_limit=preview_words)
        return

    destination = output or bionic_output_path(epub)
    if not quiet:
        typer.echo(f"Converting {epub.name} → {destination.name} …")

    result = transform_epub(epub, destination, settings)
    _print_summary(result, quiet=quiet)


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()