"""Tests for the portfolio optimizer module."""

import numpy as np
import pytest

from backend.core.optimizer import (
    OptimizationConstraints,
    OptimizedPortfolio,
    efficient_frontier,
    maximize_sharpe_ratio,
    minimize_variance,
)
from backend.core.risk_engine import portfolio_return, portfolio_volatility


@pytest.fixture
def simple_assets() -> tuple[np.ndarray, np.ndarray]:
    """3-asset universe with known properties.

    Asset A: high return, high vol
    Asset B: medium return, medium vol
    Asset C: low return, low vol (bond-like)
    Low correlations to enable diversification.
    """
    expected_returns = np.array([0.12, 0.08, 0.04])
    cov_matrix = np.array([
        [0.0400, 0.0060, 0.0010],  # vol=20%, corr(A,B)=0.3, corr(A,C)=0.05
        [0.0060, 0.0100, 0.0012],  # vol=10%, corr(B,C)=0.12
        [0.0010, 0.0012, 0.0025],  # vol=5%
    ])
    return expected_returns, cov_matrix


@pytest.fixture
def two_assets() -> tuple[np.ndarray, np.ndarray]:
    """Simple 2-asset case for analytical verification."""
    expected_returns = np.array([0.10, 0.05])
    cov_matrix = np.array([
        [0.04, 0.005],
        [0.005, 0.01],
    ])
    return expected_returns, cov_matrix


class TestMaximizeSharpeRatio:
    def test_weights_sum_to_one(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        result = maximize_sharpe_ratio(mu, cov)
        assert abs(np.sum(result.weights) - 1.0) < 1e-6

    def test_no_negative_weights(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        result = maximize_sharpe_ratio(mu, cov)
        assert all(w >= -1e-8 for w in result.weights)

    def test_sharpe_is_positive(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        result = maximize_sharpe_ratio(mu, cov)
        assert result.sharpe_ratio > 0

    def test_beats_equal_weight(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        result = maximize_sharpe_ratio(mu, cov)
        # Equal weight Sharpe
        eq_w = np.array([1 / 3, 1 / 3, 1 / 3])
        eq_ret = portfolio_return(eq_w, mu)
        eq_vol = portfolio_volatility(eq_w, cov)
        eq_sharpe = (eq_ret - 0.045) / eq_vol
        assert result.sharpe_ratio >= eq_sharpe - 1e-6

    def test_respects_max_weight(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        constraints = OptimizationConstraints(max_weight=0.50)
        result = maximize_sharpe_ratio(mu, cov, constraints)
        assert all(w <= 0.50 + 1e-6 for w in result.weights)

    def test_respects_excluded(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        constraints = OptimizationConstraints(excluded_indices=[0])
        result = maximize_sharpe_ratio(mu, cov, constraints)
        assert result.weights[0] < 1e-8

    def test_respects_required(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        constraints = OptimizationConstraints(
            min_weight=0.05,
            required_indices=[2],
        )
        result = maximize_sharpe_ratio(mu, cov, constraints)
        assert result.weights[2] > 0.05 - 1e-6

    def test_two_asset_prefers_higher_sharpe(self, two_assets: tuple) -> None:
        mu, cov = two_assets
        result = maximize_sharpe_ratio(mu, cov)
        # Asset 1: return 10%, vol 20%, Sharpe (10-4.5)/20 = 0.275
        # Asset 2: return 5%, vol 10%, Sharpe (5-4.5)/10 = 0.05
        # Optimal should tilt toward asset 1 but include some of asset 2 for diversification
        assert result.weights[0] > result.weights[1]


class TestMinimizeVariance:
    def test_weights_sum_to_one(self, simple_assets: tuple) -> None:
        _, cov = simple_assets
        result = minimize_variance(cov)
        assert abs(np.sum(result.weights) - 1.0) < 1e-6

    def test_tilts_toward_low_vol(self, simple_assets: tuple) -> None:
        _, cov = simple_assets
        result = minimize_variance(cov)
        # Should heavily favor Asset C (lowest vol)
        assert result.weights[2] > result.weights[0]

    def test_lower_vol_than_equal_weight(self, simple_assets: tuple) -> None:
        _, cov = simple_assets
        result = minimize_variance(cov)
        eq_vol = portfolio_volatility(np.array([1 / 3, 1 / 3, 1 / 3]), cov)
        assert result.volatility <= eq_vol + 1e-8

    def test_lower_vol_than_any_single_asset(self, simple_assets: tuple) -> None:
        _, cov = simple_assets
        result = minimize_variance(cov)
        for i in range(3):
            w = np.zeros(3)
            w[i] = 1.0
            single_vol = portfolio_volatility(w, cov)
            assert result.volatility <= single_vol + 1e-8

    def test_respects_max_weight(self, simple_assets: tuple) -> None:
        _, cov = simple_assets
        constraints = OptimizationConstraints(max_weight=0.40)
        result = minimize_variance(cov, constraints)
        assert all(w <= 0.40 + 1e-6 for w in result.weights)


class TestEfficientFrontier:
    def test_returns_correct_count(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=20)
        # May have fewer than 20 if some targets are infeasible
        assert len(frontier) > 5
        assert len(frontier) <= 20

    def test_sorted_by_volatility(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=20)
        vols = [p.volatility for p in frontier]
        for i in range(len(vols) - 1):
            assert vols[i] <= vols[i + 1] + 1e-8

    def test_return_increases_with_risk(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=20)
        # On the efficient frontier, return should generally increase with vol
        # (allowing small tolerance for numerical noise)
        returns = [p.expected_return for p in frontier]
        # First point should have lower return than last
        assert returns[-1] > returns[0] - 1e-6

    def test_weights_sum_to_one(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=10)
        for point in frontier:
            assert abs(np.sum(point.weights) - 1.0) < 1e-4

    def test_no_negative_weights(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=10)
        for point in frontier:
            assert all(w >= -1e-6 for w in point.weights)

    def test_with_constraints(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        constraints = OptimizationConstraints(max_weight=0.60)
        frontier = efficient_frontier(mu, cov, constraints, n_points=10)
        for point in frontier:
            assert all(w <= 0.60 + 1e-6 for w in point.weights)

    def test_sharpe_ratios_computed(self, simple_assets: tuple) -> None:
        mu, cov = simple_assets
        frontier = efficient_frontier(mu, cov, n_points=10)
        for point in frontier:
            if point.volatility > 1e-8:
                expected_sr = (point.expected_return - 0.045) / point.volatility
                assert abs(point.sharpe_ratio - expected_sr) < 1e-4


class TestEdgeCases:
    def test_single_asset_universe(self) -> None:
        mu = np.array([0.08])
        cov = np.array([[0.04]])
        result = maximize_sharpe_ratio(mu, cov)
        assert abs(result.weights[0] - 1.0) < 1e-6

    def test_identical_assets(self) -> None:
        mu = np.array([0.08, 0.08])
        cov = np.array([[0.04, 0.02], [0.02, 0.04]])
        result = minimize_variance(cov)
        # Should be approximately equal weights for identical assets
        assert abs(result.weights[0] - result.weights[1]) < 0.05

    def test_all_excluded_but_one(self) -> None:
        mu = np.array([0.12, 0.08, 0.04])
        cov = np.array([
            [0.04, 0.006, 0.001],
            [0.006, 0.01, 0.0012],
            [0.001, 0.0012, 0.0025],
        ])
        constraints = OptimizationConstraints(excluded_indices=[0, 1])
        result = maximize_sharpe_ratio(mu, cov, constraints)
        assert result.weights[2] > 0.99
