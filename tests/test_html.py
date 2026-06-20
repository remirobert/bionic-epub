from bionic_reading.html import transform_html_document
from bionic_reading.settings import BionicSettings


class TestHtmlTransform:
    def test_paragraph_text(self):
        html = "<html><body><p>Reading is fun.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<p><b>Readi</b>ng <b>i</b>s <b>fu</b>n.</p>" in result

    def test_french_accents(self):
        html = "<html><body><p>Bienvenue à Paris.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>Bienven</b>ue" in result
        assert "<b>Par</b>is" in result

    def test_skips_code_blocks(self):
        html = "<html><body><p>Hello world.</p><pre>Hello world.</pre></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>Hel</b>lo" in result
        assert "<pre>Hello world.</pre>" in result

    def test_skips_existing_bold(self):
        html = "<html><body><p>Normal and <strong>bold</strong> text.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>Norm</b>al" in result
        assert "<strong>bold</strong>" in result

    def test_skips_headings(self):
        html = "<html><body><h1>Chapter One</h1><p>Body text.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<h1>Chapter One</h1>" in result
        assert "<b>Bod</b>y" in result

    def test_preserves_inline_markup(self):
        html = "<html><body><p>Read <em>more</em> books.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>Rea</b>d" in result
        assert "<em><b>mor</b>e</em>" in result

    def test_hyphenated_word_in_paragraph(self):
        html = "<html><body><p>It was well-known.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>wel</b>l-<b>kno</b>wn" in result

    def test_numbers_unchanged(self):
        html = "<html><body><p>Flight 123 landed.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "123" in result
        assert "<b>123</b>" not in result
        assert "<b>Flig</b>ht" in result
