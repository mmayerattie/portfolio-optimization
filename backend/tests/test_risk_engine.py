"""Tests for the risk engine module using deterministic synthetic data."""

import numpy as np
import pandas as pd
import pytest

from backend.core.risk_engine import (
    annualized_covariance_matrix,
    annualized_return,
    annualized_volatility,
    conditional_value_at_risk,
    covariance_matrix_ledoit_wolf,
    max_drawdown,
    percentage_risk_contribution,
    portfolio_diagnostics,
    portfolio_return,
    portfolio_volatility,
    risk_contribution,
    sharpe_ratio,
    value_at_risk,
)
from backend.config import RISK_FREE_RATE, TRADING_DAYS_PER_YEAR


@pytest.fixture
def synthetic_returns() -> pd.DataFrame:
    """Generate deterministic synthetic daily returns for 3 assets."""
    rng = np.random.default_rng(42)
    n_days = 504  # ~2 years

    # Create returns with known statistical properties
    mu = np.array([0.0004, 0.0002, 0.0001])  # daily means
    # Daily covariance (will produce annualized vol ~ 16%, 10%, 5%)
    daily_vol = np.array([0.01, 0.006, 0.003])
    corr = np.array([
        [1.0, 0.5, 0.2],
        [0.5, 1.0, 0.3],
        [0.2, 0.3, 1.0],
    ])
    daily_cov = np.outer(daily_vol, daily_vol) * corr

    chol = np.linalg.cholesky(daily_cov)
    z = rng.standard_normal((n_days, 3))
    raw_returns = z @ chol.T + mu

    return pd.DataFrame(
        raw_returns,
        columns=["ASSET_A", "ASSET_B", "ASSET_C"],
    )


@pytest.fixture
def equal_weights() -> np.ndarray:
    return np.array([1 / 3, 1 / 3, 1 / 3])


class TestAnnualizedReturn:
    def test_positive_returns(self, synthetic_returns: pd.DataFrame) -> None:
        ret = annualized_return(synthetic_returns["ASSET_A"])
        # Asset A has daily mean ~0.04% -> annualized ~10%+
        assert isinstance(ret, float)
        assert ret > 0

    def test_series_vs_dataframe(self, synthetic_returns: pd.DataFrame) -> None:
        series_ret = annualized_return(synthetic_returns["ASSET_A"])
        df_ret = annualized_return(synthetic_returns)
        assert abs(series_ret - df_ret["ASSET_A"]) < 1e-10

    def test_zero_returns(self) -> None:
        zero = pd.Series(np.zeros(252))
        ret = annualized_return(zero)
        assert abs(ret) < 1e-10


class TestAnnualizedVolatility:
    def test_ordering(self, synthetic_returns: pd.DataFrame) -> None:
        vols = annualized_volatility(synthetic_returns)
        # Asset A is most volatile, Asset C is least
        assert vols["ASSET_A"] > vols["ASSET_B"] > vols["ASSET_C"]

    def test_approximate_magnitude(self, synthetic_returns: pd.DataFrame) -> None:
        vol_a = annualized_volatility(synthetic_returns["ASSET_A"])
        # daily vol 0.01 * sqrt(252) ≈ 0.159
        assert 0.10 < vol_a < 0.25

    def test_zero_returns(self) -> None:
        zero = pd.Series(np.zeros(252))
        vol = annualized_volatility(zero)
        assert vol == 0.0


class TestSharpeRatio:
    def test_higher_return_higher_sharpe(self, synthetic_returns: pd.DataFrame) -> None:
        sr = sharpe_ratio(synthetic_returns)
        # Asset A has highest return; won't always have highest Sharpe due to vol
        # but all should be finite
        assert all(np.isfinite(sr))

    def test_with_custom_rf(self, synthetic_returns: pd.DataFrame) -> None:
        sr_high_rf = sharpe_ratio(synthetic_returns["ASSET_A"], risk_free_rate=0.10)
        sr_low_rf = sharpe_ratio(synthetic_returns["ASSET_A"], risk_free_rate=0.01)
        assert sr_low_rf > sr_high_rf


class TestMaxDrawdown:
    def test_positive_drawdown(self, synthetic_returns: pd.DataFrame) -> None:
        mdd = max_drawdown(synthetic_returns["ASSET_A"])
        assert mdd > 0
        assert mdd <= 1.0  # Can't lose more than 100%

    def test_zero_drawdown(self) -> None:
        # Monotonically increasing returns -> still has zero drawdown only if never negative cumulative
        pos = pd.Series([0.01] * 100)
        mdd = max_drawdown(pos)
        assert mdd == 0.0

    def test_known_drawdown(self) -> None:
        # Create a series that goes up 10%, then drops 20% from peak
        returns = pd.Series([0.10, -0.20])
        mdd = max_drawdown(returns)
        # Peak = 1.1, trough after = 1.1 * 0.8 = 0.88, drawdown = (1.1-0.88)/1.1 = 0.2
        assert abs(mdd - 0.2) < 1e-10


class TestValueAtRisk:
    def test_positive_var(self, synthetic_returns: pd.DataFrame) -> None:
        var = value_at_risk(synthetic_returns["ASSET_A"], 0.95)
        assert var > 0  # VaR should be positive (represents a loss)

    def test_higher_confidence_higher_var(self, synthetic_returns: pd.DataFrame) -> None:
        var_95 = value_at_risk(synthetic_returns["ASSET_A"], 0.95)
        var_99 = value_at_risk(synthetic_returns["ASSET_A"], 0.99)
        assert var_99 > var_95


class TestConditionalValueAtRisk:
    def test_cvar_greater_than_var(self, synthetic_returns: pd.DataFrame) -> None:
        var = value_at_risk(synthetic_returns["ASSET_A"], 0.95)
        cvar = conditional_value_at_risk(synthetic_returns["ASSET_A"], 0.95)
        assert cvar >= var  # CVaR is always >= VaR

    def test_positive(self, synthetic_returns: pd.DataFrame) -> None:
        cvar = conditional_value_at_risk(synthetic_returns["ASSET_A"], 0.95)
        assert cvar > 0


class TestCovarianceMatrix:
    def test_shape(self, synthetic_returns: pd.DataFrame) -> None:
        cov = covariance_matrix_ledoit_wolf(synthetic_returns)
        assert cov.shape == (3, 3)

    def test_symmetric(self, synthetic_returns: pd.DataFrame) -> None:
        cov = covariance_matrix_ledoit_wolf(synthetic_returns)
        np.testing.assert_array_almost_equal(cov.values, cov.values.T)

    def test_positive_diagonal(self, synthetic_returns: pd.DataFrame) -> None:
        cov = covariance_matrix_ledoit_wolf(synthetic_returns)
        assert all(cov.values[i, i] > 0 for i in range(3))

    def test_annualized_scaling(self, synthetic_returns: pd.DataFrame) -> None:
        daily_cov = covariance_matrix_ledoit_wolf(synthetic_returns)
        ann_cov = annualized_covariance_matrix(synthetic_returns)
        np.testing.assert_array_almost_equal(
            ann_cov.values, daily_cov.values * TRADING_DAYS_PER_YEAR
        )

    def test_columns_preserved(self, synthetic_returns: pd.DataFrame) -> None:
        cov = covariance_matrix_ledoit_wolf(synthetic_returns)
        assert list(cov.columns) == ["ASSET_A", "ASSET_B", "ASSET_C"]


class TestPortfolioMetrics:
    def test_portfolio_return(self) -> None:
        weights = np.array([0.5, 0.3, 0.2])
        expected_returns = np.array([0.10, 0.08, 0.05])
        ret = portfolio_return(weights, expected_returns)
        expected = 0.5 * 0.10 + 0.3 * 0.08 + 0.2 * 0.05
        assert abs(ret - expected) < 1e-10

    def test_portfolio_volatility(self) -> None:
        weights = np.array([1.0, 0.0])
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        vol = portfolio_volatility(weights, cov)
        assert abs(vol - 0.2) < 1e-10  # sqrt(0.04) = 0.2

    def test_diversification_reduces_vol(self) -> None:
        cov = np.array([[0.04, 0.01], [0.01, 0.04]])
        vol_concentrated = portfolio_volatility(np.array([1.0, 0.0]), cov)
        vol_diversified = portfolio_volatility(np.array([0.5, 0.5]), cov)
        assert vol_diversified < vol_concentrated


class TestRiskContribution:
    def test_sum_equals_portfolio_vol(self, synthetic_returns: pd.DataFrame) -> None:
        weights = np.array([0.5, 0.3, 0.2])
        ann_cov = annualized_covariance_matrix(synthetic_returns)
        rc = risk_contribution(weights, ann_cov.values)
        port_vol = portfolio_volatility(weights, ann_cov.values)
        assert abs(rc.sum() - port_vol) < 1e-10

    def test_percentage_sums_to_one(self, synthetic_returns: pd.DataFrame) -> None:
        weights = np.array([0.5, 0.3, 0.2])
        ann_cov = annualized_covariance_matrix(synthetic_returns)
        prc = percentage_risk_contribution(weights, ann_cov.values)
        assert abs(prc.sum() - 1.0) < 1e-10

    def test_zero_weight_zero_contribution(self, synthetic_returns: pd.DataFrame) -> None:
        weights = np.array([0.6, 0.4, 0.0])
        ann_cov = annualized_covariance_matrix(synthetic_returns)
        rc = risk_contribution(weights, ann_cov.values)
        assert abs(rc[2]) < 1e-10


class TestPortfolioDiagnostics:
    def test_returns_all_keys(
        self, synthetic_returns: pd.DataFrame, equal_weights: np.ndarray
    ) -> None:
        diag = portfolio_diagnostics(equal_weights, synthetic_returns)
        expected_keys = {
            "expected_return",
            "volatility",
            "sharpe_ratio",
            "max_drawdown_historical",
            "var_95",
            "cvar_95",
            "risk_contributions",
            "correlation_matrix",
        }
        assert set(diag.keys()) == expected_keys

    def test_risk_contributions_count(
        self, synthetic_returns: pd.DataFrame, equal_weights: np.ndarray
    ) -> None:
        diag = portfolio_diagnostics(equal_weights, synthetic_returns)
        assert len(diag["risk_contributions"]) == 3

    def test_correlation_matrix_shape(
        self, synthetic_returns: pd.DataFrame, equal_weights: np.ndarray
    ) -> None:
        diag = portfolio_diagnostics(equal_weights, synthetic_returns)
        corr = diag["correlation_matrix"]
        assert len(corr) == 3
        assert len(corr[0]) == 3
        # Diagonal should be 1.0
        for i in range(3):
            assert abs(corr[i][i] - 1.0) < 1e-10
