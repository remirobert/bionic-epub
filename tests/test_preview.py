import tempfile
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bionic_reading.preview import print_epub_preview
from bionic_reading.settings import BionicSettings
from bionic_reading.text_sample import extract_epub_text_sample

pytest.importorskip("ebooklib")

from bionic_reading.cli import app


def _write_text_epub(path: Path, paragraphs: list[str]) -> None:
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    chapter = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter</title></head>
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
            result = runner.invoke(app, ["epub", str(src), str(out), "--preview", "--preview-words", "5"])
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
