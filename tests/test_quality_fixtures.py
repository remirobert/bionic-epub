"""Golden quality fixtures for messy real-world HTML edge cases.

Fixtures live under tests/fixtures/quality/. Assertions use stable substrings
(not full-document equality) because BeautifulSoup serialization can vary.
"""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from bionic_reading.html import has_bionic_css, has_bionic_marker, transform_html_document
from bionic_reading.settings import BionicSettings

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "quality"


def _load(name: str) -> str:
    path = FIXTURES / name
    return path.read_text(encoding="utf-8")


class TestQualityFixtures:
    def test_fixture_files_exist(self):
        expected = {
            "word_style_elements.html",
            "soft_hyphen.html",
            "already_bionic.html",
            "clean_control.html",
        }
        present = {p.name for p in FIXTURES.iterdir() if p.is_file()}
        assert expected <= present

    def test_word_style_elements_gets_continuous_bold(self):
        """Word-style lang-only spans around *éléments* must merge into one token."""
        html = _load("word_style_elements.html")
        # Require mid-word Word fragmentation in the body (not just <html lang=…>).
        assert '<span lang="FR">é</span>' in html
        assert '<span lang="FR">l</span>' in html
        assert html.count('lang="FR"') >= 3

        result = transform_html_document(html, BionicSettings(fixation=2))
        assert '<b class="bionic">éléme</b>nts' in result
        # Must not bold each letter fragment independently.
        assert result.count('<b class="bionic">é</b>') == 0
        assert '<b class="bionic">l</b>' not in result
        # Language-only mid-word spans are unwrapped during normalize.
        assert '<span lang="FR">' not in result
        assert has_bionic_marker(BeautifulSoup(result, "html.parser"))

    def test_soft_hyphen_mid_word_gets_continuous_bold(self):
        """Soft hyphen (U+00AD) mid-word must be stripped so fixation sees one token."""
        soft = "\u00ad"
        html = _load("soft_hyphen.html")
        assert soft in html  # fixture contains the soft hyphen

        result = transform_html_document(html, BionicSettings(fixation=1))
        assert '<b class="bionic">planè</b>te' in result
        assert soft not in result
        # No bold boundary splitting plan|ète after strip.
        assert '<b class="bionic">pla</b>n' not in result

    def test_already_bionic_has_marker(self):
        """Minimal already-bionic fixture is detectable via the meta marker only."""
        html = _load("already_bionic.html")
        soup = BeautifulSoup(html, "html.parser")
        assert has_bionic_marker(soup)
        assert has_bionic_css(soup)
        # Already-bolded content is present as a stable substring.
        assert '<b class="bionic">Readi</b>ng' in html
        assert 'name="bionic-epub"' in html
        assert 'content="1"' in html

    def test_clean_control_paragraph(self):
        """Clean control needs no normalize and gets ordinary continuous bold."""
        html = _load("clean_control.html")
        # No language-only spans or soft hyphens in the control fixture.
        assert "lang=" not in html
        assert "\u00ad" not in html
        assert 'name="bionic-epub"' not in html

        result = transform_html_document(html, BionicSettings(fixation=1))
        assert '<b class="bionic">Readi</b>ng' in result
        assert '<b class="bionic">i</b>s' in result
        assert '<b class="bionic">fu</b>n' in result
        assert has_bionic_marker(BeautifulSoup(result, "html.parser"))
        assert has_bionic_css(BeautifulSoup(result, "html.parser"))
