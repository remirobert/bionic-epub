import tempfile
import zipfile
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from bionic_reading.preview import print_epub_preview
from bionic_reading.settings import BionicSettings
from bionic_reading.text_sample import extract_epub_text_sample

pytest.importorskip("ebooklib")

from bionic_reading.cli import main

_cli = typer.Typer(add_completion=False)
_cli.command()(main)


def _write_text_epub(path: Path, paragraphs: list[str], *, already_bionic: bool = False) -> None:
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    marker = '<meta name="bionic-epub" content="1"/>' if already_bionic else ""
    chapter = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter</title>{marker}</head>
  <body>{body}</body>
</html>"""
    container = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">test-book</dc:identifier>
    <dc:title>Test</dc:title>
    <dc:language>fr</dc:language>
  </metadata>
  <manifest>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter"/>
  </spine>
</package>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/chapter.xhtml", chapter)


class TestPreview:
    def test_extract_epub_text_sample_respects_word_limit(self):
        words = [f"mot{i}" for i in range(300)]
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "sample.epub"
            _write_text_epub(epub_path, [" ".join(words)])
            sample, count = extract_epub_text_sample(epub_path, word_limit=200)
            assert count == 200
            assert sample.startswith("mot0 mot1")
            assert sample.endswith("mot199")

    def test_cli_preview_does_not_write_output(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "book.epub"
            out = Path(tmp) / "book-bionic.epub"
            _write_text_epub(src, ["Le petit prince voyage loin."])
            result = runner.invoke(_cli, [str(src), "-o", str(out), "--preview", "--preview-words", "5"])
            assert result.exit_code == 0
            assert "Preview" in result.stdout
            assert "Original" in result.stdout
            assert "Bionic" in result.stdout
            assert "Le petit prince voyage loin" in result.stdout
            assert not out.exists()

    def test_print_epub_preview_french(self, capsys):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "french.epub"
            _write_text_epub(epub_path, ["Bienvenue à Paris, la ville lumière."])
            print_epub_preview(epub_path, BionicSettings(fixation=2, saccade=10), word_limit=10)
            captured = capsys.readouterr()
            assert "Bienvenue" in captured.out
            assert "Preview stats" in captured.out

    def test_preview_refuses_already_bionic_without_force(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            converted = Path(tmp) / "converted.epub"
            _write_text_epub(converted, ["Le petit prince voyage loin."], already_bionic=True)
            result = runner.invoke(_cli, [str(converted), "--preview"])
            assert result.exit_code == 1
            combined = (result.stderr or "") + (result.stdout or "")
            assert "--force" in combined
            assert "original" in combined.lower()

    def test_preview_allows_already_bionic_with_force(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            converted = Path(tmp) / "converted.epub"
            _write_text_epub(converted, ["Le petit prince voyage loin."], already_bionic=True)
            result = runner.invoke(_cli, [str(converted), "--preview", "--force"])
            assert result.exit_code == 0
            assert "Preview" in result.stdout

    def test_cli_convert_refuses_already_bionic_without_force(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            converted = Path(tmp) / "converted.epub"
            again = Path(tmp) / "again.epub"
            _write_text_epub(converted, ["Hello world text here."], already_bionic=True)
            result = runner.invoke(_cli, [str(converted), "-o", str(again)])
            assert result.exit_code == 1
            assert not again.exists()
            combined = (result.stderr or "") + (result.stdout or "")
            assert "--force" in combined
            # Progress line must not appear before a clean refusal.
            assert "Converting" not in (result.stdout or "")

    def test_cli_convert_allows_already_bionic_with_force(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            converted = Path(tmp) / "converted.epub"
            again = Path(tmp) / "again.epub"
            _write_text_epub(converted, ["Hello world text here."], already_bionic=True)
            result = runner.invoke(_cli, [str(converted), "-o", str(again), "--force", "-f", "1"])
            assert result.exit_code == 0, (result.stdout or "") + (result.stderr or "")
            assert again.exists()
            with zipfile.ZipFile(again) as archive:
                # ebooklib may place chapter under EPUB/
                names = [n for n in archive.namelist() if n.endswith("chapter.xhtml")]
                assert names
                output = archive.read(names[0]).decode("utf-8")
            # Force must re-transform body text, not only re-stamp the marker.
            assert '<b class="bionic">Hel</b>lo' in output
