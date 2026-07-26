from bionic_reading import transform_text
from bionic_reading.settings import BionicSettings
from bionic_reading.stats import TransformStats


class TestSaccade:
    TEXT = "alpha beta gamma delta epsilon zeta"

    def _transform(self, text: str, saccade: int) -> tuple[str, TransformStats]:
        stats = TransformStats()
        output = transform_text(text, BionicSettings(fixation=1, saccade=saccade), stats)
        return output, stats

    def test_saccade_10_bolds_every_word(self):
        output, stats = self._transform(self.TEXT, saccade=10)
        assert output.count('<b class="bionic">') == 6
        assert stats.words_bolded == 6
        assert stats.words_saccade_skipped == 0

    def test_saccade_50_bolds_fewer_words(self):
        output, stats = self._transform(self.TEXT, saccade=50)
        assert output.count('<b class="bionic">') < 6
        assert stats.words_saccade_skipped > 0

    def test_higher_saccade_means_fewer_bold_words(self):
        _, stats_dense = self._transform(self.TEXT, saccade=10)
        _, stats_sparse = self._transform(self.TEXT, saccade=50)
        assert stats_sparse.words_bolded < stats_dense.words_bolded

    def test_saccade_30_example(self):
        # gap=20: alpha bold, then skip until ~20 chars, then epsilon bold
        output, stats = self._transform(self.TEXT, saccade=30)
        assert '<b class="bionic">alp</b>ha' in output
        assert '<b class="bionic">epsil</b>on' in output
        assert stats.words_bolded == 2
        assert stats.words_saccade_skipped == 4

    def test_french_with_saccade(self):
        stats = TransformStats()
        output = transform_text(
            "Bienvenue à Paris.",
            BionicSettings(fixation=1, saccade=50),
            stats,
        )
        assert '<b class="bionic">' in output
        assert stats.words_saccade_skipped >= 1
