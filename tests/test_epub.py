"""EPUB integration tests (skipped when ebooklib is unavailable)."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("ebooklib")

from bionic_reading.epub_io import AlreadyBionicError, transform_epub
from bionic_reading.html import has_bionic_marker
from bionic_reading.settings import BionicSettings
from bs4 import BeautifulSoup


def _write_minimal_epub(path: Path, chapter_html: str) -> None:
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
    <dc:language>en</dc:language>
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
        archive.writestr("OEBPS/chapter.xhtml", chapter_html)


def _write_epub3_with_nav_and_ncx(path: Path, chapter_html: str) -> None:
    """Minimal EPUB3 whose nav TOC yields ebooklib Links without uid (plus legacy NCX)."""
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
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter"/>
  </spine>
</package>"""
    nav = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>TOC</title></head>
  <body>
    <nav epub:type="toc" id="toc">
      <ol>
        <li><a href="chapter.xhtml#intro">Introduction</a></li>
        <li>
          <span>Part One</span>
          <ol>
            <li><a href="chapter.xhtml#sec1">Section One</a></li>
          </ol>
        </li>
      </ol>
    </nav>
  </body>
</html>"""
    ncx = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="test-book"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>Test</text></docTitle>
  <navMap>
    <navPoint id="navPoint-1">
      <navLabel><text>Introduction</text></navLabel>
      <content src="chapter.xhtml#intro"/>
    </navPoint>
  </navMap>
</ncx>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/nav.xhtml", nav)
        archive.writestr("OEBPS/toc.ncx", ncx)
        archive.writestr("OEBPS/chapter.xhtml", chapter_html)


class TestEpubIo:
    def test_transform_epub_writes_bionic_html(self):
        chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter</title></head>
  <body>
    <p>Reading is fun.</p>
    <pre>Reading is fun.</pre>
  </body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "input.epub"
            dst = Path(tmp) / "output.epub"
            _write_minimal_epub(src, chapter)
            transform_epub(src, dst, BionicSettings(fixation=1))
            assert dst.exists()
            with zipfile.ZipFile(dst) as archive:
                output = archive.read("EPUB/chapter.xhtml").decode("utf-8")
            assert "<b>Readi</b>ng" in output
            assert "<pre>Reading is fun.</pre>" in output
            assert has_bionic_marker(BeautifulSoup(output, "html.parser"))
            # Plain <b> only — no class or injected CSS.
            assert "b.bionic" not in output
            assert "font-weight: 700" not in output
            assert "data-bionic-epub" not in output

    def test_transform_epub_writes_nav_toc_with_legacy_ncx(self):
        chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter</title></head>
  <body>
    <p id="intro">Reading is fun.</p>
    <p id="sec1">More text.</p>
  </body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "input.epub"
            dst = Path(tmp) / "output.epub"
            _write_epub3_with_nav_and_ncx(src, chapter)
            transform_epub(src, dst, BionicSettings(fixation=1))
            assert dst.exists()
            with zipfile.ZipFile(dst) as archive:
                output = archive.read("EPUB/chapter.xhtml").decode("utf-8")
            assert "<b>Readi</b>ng" in output
            assert has_bionic_marker(BeautifulSoup(output, "html.parser"))
            assert "b.bionic" not in output
            assert "font-weight: 700" not in output

    def test_second_run_aborts_without_force_and_writes_nothing(self):
        # Source already carries the marker (as a prior bionic-epub output would).
        chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Chapter</title>
    <meta name="bionic-epub" content="1"/>
  </head>
  <body><p><b>Readi</b>ng is fun.</p></body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "already.epub"
            dst = Path(tmp) / "second.epub"
            _write_minimal_epub(src, chapter)

            with pytest.raises(AlreadyBionicError, match="--force"):
                transform_epub(src, dst, BionicSettings(fixation=1))
            assert not dst.exists()

    def test_force_reconvert_writes_output(self):
        chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Chapter</title>
    <meta name="bionic-epub" content="1"/>
  </head>
  <body><p>Reading is fun.</p></body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "already.epub"
            dst = Path(tmp) / "forced.epub"
            _write_minimal_epub(src, chapter)
            transform_epub(
                src,
                dst,
                BionicSettings(fixation=1, skip_if_bionic=False),
            )
            assert dst.exists()
            with zipfile.ZipFile(dst) as archive:
                output = archive.read("EPUB/chapter.xhtml").decode("utf-8")
            assert has_bionic_marker(BeautifulSoup(output, "html.parser"))
            # Only one marker even after force re-run.
            assert output.count('name="bionic-epub"') == 1
            # Force must actually re-transform, not only re-stamp the marker.
            assert "<b>Readi</b>ng" in output
            assert "b.bionic" not in output
            assert "font-weight: 700" not in output

    def test_round_trip_detects_marker_from_own_output(self):
        """Marker written via ebooklib add_meta is visible on re-read (nav+ncx EPUB)."""
        chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter</title></head>
  <body>
    <p id="intro">Reading is fun.</p>
    <p id="sec1">More text.</p>
  </body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "input.epub"
            first = Path(tmp) / "first.epub"
            second = Path(tmp) / "second.epub"
            _write_epub3_with_nav_and_ncx(src, chapter)
            transform_epub(src, first, BionicSettings(fixation=1))
            with pytest.raises(AlreadyBionicError, match="--force"):
                transform_epub(first, second, BionicSettings(fixation=1))
            assert not second.exists()
            # Force re-convert of our own output still works.
            transform_epub(
                first,
                second,
                BionicSettings(fixation=1, skip_if_bionic=False),
            )
            assert second.exists()

    def test_marker_in_any_content_doc_aborts_whole_book(self):
        """If any spine document is marked, the whole book is refused."""
        plain = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>A</title></head>
  <body><p>Plain chapter.</p></body>
</html>"""
        marked = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>B</title>
    <meta name="bionic-epub" content="1"/>
  </head>
  <body><p>Already converted.</p></body>
</html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "mixed.epub"
            dst = Path(tmp) / "out.epub"
            _write_two_chapter_epub(src, plain, marked)
            with pytest.raises(AlreadyBionicError):
                transform_epub(src, dst, BionicSettings(fixation=1))
            assert not dst.exists()


def _write_two_chapter_epub(path: Path, chapter_a: str, chapter_b: str) -> None:
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
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>
    <item id="b" href="b.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="a"/>
    <itemref idref="b"/>
  </spine>
</package>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/a.xhtml", chapter_a)
        archive.writestr("OEBPS/b.xhtml", chapter_b)
