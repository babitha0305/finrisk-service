import numpy as np
import pandas as pd
import pytest

from app.risk import compute_metrics


def _series(values):
    return pd.Series(values, index=pd.bdate_range("2026-01-01", periods=len(values)))


def test_constant_growth_has_zero_vol():
    s = _series(100 * 1.001 ** np.arange(60))
    m = compute_metrics(s)
    assert m["ann_volatility"] == pytest.approx(0.0, abs=1e-9)
    assert m["max_drawdown"] == 0.0


def test_max_drawdown_known_path():
    path = [100] * 28 + [120, 90, 110]
    assert compute_metrics(_series(path))["max_drawdown"] == pytest.approx(0.25)


def test_var_is_positive_loss_and_matches_percentile():
    rng = np.random.default_rng(0)
    s = _series(100 * np.cumprod(1 + rng.normal(0, 0.01, 500)))
    m = compute_metrics(s)
    expected = -np.percentile(s.pct_change().dropna(), 5)
    assert m["var_95_1d"] == pytest.approx(expected)
    assert m["var_95_1d"] > 0


def test_too_few_observations_rejected():
    with pytest.raises(ValueError):
        compute_metrics(_series([100, 101, 102]))
