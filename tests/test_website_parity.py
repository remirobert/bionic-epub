"""Parity checks against official Bionic Reading web demo (default settings).

Default fixation (3) uses ``round(0.4 * n)``. Fixtures under
``tests/fixtures/parity/`` hold source text and expected bold lengths
transcribed from the public demo (not derived from this codebase).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bionic_reading.fixation import WEBSITE_DEFAULT_FIXATION_RATIO, fixation_length
from bionic_reading.settings import BionicSettings
from bionic_reading.transform import CONVERTIBLE_WORD, transform_text, transform_word

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "parity"

# Single-letter initials (J, K, A) are bolded on the website but skipped by
# min_bold_word_length=2. Require high overall match, not 100%.
MIN_EXACT_MATCH_RATIO = 0.95

# Plain <b>…</b> prefix produced by bold_style="b".
_PLAIN_BOLD_PREFIX = re.compile(r"^<b>(.*?)</b>", re.DOTALL)


def _tokens(text: str) -> list[str]:
    return [m.group(0) for m in CONVERTIBLE_WORD.finditer(text)]


def _settings_for_scoring() -> BionicSettings:
    """Default fixation/saccade/min-bold, plain marker for easy bold-length parse."""
    return BionicSettings(bold_style="b")


def _bold_len_from_transform_word(word: str, settings: BionicSettings) -> int:
    """Bold length via production ``transform_word`` (not a parallel formula path)."""
    out = transform_word(word, settings)
    if out == word:
        return 0
    match = _PLAIN_BOLD_PREFIX.match(out)
    if not match:
        return 0
    return len(match.group(1))


def _predicted_bold_lengths(text: str, settings: BionicSettings | None = None) -> list[int]:
    config = settings or _settings_for_scoring()
    return [_bold_len_from_transform_word(word, config) for word in _tokens(text)]


def _expected_from_fixture(data: dict) -> list[int]:
    lengths = data.get("bold_lengths")
    if not isinstance(lengths, list):
        raise AssertionError(
            f"fixture {data.get('id')!r} must include transcribed bold_lengths "
            "(derive/self-check fixtures are not allowed)"
        )
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

    def test_level_3_not_in_boundary_tables(self):
        from bionic_reading.fixation import FIXATION_BOUNDARIES

        assert 3 not in FIXATION_BOUNDARIES

    def test_empty_word(self):
        assert fixation_length("", 3) == 0


class TestParityFixtures:
    def test_fixtures_exist(self):
        paths = list(FIXTURES.glob("*.json"))
        assert len(paths) >= 2, "expected at least two independent parity fixtures"
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(data.get("bold_lengths"), list), path.name
            assert "derive" not in data, f"{path.name} must not use self-derived expectations"

    def test_each_fixture_meets_match_threshold(self):
        settings = _settings_for_scoring()
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

    def test_harry_potter_residual_diffs_are_single_letter(self):
        data = json.loads((FIXTURES / "harry_potter.json").read_text(encoding="utf-8"))
        tokens = _tokens(data["text"])
        assert len(tokens) == len(data["bold_lengths"])
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
