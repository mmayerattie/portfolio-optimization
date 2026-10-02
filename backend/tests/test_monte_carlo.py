"""Tests for the Monte Carlo simulation module."""

import numpy as np
import pytest

from backend.core.monte_carlo import MonteCarloResult, simulate


@pytest.fixture
def simple_portfolio() -> dict:
    """Simple 2-asset portfolio for testing."""
    return {
        "expected_returns": np.array([0.08, 0.04]),
        "cov_matrix": np.array([
            [0.04, 0.005],
            [0.005, 0.01],
        ]),
        "weights": np.array([0.6, 0.4]),
    }


class TestSimulation:
    def test_reproducible_with_seed(self, simple_portfolio: dict) -> None:
        result1 = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=100)
        result2 = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=100)
        np.testing.assert_array_equal(
            result1.all_terminal_values, result2.all_terminal_values
        )

    def test_different_seeds_differ(self, simple_portfolio: dict) -> None:
        result1 = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=100)
        result2 = simulate(**simple_portfolio, horizon_years=5, seed=99, n_simulations=100)
        assert not np.allclose(result1.all_terminal_values, result2.all_terminal_values)

    def test_returns_correct_type(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=3, seed=42, n_simulations=100)
        assert isinstance(result, MonteCarloResult)

    def test_terminal_values_count(self, simple_portfolio: dict) -> None:
        n = 500
        result = simulate(**simple_portfolio, horizon_years=3, seed=42, n_simulations=n)
        assert len(result.all_terminal_values) == n

    def test_sample_paths_count(self, simple_portfolio: dict) -> None:
        result = simulate(
            **simple_portfolio,
            horizon_years=3,
            seed=42,
            n_simulations=100,
            n_display_paths=10,
        )
        assert result.sample_paths.shape[0] == 10

    def test_sample_paths_start_at_initial(self, simple_portfolio: dict) -> None:
        result = simulate(
            **simple_portfolio,
            horizon_years=2,
            seed=42,
            n_simulations=100,
            initial_value=10000.0,
        )
        np.testing.assert_array_equal(result.sample_paths[:, 0], 10000.0)

    def test_sample_paths_length(self, simple_portfolio: dict) -> None:
        result = simulate(
            **simple_portfolio,
            horizon_years=2,
            seed=42,
            n_simulations=100,
        )
        expected_cols = 2 * 252 + 1  # n_days + 1 for initial value
        assert result.sample_paths.shape[1] == expected_cols


class TestPercentiles:
    def test_all_percentile_keys(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=1000)
        for key in ["p5", "p25", "p50", "p75", "p95"]:
            assert key in result.percentiles

    def test_percentile_ordering(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=1000)
        p = result.percentiles
        assert p["p5"] <= p["p25"] <= p["p50"] <= p["p75"] <= p["p95"]

    def test_positive_expected_returns_median_grows(self, simple_portfolio: dict) -> None:
        result = simulate(
            **simple_portfolio,
            horizon_years=10,
            seed=42,
            n_simulations=5000,
            initial_value=1.0,
        )
        # With positive expected returns over 10 years, median should be > 1
        assert result.percentiles["p50"] > 1.0


class TestRiskMetrics:
    def test_probability_of_loss_range(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=1000)
        assert 0.0 <= result.probability_of_loss <= 1.0

    def test_positive_expected_max_drawdown(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=1000)
        assert result.expected_max_drawdown > 0

    def test_max_drawdown_bounded(self, simple_portfolio: dict) -> None:
        result = simulate(**simple_portfolio, horizon_years=5, seed=42, n_simulations=1000)
        assert result.expected_max_drawdown <= 1.0

    def test_longer_horizon_more_growth(self) -> None:
        """With positive returns, longer horizon should yield higher median terminal value."""
        params = {
            "expected_returns": np.array([0.10, 0.05]),
            "cov_matrix": np.array([[0.04, 0.005], [0.005, 0.01]]),
            "weights": np.array([0.5, 0.5]),
        }
        short = simulate(**params, horizon_years=1, seed=42, n_simulations=2000)
        long = simulate(**params, horizon_years=10, seed=42, n_simulations=2000)
        assert long.percentiles["p50"] > short.percentiles["p50"]


class TestCorrelation:
    def test_uncorrelated_assets(self) -> None:
        """With zero correlation, portfolio vol should be lower than weighted sum of vols."""
        expected_returns = np.array([0.08, 0.08])
        cov_matrix = np.array([[0.04, 0.0], [0.0, 0.04]])
        weights = np.array([0.5, 0.5])

        result = simulate(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            weights=weights,
            horizon_years=5,
            seed=42,
            n_simulations=5000,
        )
        # Median should be close to the same for diversified vs undiversified
        # but dispersion should be lower
        single = simulate(
            expected_returns=np.array([0.08]),
            cov_matrix=np.array([[0.04]]),
            weights=np.array([1.0]),
            horizon_years=5,
            seed=42,
            n_simulations=5000,
        )
        # p95-p5 spread should be narrower for diversified
        div_spread = result.percentiles["p95"] - result.percentiles["p5"]
        single_spread = single.percentiles["p95"] - single.percentiles["p5"]
        assert div_spread < single_spread

    def test_single_asset(self) -> None:
        """Single asset simulation should work correctly."""
        result = simulate(
            expected_returns=np.array([0.10]),
            cov_matrix=np.array([[0.04]]),
            weights=np.array([1.0]),
            horizon_years=3,
            seed=42,
            n_simulations=100,
        )
        assert len(result.all_terminal_values) == 100
        assert result.sample_paths.shape[1] == 3 * 252 + 1
