"""Tests for the API layer.

Uses httpx TestClient with mocked market data to avoid network dependencies.
Network-dependent integration tests are marked with @pytest.mark.network.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def mock_market_data():
    """Patch market data functions to return synthetic data."""
    rng = np.random.default_rng(42)
    n_days = 1260  # 5 years

    tickers = ["SPY", "TLT", "GLD"]
    mu = np.array([0.0004, 0.0001, 0.0002])
    daily_vol = np.array([0.01, 0.005, 0.008])
    corr = np.array([
        [1.0, -0.2, 0.1],
        [-0.2, 1.0, 0.15],
        [0.1, 0.15, 1.0],
    ])
    daily_cov = np.outer(daily_vol, daily_vol) * corr
    chol = np.linalg.cholesky(daily_cov + np.eye(3) * 1e-10)
    z = rng.standard_normal((n_days, 3))
    raw_returns = z @ chol.T + mu

    # Build prices from returns
    prices_array = 100 * np.cumprod(1 + raw_returns, axis=0)
    dates = pd.bdate_range(end="2026-04-01", periods=n_days)
    prices_df = pd.DataFrame(prices_array, index=dates, columns=tickers)

    current_prices = {
        "SPY": float(prices_df["SPY"].iloc[-1]),
        "TLT": float(prices_df["TLT"].iloc[-1]),
        "GLD": float(prices_df["GLD"].iloc[-1]),
    }

    with (
        patch("backend.api.routes.portfolio.fetch_historical_prices", return_value=prices_df),
        patch("backend.api.routes.portfolio.get_current_prices", return_value=current_prices),
    ):
        yield prices_df, current_prices


@pytest.fixture
def sample_input() -> dict:
    """Sample portfolio input payload."""
    return {
        "positions": [
            {"ticker": "SPY", "shares": 100, "cost_basis": 400.0},
            {"ticker": "TLT", "shares": 50, "cost_basis": 110.0},
            {"ticker": "GLD", "shares": 30, "cost_basis": 170.0},
        ],
        "preferences": {
            "investment_horizon_years": 5,
            "max_drawdown_tolerance": 0.20,
            "risk_profile": "moderate",
            "rebalance_frequency": "quarterly",
            "include_tax_optimization": True,
            "benchmark": "SPY",
        },
    }


# ── Health Check ────────────────────────────────────────────────


class TestHealthCheck:
    def test_health_returns_200(self) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_body(self) -> None:
        response = client.get("/api/health")
        body = response.json()
        assert body["status"] == "healthy"
        assert "version" in body


# ── Input Validation ────────────────────────────────────────────


class TestInputValidation:
    def test_empty_positions_rejected(self, mock_market_data) -> None:
        payload = {"positions": [], "preferences": {}}
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 422

    def test_negative_shares_rejected(self, mock_market_data) -> None:
        payload = {
            "positions": [
                {"ticker": "SPY", "shares": -10},
                {"ticker": "TLT", "shares": 50},
            ],
        }
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 422

    def test_duplicate_tickers_rejected(self, mock_market_data) -> None:
        payload = {
            "positions": [
                {"ticker": "SPY", "shares": 100},
                {"ticker": "SPY", "shares": 50},
            ],
        }
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 422

    def test_invalid_risk_profile_rejected(self, mock_market_data) -> None:
        payload = {
            "positions": [
                {"ticker": "SPY", "shares": 100},
                {"ticker": "TLT", "shares": 50},
            ],
            "preferences": {"risk_profile": "yolo"},
        }
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 422

    def test_ticker_normalized_to_uppercase(self) -> None:
        """Verify tickers are normalized before processing."""
        from backend.api.schemas.portfolio import Position
        pos = Position(ticker="spy", shares=10)
        assert pos.ticker == "SPY"


# ── Full Analysis Pipeline (Mocked) ────────────────────────────


class TestAnalyzeEndpoint:
    def test_returns_200(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        assert response.status_code == 200

    def test_response_has_all_sections(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        body = response.json()
        assert "diagnostic" in body
        assert "optimization" in body
        assert "stress_test" in body
        assert "rebalance" in body
        assert "monitoring" in body

    def test_diagnostic_fields(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        diag = response.json()["diagnostic"]
        assert diag["total_value"] > 0
        assert isinstance(diag["expected_return"], float)
        assert isinstance(diag["volatility"], float)
        assert isinstance(diag["sharpe_ratio"], float)
        assert isinstance(diag["max_drawdown_historical"], float)
        assert isinstance(diag["var_95"], float)
        assert isinstance(diag["cvar_95"], float)
        assert len(diag["risk_contributions"]) == 3
        assert len(diag["correlation_matrix"]) == 3

    def test_optimization_fields(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        opt = response.json()["optimization"]
        assert len(opt["efficient_frontier"]) >= 3
        assert "expected_return" in opt["current_portfolio_point"]
        assert "weights" in opt["optimal_portfolio"]
        assert "weights" in opt["min_variance_portfolio"]
        assert "weights" in opt["risk_parity_portfolio"]
        assert "rationale" in opt["suggested_portfolio"]

    def test_frontier_weights_sum_to_one(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        frontier = response.json()["optimization"]["efficient_frontier"]
        for point in frontier:
            total = sum(point["weights"].values())
            assert abs(total - 1.0) < 0.01

    def test_stress_test_fields(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        stress = response.json()["stress_test"]
        assert len(stress["scenarios"]) == 6  # 6 historical scenarios
        assert "percentiles" in stress["monte_carlo"]
        assert len(stress["monte_carlo"]["sample_paths"]) > 0

    def test_monte_carlo_percentile_ordering(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        p = response.json()["stress_test"]["monte_carlo"]["percentiles"]
        assert p["p5"] <= p["p25"] <= p["p50"] <= p["p75"] <= p["p95"]

    def test_rebalance_fields(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        reb = response.json()["rebalance"]
        assert isinstance(reb["trades"], list)
        assert isinstance(reb["estimated_transaction_costs"], float)
        assert isinstance(reb["turnover"], float)
        assert reb["turnover"] >= 0

    def test_monitoring_fields(self, mock_market_data, sample_input: dict) -> None:
        response = client.post("/api/portfolio/analyze", json=sample_input)
        mon = response.json()["monitoring"]
        assert isinstance(mon["rebalance_bands"], dict)
        assert "next_review_date" in mon
        assert len(mon["risk_budget_rules"]) > 0

    def test_tax_loss_harvesting_with_flag(self, mock_market_data, sample_input: dict) -> None:
        """When include_tax_optimization is True, TLH section should be present."""
        response = client.post("/api/portfolio/analyze", json=sample_input)
        reb = response.json()["rebalance"]
        assert isinstance(reb["tax_loss_harvesting"], list)

    def test_default_preferences(self, mock_market_data) -> None:
        """Minimal payload with just positions should use defaults."""
        payload = {
            "positions": [
                {"ticker": "SPY", "shares": 100},
                {"ticker": "TLT", "shares": 50},
                {"ticker": "GLD", "shares": 30},
            ],
        }
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 200

    def test_with_constraints(self, mock_market_data) -> None:
        """Test with explicit position constraints."""
        payload = {
            "positions": [
                {"ticker": "SPY", "shares": 100},
                {"ticker": "TLT", "shares": 50},
                {"ticker": "GLD", "shares": 30},
            ],
            "preferences": {
                "investment_horizon_years": 10,
                "risk_profile": "aggressive",
                "constraints": {
                    "max_single_position": 0.50,
                    "min_position_size": 0.05,
                    "required_tickers": ["SPY"],
                },
            },
        }
        response = client.post("/api/portfolio/analyze", json=payload)
        assert response.status_code == 200
        opt = response.json()["optimization"]
        assert opt["optimal_portfolio"]["weights"]["SPY"] > 0.04


# ── Schema Validation Tests ─────────────────────────────────────


class TestSchemaValidation:
    def test_position_model(self) -> None:
        from backend.api.schemas.portfolio import Position
        p = Position(ticker="aapl", shares=10.5, cost_basis=150.0)
        assert p.ticker == "AAPL"
        assert p.shares == 10.5

    def test_preferences_defaults(self) -> None:
        from backend.api.schemas.portfolio import UserPreferences
        prefs = UserPreferences()
        assert prefs.investment_horizon_years == 5
        assert prefs.risk_profile.value == "moderate"
        assert prefs.rebalance_frequency.value == "quarterly"

    def test_portfolio_input_validation(self) -> None:
        from backend.api.schemas.portfolio import PortfolioInput, Position
        # Valid input
        pi = PortfolioInput(
            positions=[
                Position(ticker="SPY", shares=100),
                Position(ticker="TLT", shares=50),
            ]
        )
        assert len(pi.positions) == 2

    def test_portfolio_input_duplicate_rejection(self) -> None:
        from backend.api.schemas.portfolio import PortfolioInput, Position
        with pytest.raises(Exception):
            PortfolioInput(
                positions=[
                    Position(ticker="SPY", shares=100),
                    Position(ticker="SPY", shares=50),
                ]
            )
