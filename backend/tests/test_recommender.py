"""Tests for the asset recommendation engine using synthetic data."""

import numpy as np
import pandas as pd
import pytest

from backend.core.recommender import recommend_assets


@pytest.fixture
def synthetic_data() -> (
    tuple[list[str], np.ndarray, np.ndarray, np.ndarray, pd.DataFrame, list[str]]
):
    """Build a small synthetic universe with 2 portfolio assets and 3 candidates.

    Portfolio assets:
        ASSET_A -- mediocre risk-adjusted return (high vol, moderate return)
        ASSET_B -- decent Sharpe

    Expansion candidates:
        CAND_X -- strong Sharpe (high return, moderate vol, low correlation)
        CAND_Y -- poor Sharpe (low return, high vol)
        CAND_Z -- moderate Sharpe
    """
    rng = np.random.default_rng(123)
    n_days = 504  # ~2 years

    tickers = ["ASSET_A", "ASSET_B"]
    expansion = ["CAND_X", "CAND_Y", "CAND_Z"]
    all_tickers = tickers + expansion

    # Daily means -- chosen so CAND_X clearly improves the portfolio
    daily_mu = np.array([0.0002, 0.0003, 0.0006, -0.0001, 0.0003])
    daily_vol = np.array([0.015, 0.008, 0.010, 0.020, 0.009])

    corr = np.array([
        [1.0, 0.4, 0.1, 0.3, 0.5],
        [0.4, 1.0, 0.2, 0.2, 0.4],
        [0.1, 0.2, 1.0, 0.1, 0.3],
        [0.3, 0.2, 0.1, 1.0, 0.2],
        [0.5, 0.4, 0.3, 0.2, 1.0],
    ])
    daily_cov = np.outer(daily_vol, daily_vol) * corr
    chol = np.linalg.cholesky(daily_cov)
    z = rng.standard_normal((n_days, 5))
    raw = z @ chol.T + daily_mu

    daily_returns = pd.DataFrame(raw, columns=all_tickers)

    weights = np.array([0.5, 0.5])

    # Annualized stats for the portfolio tickers only
    from backend.core.risk_engine import annualized_covariance_matrix, annualized_return

    ann_ret = np.array(annualized_return(daily_returns[tickers]))
    ann_cov = annualized_covariance_matrix(daily_returns[tickers]).values

    return tickers, weights, ann_ret, ann_cov, daily_returns, expansion


class TestRecommendAssets:
    def test_returns_list(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion
        )
        assert isinstance(results, list)

    def test_max_suggestions_respected(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
            max_suggestions=2,
        )
        assert len(results) <= 2

    def test_max_suggestions_default(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        assert len(results) <= 5

    def test_required_fields_present(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        required_keys = {"ticker", "name", "asset_class", "reason", "sharpe_improvement", "action"}
        for suggestion in results:
            assert required_keys.issubset(suggestion.keys()), (
                f"Missing keys: {required_keys - suggestion.keys()}"
            )

    def test_suggestions_not_in_portfolio(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        portfolio_set = {t.upper() for t in tickers}
        for suggestion in results:
            assert suggestion["ticker"].upper() not in portfolio_set

    def test_action_is_valid(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        for suggestion in results:
            assert suggestion["action"] in ("add", "replace")

    def test_replace_has_replaces_ticker(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        for suggestion in results:
            if suggestion["action"] == "replace":
                assert "replaces_ticker" in suggestion
                assert suggestion["replaces_ticker"] in tickers

    def test_sorted_by_sharpe_improvement(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        if len(results) >= 2:
            improvements = [r["sharpe_improvement"] for r in results]
            for i in range(len(improvements) - 1):
                assert improvements[i] >= improvements[i + 1]

    def test_sharpe_improvement_positive(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, expansion = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
        )
        for suggestion in results:
            assert suggestion["sharpe_improvement"] > 0

    def test_empty_expansion_returns_empty(self, synthetic_data: tuple) -> None:
        tickers, weights, ann_ret, ann_cov, daily_returns, _ = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns,
            expansion_tickers=[],
        )
        assert results == []

    def test_expansion_already_in_portfolio(self, synthetic_data: tuple) -> None:
        """If all expansion tickers are already in the portfolio, return empty."""
        tickers, weights, ann_ret, ann_cov, daily_returns, _ = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns,
            expansion_tickers=list(tickers),  # same as portfolio
        )
        assert results == []

    def test_missing_candidate_data_skipped(self, synthetic_data: tuple) -> None:
        """Candidates not present in daily_returns are silently skipped."""
        tickers, weights, ann_ret, ann_cov, daily_returns, _ = synthetic_data
        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns,
            expansion_tickers=["NONEXISTENT_TICKER"],
        )
        assert results == []

    def test_single_asset_portfolio(self) -> None:
        """Recommender works when the portfolio has just 1 asset."""
        rng = np.random.default_rng(99)
        n_days = 504

        tickers = ["ONLY"]
        expansion = ["NEW"]
        all_tickers = tickers + expansion

        daily_mu = np.array([0.0001, 0.0005])
        daily_vol = np.array([0.015, 0.008])
        corr = np.array([[1.0, 0.2], [0.2, 1.0]])
        daily_cov = np.outer(daily_vol, daily_vol) * corr
        chol = np.linalg.cholesky(daily_cov)
        z = rng.standard_normal((n_days, 2))
        raw = z @ chol.T + daily_mu
        daily_returns = pd.DataFrame(raw, columns=all_tickers)

        from backend.core.risk_engine import annualized_covariance_matrix, annualized_return

        ann_ret = np.array(annualized_return(daily_returns[tickers]))
        ann_cov = annualized_covariance_matrix(daily_returns[tickers]).values
        weights = np.array([1.0])

        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov, daily_returns, expansion,
            max_suggestions=3,
        )
        assert isinstance(results, list)
        # With a single-asset portfolio, replace strategy requires n_current >= 2,
        # so only 'add' actions should appear
        for suggestion in results:
            assert suggestion["action"] == "add"

    def test_three_asset_portfolio_with_candidates(self) -> None:
        """Full test with 3 portfolio assets and 2 candidates."""
        rng = np.random.default_rng(77)
        n_days = 504

        tickers = ["P1", "P2", "P3"]
        expansion = ["C1", "C2"]
        all_tickers = tickers + expansion

        daily_mu = np.array([0.0001, 0.0002, 0.0003, 0.0005, 0.0001])
        daily_vol = np.array([0.012, 0.010, 0.008, 0.009, 0.014])
        n = len(all_tickers)
        corr = np.eye(n)
        corr[0, 1] = corr[1, 0] = 0.3
        corr[0, 2] = corr[2, 0] = 0.2
        corr[1, 2] = corr[2, 1] = 0.4
        corr[0, 3] = corr[3, 0] = 0.1
        corr[0, 4] = corr[4, 0] = 0.5
        corr[1, 3] = corr[3, 1] = 0.15
        corr[1, 4] = corr[4, 1] = 0.3
        corr[2, 3] = corr[3, 2] = 0.2
        corr[2, 4] = corr[4, 2] = 0.25
        corr[3, 4] = corr[4, 3] = 0.1

        daily_cov = np.outer(daily_vol, daily_vol) * corr
        chol = np.linalg.cholesky(daily_cov)
        z = rng.standard_normal((n_days, n))
        raw = z @ chol.T + daily_mu
        daily_returns = pd.DataFrame(raw, columns=all_tickers)

        from backend.core.risk_engine import annualized_covariance_matrix, annualized_return

        weights = np.array([0.4, 0.35, 0.25])
        ann_ret = np.array(annualized_return(daily_returns[tickers]))
        ann_cov_mat = annualized_covariance_matrix(daily_returns[tickers]).values

        results = recommend_assets(
            tickers, weights, ann_ret, ann_cov_mat, daily_returns, expansion,
            max_suggestions=5,
        )
        assert isinstance(results, list)
        for r in results:
            assert r["ticker"] in ["C1", "C2"]
            assert r["sharpe_improvement"] > 0
