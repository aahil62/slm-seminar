import pytest

from slmcheck import stats


def test_mcnemar_known_value():
    assert stats.exact_mcnemar(10, 2) == pytest.approx(0.0386, abs=1e-4)
    assert stats.exact_mcnemar(0, 0) == 1.0


def test_holm():
    assert stats.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_wilson_bounds():
    lo, hi = stats.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)
    assert stats.wilson(0, 0) == (0.0, 1.0)


def test_bootstrap_contains_mean():
    lo, hi = stats.bootstrap_mean_ci([0, 1] * 50, resamples=2000)
    assert lo < 0.5 < hi


def test_gap_recovered_none_when_slm_beats_llm():
    assert stats.gap_recovered(0.7, 0.6, 0.5) is None
    assert stats.gap_recovered(0.6, 0.4, 0.8) == pytest.approx(0.5)
