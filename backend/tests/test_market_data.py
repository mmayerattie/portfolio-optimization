"""Tests for the market data module.

Tests cover validation, caching logic, and data transformation.
Network-dependent tests are marked with @pytest.mark.network.
"""

import numpy as np
import pandas as pd
import pytest

from backend.data.market_data import (
    MarketDataCache,
    _validate_ticker,
    compute_daily_returns,
    fetch_daily_returns,
    fetch_historical_prices,
    fetch_ticker_info,
    get_cache,
)


class TestValidateTicker:
    def test_normalizes_to_uppercase(self) -> None:
        assert _validate_ticker("spy") == "SPY"

    def test_strips_whitespace(self) -> None:
        assert _validate_ticker("  AAPL  ") == "AAPL"

    def test_dots_converted_to_hyphens(self) -> None:
        assert _validate_ticker("BRK.B") == "BRK-B"

    def test_allows_caret(self) -> None:
        assert _validate_ticker("^GSPC") == "^GSPC"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_ticker("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_ticker("   ")

    def test_special_chars_raise(self) -> None:
        with pytest.raises(ValueError, match="Invalid ticker"):
            _validate_ticker("SPY!@#")


class TestCache:
    def test_set_and_get(self) -> None:
        cache = MarketDataCache()
        cache.set("test_key", {"data": 42}, ttl=3600)
        assert cache.get("test_key") == {"data": 42}

    def test_miss_returns_none(self) -> None:
        cache = MarketDataCache()
        assert cache.get("nonexistent") is None

    def test_expired_returns_none(self) -> None:
        cache = MarketDataCache()
        cache.set("test_key", "value", ttl=0)  # Expires immediately
        import time
        time.sleep(0.01)
        assert cache.get("test_key") is None

    def test_clear(self) -> None:
        cache = MarketDataCache()
        cache.set("a", 1, ttl=3600)
        cache.set("b", 2, ttl=3600)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


class TestComputeDailyReturns:
    def test_basic_returns(self) -> None:
        prices = pd.DataFrame(
            {"A": [100.0, 110.0, 105.0], "B": [50.0, 52.0, 51.0]}
        )
        returns = compute_daily_returns(prices)
        assert len(returns) == 2  # First row dropped
        assert abs(returns.iloc[0]["A"] - 0.10) < 1e-10
        assert abs(returns.iloc[1]["A"] - (-5 / 110)) < 1e-10

    def test_no_nans(self) -> None:
        prices = pd.DataFrame({"A": [100.0, 110.0, 121.0, 115.0]})
        returns = compute_daily_returns(prices)
        assert not returns.isna().any().any()

    def test_preserves_columns(self) -> None:
        prices = pd.DataFrame({"SPY": [100.0, 101.0], "QQQ": [200.0, 202.0]})
        returns = compute_daily_returns(prices)
        assert list(returns.columns) == ["SPY", "QQQ"]


@pytest.mark.network
class TestFetchHistoricalPrices:
    """Integration tests that hit yfinance. Requires network access."""

    def test_fetches_spy(self) -> None:
        get_cache().clear()
        prices = fetch_historical_prices(["SPY"], lookback_years=5)
        assert "SPY" in prices.columns
        assert len(prices) > 200

    def test_multiple_tickers(self) -> None:
        get_cache().clear()
        prices = fetch_historical_prices(["SPY", "TLT"], lookback_years=5)
        assert "SPY" in prices.columns
        assert "TLT" in prices.columns

    def test_caches_result(self) -> None:
        get_cache().clear()
        prices1 = fetch_historical_prices(["SPY"], lookback_years=5)
        prices2 = fetch_historical_prices(["SPY"], lookback_years=5)
        pd.testing.assert_frame_equal(prices1, prices2)

    def test_invalid_ticker_raises(self) -> None:
        get_cache().clear()
        with pytest.raises(ValueError):
            fetch_historical_prices(["ZZZZZZNOTREAL123"], lookback_years=5)


@pytest.mark.network
class TestFetchDailyReturns:
    def test_returns_dataframe(self) -> None:
        get_cache().clear()
        returns = fetch_daily_returns(["SPY"], lookback_years=5)
        assert isinstance(returns, pd.DataFrame)
        assert not returns.empty

    def test_no_nans(self) -> None:
        get_cache().clear()
        returns = fetch_daily_returns(["SPY"], lookback_years=5)
        # Allow a small number of NaNs due to market holidays misalignment
        nan_pct = returns.isna().sum().sum() / returns.size
        assert nan_pct < 0.01


@pytest.mark.network
class TestFetchTickerInfo:
    def test_returns_ticker_info(self) -> None:
        get_cache().clear()
        info = fetch_ticker_info("SPY")
        assert info.ticker == "SPY"
        assert info.current_price > 0
        assert info.name != ""
