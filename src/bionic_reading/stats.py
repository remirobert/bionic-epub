"""Conversion statistics collected during Bionic Reading transforms."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def format_bytes(size: int) -> str:
    """Human-readable byte size."""
    if size < 0:
        return f"-{format_bytes(-size)}"
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def format_count(value: int) -> str:
    return f"{value:,}"


@dataclass
class TransformStats:
    """Counters accumulated while transforming text or HTML."""

    words_seen: int = 0
    words_bolded: int = 0
    words_saccade_skipped: int = 0
    bold_tags: int = 0
    bold_chars: int = 0
    text_nodes_changed: int = 0
    documents_processed: int = 0

    def record_word(self, word: str, bold_len: int, *, saccade_skipped: bool = False) -> None:
        self.words_seen += 1
        if saccade_skipped:
            self.words_saccade_skipped += 1
            return
        if bold_len <= 0:
            return
        self.words_bolded += 1
        self.bold_tags += 1
        self.bold_chars += bold_len

    def merge(self, other: TransformStats) -> None:
        self.words_seen += other.words_seen
        self.words_bolded += other.words_bolded
        self.words_saccade_skipped += other.words_saccade_skipped
        self.bold_tags += other.bold_tags
        self.bold_chars += other.bold_chars
        self.text_nodes_changed += other.text_nodes_changed
        self.documents_processed += other.documents_processed

    @property
    def avg_bold_chars(self) -> float:
        if self.words_bolded == 0:
            return 0.0
        return self.bold_chars / self.words_bolded

    @property
    def bold_word_ratio(self) -> float:
        if self.words_seen == 0:
            return 0.0
        return self.words_bolded / self.words_seen


@dataclass
class TransformResult:
    """Outcome of an EPUB or text conversion."""

    input_path: Path | None = None
    output_path: Path | None = None
    input_bytes: int = 0
    output_bytes: int = 0
    settings_fixation: int = 1
    settings_saccade: int = 10
    stats: TransformStats = field(default_factory=TransformStats)

    @property
    def size_delta(self) -> int:
        return self.output_bytes - self.input_bytes

    @property
    def size_delta_pct(self) -> float:
        if self.input_bytes == 0:
            return 0.0
        return (self.size_delta / self.input_bytes) * 100

    def lines(self) -> list[tuple[str, str]]:
        """Key/value rows for CLI rendering."""
        rows: list[tuple[str, str]] = []
        if self.input_path is not None:
            rows.append(("Input", f"{self.input_path.name} ({format_bytes(self.input_bytes)})"))
        if self.output_path is not None:
            rows.append(("Output", f"{self.output_path.name} ({format_bytes(self.output_bytes)})"))
        if self.input_bytes and self.output_bytes:
            sign = "+" if self.size_delta >= 0 else ""
            rows.append(("Size change", f"{sign}{format_bytes(self.size_delta)} ({sign}{self.size_delta_pct:.1f}%)"))
        rows.append(("Fixation", str(self.settings_fixation)))
        rows.append(("Saccade", str(self.settings_saccade)))
        rows.append(("Documents", format_count(self.stats.documents_processed)))
        rows.append(("Text nodes changed", format_count(self.stats.text_nodes_changed)))
        rows.append(("Words processed", format_count(self.stats.words_seen)))
        rows.append(("Words bolded", format_count(self.stats.words_bolded)))
        if self.stats.words_saccade_skipped:
            rows.append(("Words skipped (saccade)", format_count(self.stats.words_saccade_skipped)))
        rows.append(("Bold tags added", format_count(self.stats.bold_tags)))
        rows.append(("Bold characters", format_count(self.stats.bold_chars)))
        if self.stats.words_bolded:
            rows.append(("Avg bold / word", f"{self.stats.avg_bold_chars:.1f} chars"))
            rows.append(("Bold coverage", f"{self.stats.bold_word_ratio * 100:.1f}% of words"))
        return rows
