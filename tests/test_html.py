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

    def test_word_split_across_lang_only_spans_gets_continuous_bold(self):
        """Word exports often wrap each accented letter in its own lang span.

        Without merging those fragments, fixation is applied per letter and the
        bold range is broken inside a single word (e.g. éléments).
        """
        html = (
            "<html><body><p>"
            '<span lang="FR">plusieurs </span>'
            '<span lang="FR">é</span>'
            '<span lang="FR">l</span>'
            '<span lang="FR">é</span>'
            '<span lang="FR">ments baroques</span>'
            "</p></body></html>"
        )
        result = transform_html_document(html, BionicSettings(fixation=2))
        assert "<b>éléme</b>nts" in result
        # Must not bold each letter fragment independently.
        assert result.count("<b>é</b>") == 0
        assert "<b>l</b>" not in result

    def test_styled_spans_are_preserved(self):
        html = (
            '<html><body><p>See <span class="note">footnote</span> here.</p></body></html>'
        )
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert 'class="note"' in result
        assert '<span class="note">' in result
        assert "<b>footno</b>te" in result

    def test_soft_hyphen_mid_word_gets_continuous_bold(self):
        """Soft hyphens (U+00AD) must not split a word into separate fixation tokens."""
        soft = "\u00ad"
        html = f"<html><body><p>La plan{soft}ète.</p></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>planè</b>te" in result
        # Must not bold the halves independently around a leftover soft hyphen.
        assert f"<b>pla</b>n{soft}" not in result
        assert soft not in result

    def test_zero_width_chars_do_not_split_fixation_tokens(self):
        """Zero-width space/joiner/non-joiner/BOM must be stripped before fixation."""
        for junk in ("\u200b", "\u200c", "\u200d", "\ufeff"):
            html = f"<html><body><p>La plan{junk}ète.</p></body></html>"
            result = transform_html_document(html, BionicSettings(fixation=1))
            assert "<b>planè</b>te" in result, f"failed for {junk!r}"
            assert junk not in result
            assert "<b>pla</b>n" not in result

    def test_break_junk_preserved_in_skipped_containers_and_ancestors(self):
        """Soft hyphens must remain inside code/pre/strong/headings (skip set)."""
        soft = "\u00ad"
        zwsp = "\u200b"
        html = (
            "<html><body>"
            f"<p>Body plan{soft}ète ok.</p>"
            f"<pre>code plan{soft}ète</pre>"
            f"<p><code>inline{zwsp}word</code></p>"
            f"<p><strong>bold{soft}word</strong></p>"
            f"<h1>Head{soft}ing</h1>"
            "</body></html>"
        )
        result = transform_html_document(html, BionicSettings(fixation=1))
        # Body text is stripped and continuously bolded.
        assert "<b>planè</b>te" in result
        # Skip containers / ancestors keep break junk intact and untransformed.
        assert f"<pre>code plan{soft}ète</pre>" in result
        assert f"<code>inline{zwsp}word</code>" in result
        assert f"<strong>bold{soft}word</strong>" in result
        assert f"<h1>Head{soft}ing</h1>" in result

    def test_lang_spans_plus_soft_hyphen_get_continuous_bold(self):
        """Lang-only unwrap + soft-hyphen strip combine into one fixation token."""
        soft = "\u00ad"
        html = (
            "<html><body><p>"
            f'<span lang="FR">plan{soft}</span>'
            '<span lang="FR">ète</span>'
            "</p></body></html>"
        )
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert "<b>planè</b>te" in result
        assert soft not in result
        assert result.count("<b>pla</b>") == 0

    def test_comments_with_break_junk_are_not_demoted_to_text(self):
        """Comments containing soft hyphens must stay comments, not body text."""
        soft = "\u00ad"
        html = f"<html><body><p>Hello.</p><!-- plan{soft}ète --></body></html>"
        result = transform_html_document(html, BionicSettings(fixation=1))
        assert f"<!-- plan{soft}ète -->" in result
        # Soft-hyphenated comment content must not leak as transformed body text.
        assert "<b>planè</b>te" not in result
