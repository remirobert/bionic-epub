from bionic_reading import fixation_length, transform_text, transform_text_spaced
from bionic_reading.settings import BionicSettings
from bionic_reading.markers import HtmlBoldMarker, SpaceMarker


class TestFixationLength:
    def test_short_words_fixation_1(self):
        assert fixation_length("is", 1) == 1
        assert fixation_length("the", 1) == 2
        assert fixation_length("reading", 1) == 5

    def test_single_character_is_not_bolded(self):
        assert fixation_length("a", 1) == 0

    def test_medium_words_fixation_1(self):
        assert fixation_length("Bionic", 1) == 4
        assert fixation_length("understanding", 1) == 10

    def test_fixation_5_is_lighter(self):
        assert fixation_length("text", 5) == 1
        assert fixation_length("reading", 5) < fixation_length("reading", 1)

    def test_invalid_fixation_falls_back_to_level_1(self):
        assert fixation_length("reading", 99) == fixation_length("reading", 1)


class TestEnglishReference:
    PARAGRAPH = (
        "Bionic Reading is a new method facilitating the reading process by guiding the eyes "
        "through text with artificial fixation points."
    )

    def test_paragraph_fixation_1_html(self):
        result = transform_text(self.PARAGRAPH, BionicSettings(fixation=1))
        assert result.startswith("<b>Bion</b>ic <b>Readi</b>ng")
        assert "<b>fixati</b>on" in result

    def test_paragraph_fixation_2_html(self):
        result = transform_text(self.PARAGRAPH, BionicSettings(fixation=2))
        assert "<b>Bion</b>ic" in result
        assert "<b>facilita</b>ting" in result

    def test_html_markers(self):
        assert transform_text("reading", BionicSettings(fixation=1)) == "<b>readi</b>ng"

    def test_pure_numbers_unchanged(self):
        assert transform_text_spaced("1234567890") == "1234567890"
        assert transform_text_spaced("1234-567890") == "1234-567890"

    def test_mixed_alphanumeric(self):
        assert transform_text_spaced("a1234567890") == "a12345678 90"
        assert transform_text_spaced("1234567890a") == "123456789 0a"

    def test_hyphenated_words(self):
        assert transform_text_spaced("round-the-world") == "rou nd-th e-wor ld"

    def test_empty_and_single_char(self):
        assert transform_text_spaced("") == ""
        assert transform_text_spaced("a") == "a"

    def test_very_long_word(self):
        word = "a" * 150
        assert transform_text_spaced(word) == ("a" * 141) + " " + ("a" * 9)

    def test_spaced_output_has_no_double_spaces_between_words(self):
        assert "  " not in transform_text_spaced("Bionic Reading")


class TestFrench:
    def test_accented_characters_count_as_letters(self):
        assert transform_text_spaced("été") == "ét é"
        assert transform_text_spaced("français") == "frança is"

    def test_french_sentence(self):
        text = "Bienvenue à Paris, la ville lumière."
        result = transform_text_spaced(text, fixation=1)
        assert result == "Bienven ue à Par is, l a vil le lumiè re."

    def test_french_html_output_preserves_accents(self):
        assert transform_text("français", BionicSettings(fixation=1)) == "<b>frança</b>is"

    def test_cedilla_and_circumflex(self):
        assert transform_text_spaced("garçon") == "garç on"
        assert transform_text_spaced("hôtel") == "hôt el"

    def test_elision_splits_on_apostrophe(self):
        result = transform_text_spaced("l'homme")
        assert "l" in result
        assert "hom me" in result

    def test_ligature_oe(self):
        assert transform_text_spaced("cœur") == "cœu r"

    def test_french_typographic_quotes_unchanged(self):
        text = "« Bonjour » dit-elle."
        result = transform_text(text, BionicSettings(fixation=1))
        assert result.startswith("«")
        assert "<b>Bonjo</b>ur" in result


class TestSettings:
    def test_fixation_out_of_range(self):
        try:
            BionicSettings(fixation=0)
        except ValueError as exc:
            assert "fixation" in str(exc)
        else:
            raise AssertionError("expected ValueError")

    def test_saccade_out_of_range(self):
        try:
            BionicSettings(saccade=5)
        except ValueError as exc:
            assert "saccade" in str(exc)
        else:
            raise AssertionError("expected ValueError")

    def test_custom_marker(self):
        settings = BionicSettings(fixation=1, marker=SpaceMarker())
        assert transform_text("reading", settings) == "readi ng"
