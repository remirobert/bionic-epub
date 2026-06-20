from pathlib import Path

from bionic_reading.stats import TransformResult, TransformStats, format_bytes
from bionic_reading.transform import transform_text
from bionic_reading.settings import BionicSettings


class TestTransformStats:
    def test_records_words_and_bold_chars(self):
        stats = TransformStats()
        transform_text("Reading is fun.", BionicSettings(fixation=1), stats)
        assert stats.words_seen == 3
        assert stats.words_bolded == 3
        assert stats.bold_tags == 3
        assert stats.bold_chars > 0

    def test_skips_pure_numbers(self):
        stats = TransformStats()
        transform_text("12345", BionicSettings(fixation=1), stats)
        assert stats.words_seen == 0
        assert stats.words_bolded == 0

    def test_merge(self):
        left = TransformStats(words_seen=2, words_bolded=1, bold_tags=1, bold_chars=3)
        right = TransformStats(words_seen=1, words_bolded=1, bold_tags=1, bold_chars=4)
        left.merge(right)
        assert left.words_seen == 3
        assert left.bold_chars == 7


class TestTransformResult:
    def test_size_delta_pct(self):
        result = TransformResult(input_bytes=1_000_000, output_bytes=1_007_000)
        assert result.size_delta == 7_000
        assert abs(result.size_delta_pct - 0.7) < 0.01

    def test_lines_include_file_info(self):
        result = TransformResult(
            input_path=Path("/tmp/book.epub"),
            output_path=Path("/tmp/book-bionic.epub"),
            input_bytes=956_000,
            output_bytes=963_000,
            settings_fixation=2,
            stats=TransformStats(words_bolded=100, words_seen=120, bold_tags=100, bold_chars=420),
        )
        text = "\n".join(f"{k}: {v}" for k, v in result.lines())
        assert "book.epub" in text
        assert "933.6 KB" in text
        assert "book-bionic.epub" in text
        assert "Words bolded" in text


class TestFormatBytes:
    def test_formats_kilobytes(self):
        assert format_bytes(956_000) == "933.6 KB"
