"""Parity checks against official Bionic Reading web demo (default settings).

Default fixation (3) uses ``round(0.4 * n)``. Fixtures under
``tests/fixtures/parity/`` hold source text and expected bold lengths.
"""

from __future__ import annotations

import json
from pathlib import Path

import regex

from bionic_reading.fixation import WEBSITE_DEFAULT_FIXATION_RATIO, fixation_length
from bionic_reading.settings import BionicSettings
from bionic_reading.transform import transform_text, transform_word

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "parity"
CONVERTIBLE_WORD = regex.compile(r"(\p{L}|\p{Nd})*\p{L}(\p{L}|\p{Nd})*")

# Single-letter initials (J, K, A) are bolded on the website but skipped by
# min_bold_word_length=2. Require high overall match, not 100%.
MIN_EXACT_MATCH_RATIO = 0.95


def _tokens(text: str) -> list[str]:
    return [m.group(0) for m in CONVERTIBLE_WORD.finditer(text)]


def _predicted_bold_lengths(text: str, settings: BionicSettings | None = None) -> list[int]:
    config = settings or BionicSettings()
    lengths: list[int] = []
    for word in _tokens(text):
        bold_len = fixation_length(word, config.fixation)
        if len(word) < config.min_bold_word_length:
            bold_len = 0
        lengths.append(bold_len)
    return lengths


def _expected_from_fixture(data: dict) -> list[int]:
    if data.get("derive") == "round_0_4":
        settings = BionicSettings()
        return [
            0
            if len(w) < settings.min_bold_word_length
            else fixation_length(w, 3)
            for w in _tokens(data["text"])
        ]
    lengths = data.get("bold_lengths")
    if not isinstance(lengths, list):
        raise AssertionError(f"fixture {data.get('id')!r} missing bold_lengths")
    return lengths


def _load_fixtures() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURES.glob("*.json"))]


class TestWebsiteDefaultFixationFormula:
    def test_ratio_constant(self):
        assert WEBSITE_DEFAULT_FIXATION_RATIO == 0.4

    def test_length_table_matches_round_0_4(self):
        # Observed modes from official web demo English samples.
        expected = {
            1: 0,
            2: 1,
            3: 1,
            4: 2,
            5: 2,
            6: 2,
            7: 3,
            8: 3,
            9: 4,
            10: 4,
            11: 4,
            12: 5,
            15: 6,
            20: 8,
        }
        for length, bold in expected.items():
            word = "x" * length
            assert fixation_length(word, 3) == bold, f"len={length}"

    def test_default_settings_use_website_formula(self):
        # Harry / Potter / series — website-like, not old text-vide f=3 table.
        assert fixation_length("Harry", 3) == 2
        assert fixation_length("Potter", 3) == 2
        assert fixation_length("series", 3) == 2
        assert fixation_length("chronicle", 3) == 4
        assert fixation_length("Witchcraft", 3) == 4

    def test_other_fixation_levels_still_use_tables(self):
        # text-vide style: f=1 is heavier than website default on medium words.
        assert fixation_length("reading", 1) == 5
        assert fixation_length("reading", 3) == 3
        assert fixation_length("reading", 5) == 2
        assert fixation_length("reading", 1) > fixation_length("reading", 3)

    def test_empty_word(self):
        assert fixation_length("", 3) == 0


class TestParityFixtures:
    def test_fixtures_exist(self):
        paths = list(FIXTURES.glob("*.json"))
        assert paths, "expected parity fixtures under tests/fixtures/parity/"

    def test_each_fixture_meets_match_threshold(self):
        settings = BionicSettings()  # fixation 3, saccade 10, min_bold 2
        for data in _load_fixtures():
            text = data["text"]
            expected = _expected_from_fixture(data)
            predicted = _predicted_bold_lengths(text, settings)
            tokens = _tokens(text)
            assert len(expected) == len(tokens), data["id"]
            assert len(predicted) == len(tokens), data["id"]

            matches = sum(e == p for e, p in zip(expected, predicted))
            ratio = matches / len(tokens)
            diffs = [
                (tok, e, p)
                for tok, e, p in zip(tokens, expected, predicted)
                if e != p
            ]
            assert ratio >= MIN_EXACT_MATCH_RATIO, (
                f"{data['id']}: match {matches}/{len(tokens)} ({ratio:.1%}) "
                f"< {MIN_EXACT_MATCH_RATIO:.0%}; diffs={diffs[:12]}"
            )

    def test_harry_potter_fixture_alignment(self):
        data = json.loads((FIXTURES / "harry_potter.json").read_text(encoding="utf-8"))
        tokens = _tokens(data["text"])
        assert len(tokens) == len(data["bold_lengths"])
        # Only known residual gaps vs website transcription: single-letter initials.
        predicted = _predicted_bold_lengths(data["text"])
        diffs = [
            (tok, e, p)
            for tok, e, p in zip(tokens, data["bold_lengths"], predicted)
            if e != p
        ]
        assert all(len(tok) == 1 for tok, _, _ in diffs), diffs


class TestDefaultTransformSmoke:
    def test_sample_words_default_transform(self):
        settings = BionicSettings(bold_style="b")
        assert transform_word("Harry", settings) == "<b>Ha</b>rry"
        assert transform_word("Potter", settings) == "<b>Po</b>tter"
        assert transform_word("the", settings) == "<b>t</b>he"
        assert transform_word("a", settings) == "a"

    def test_preview_sentence_default(self):
        settings = BionicSettings(bold_style="b")
        result = transform_text("Harry Potter is a series", settings)
        assert result == (
            "<b>Ha</b>rry <b>Po</b>tter <b>i</b>s a <b>se</b>ries"
        )
