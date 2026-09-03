import pytest

from hughes_forensics.statistics import wilson_interval


def test_wilson_zero_successes_is_bounded() -> None:
    result = wilson_interval(0, 60)
    assert result.rate == 0
    assert result.ci_low == 0
    assert result.ci_high == pytest.approx(0.06017185, rel=1e-5)


def test_wilson_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError):
        wilson_interval(2, 1)

