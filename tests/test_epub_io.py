from pathlib import Path

from bionic_reading.epub_io import ALREADY_BIONIC_MESSAGE, AlreadyBionicError, document_has_bionic_marker
from bionic_reading.paths import bionic_output_path
from bionic_reading.settings import BionicSettings


class TestBionicOutputPath:
    def test_appends_bionic_before_extension(self):
        assert bionic_output_path(Path("/books/novel.epub")) == Path("/books/novel-bionic.epub")

    def test_preserves_directory_and_suffix(self):
        assert bionic_output_path(Path("my book.epub")) == Path("my book-bionic.epub")


class TestAlreadyBionicDetection:
    def test_document_has_bionic_marker_true(self):
        html = '<html><head><meta name="bionic-epub" content="1"/></head><body></body></html>'
        assert document_has_bionic_marker(html) is True

    def test_document_has_bionic_marker_false(self):
        html = "<html><head><title>x</title></head><body><p>hi</p></body></html>"
        assert document_has_bionic_marker(html) is False

    def test_settings_skip_if_bionic_default_true(self):
        assert BionicSettings().skip_if_bionic is True

    def test_settings_force_via_skip_if_bionic_false(self):
        assert BionicSettings(skip_if_bionic=False).skip_if_bionic is False

    def test_error_message_mentions_force_and_original(self):
        err = AlreadyBionicError()
        msg = str(err)
        assert msg == ALREADY_BIONIC_MESSAGE
        assert "--force" in msg
        assert "original" in msg.lower()
