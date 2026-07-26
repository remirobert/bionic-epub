from bionic_reading.text_sample import extract_readable_text, take_words, strip_bold_tags


class TestTextSample:
    def test_take_words_limits_count(self):
        text = "one two three four five six"
        sample, count = take_words(text, 3)
        assert sample == "one two three"
        assert count == 3

    def test_take_words_fewer_than_limit(self):
        sample, count = take_words("hello world", 200)
        assert sample == "hello world"
        assert count == 2

    def test_extract_readable_text_skips_pre(self):
        html = "<html><body><p>Hello world.</p><pre>ignored</pre></body></html>"
        assert extract_readable_text(html) == "Hello world."

    def test_extract_readable_text_preserves_french(self):
        html = "<html><body><p>Bienvenue à Paris.</p></body></html>"
        assert extract_readable_text(html) == "Bienvenue à Paris."

    def test_strip_bold_tags(self):
        assert strip_bold_tags("<b>read</b>ing") == "reading"
        assert strip_bold_tags('<b class="bionic">read</b>ing') == "reading"
