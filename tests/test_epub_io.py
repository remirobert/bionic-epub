from pathlib import Path

from bionic_reading.paths import bionic_output_path


class TestBionicOutputPath:
    def test_appends_bionic_before_extension(self):
        assert bionic_output_path(Path("/books/novel.epub")) == Path("/books/novel-bionic.epub")

    def test_preserves_directory_and_suffix(self):
        assert bionic_output_path(Path("my book.epub")) == Path("my book-bionic.epub")
