"""Market data module wrapping yfinance with in-memory caching.

Provides functions to fetch historical prices, compute daily returns,
and retrieve basic ticker metadata. All yfinance errors are caught and
converted to descriptive ValueError exceptions.
"""

import logging
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yfinance as yf

from backend.config import DEFAULT_LOOKBACK_YEARS, MIN_HISTORY_DAYS

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached item with TTL."""

    data: object
    timestamp: float
    ttl_seconds: float

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl_seconds


class MarketDataCache:
    """Simple in-memory cache with configurable TTL per entry type."""

    PRICE_TTL: float = 3600.0       # 1 hour for current prices
    HISTORY_TTL: float = 86400.0    # 24 hours for historical series

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> object | None:
        entry = self._store.get(key)
        if entry is None or entry.is_expired:
            return None
        return entry.data

    def set(self, key: str, data: object, ttl: float) -> None:
        self._store[key] = CacheEntry(data=data, timestamp=time.time(), ttl_seconds=ttl)

    def clear(self) -> None:
        self._store.clear()


# Module-level cache instance
_cache = MarketDataCache()


def get_cache() -> MarketDataCache:
    """Return the module-level cache instance."""
    return _cache


@dataclass
class TickerInfo:
    """Basic metadata for a ticker."""

    ticker: str
    name: str
    sector: str
    asset_class: str
    current_price: float
    currency: str


def _validate_ticker(ticker: str) -> str:
    """Validate and normalize a ticker symbol.

    Parameters
    ----------
    ticker : str
        Raw ticker string.

    Returns
    -------
    str
        Uppercase, stripped ticker.

    Raises
    ------
    ValueError
        If ticker is empty or contains invalid characters.
    """
    cleaned = ticker.strip().upper()
    if not cleaned:
        raise ValueError("Ticker symbol cannot be empty.")
    if not all(c.isalnum() or c in ".-^" for c in cleaned):
        raise ValueError(f"Invalid ticker symbol: '{ticker}'")
    # Yahoo Finance uses hyphens for share classes (BRK-B, BF-B), not dots
    cleaned = cleaned.replace(".", "-")
    return cleaned


def fetch_historical_prices(
    tickers: list[str],
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
) -> pd.DataFrame:
    """Fetch historical adjusted close prices for multiple tickers.

    Parameters
    ----------
    tickers : list[str]
        List of ticker symbols.
    lookback_years : int
        Number of years of history to fetch.

    Returns
    -------
    pd.DataFrame
        DataFrame with dates as index and tickers as columns (adjusted close).

    Raises
    ------
    ValueError
        If any ticker has insufficient data.
    """
    validated = [_validate_ticker(t) for t in tickers]
    cache_key = f"prices_{'_'.join(sorted(validated))}_{lookback_years}y"

    cached = _cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    try:
        period = f"{lookback_years}y"
        data = yf.download(
            validated,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        logger.error("yfinance download failed: %s", e)
        raise ValueError(f"Failed to fetch market data: {e}") from e

    if data.empty:
        raise ValueError(f"No data returned for tickers: {validated}")

    # Handle single vs multiple tickers
    if len(validated) == 1:
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"].copy()
        else:
            prices = data[["Close"]].copy()
        prices.columns = validated
    else:
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"].copy()
        else:
            prices = data.copy()

    # Drop rows where all values are NaN, then forward-fill gaps
    prices = prices.dropna(how="all")
    prices = prices.ffill()

    # Validate sufficient history for each ticker
    for t in validated:
        if t not in prices.columns:
            raise ValueError(f"Ticker '{t}' not found in market data.")
        non_null = prices[t].notna().sum()
        if non_null < MIN_HISTORY_DAYS:
            raise ValueError(
                f"Ticker '{t}' has only {non_null} trading days of data "
                f"(minimum {MIN_HISTORY_DAYS} required)."
            )

    _cache.set(cache_key, prices, MarketDataCache.HISTORY_TTL)
    return prices


def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily simple returns from price data.

    Parameters
    ----------
    prices : pd.DataFrame
        Daily adjusted close prices.

    Returns
    -------
    pd.DataFrame
        Daily returns (first row is dropped).
    """
    returns = prices.pct_change().dropna()
    return returns


def fetch_daily_returns(
    tickers: list[str],
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
) -> pd.DataFrame:
    """Fetch historical prices and compute daily returns.

    Parameters
    ----------
    tickers : list[str]
        List of ticker symbols.
    lookback_years : int
        Number of years of history.

    Returns
    -------
    pd.DataFrame
        Daily simple returns.
    """
    prices = fetch_historical_prices(tickers, lookback_years)
    return compute_daily_returns(prices)


def fetch_ticker_info(ticker: str) -> TickerInfo:
    """Fetch basic metadata for a single ticker.

    Parameters
    ----------
    ticker : str
        Ticker symbol.

    Returns
    -------
    TickerInfo
        Basic metadata.

    Raises
    ------
    ValueError
        If ticker is invalid or data cannot be fetched.
    """
    validated = _validate_ticker(ticker)
    cache_key = f"info_{validated}"

    cached = _cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    try:
        yf_ticker = yf.Ticker(validated)
        info = yf_ticker.info
    except Exception as e:
        logger.error("Failed to fetch info for %s: %s", validated, e)
        raise ValueError(f"Could not fetch data for ticker '{validated}'.") from e

    if not info or info.get("regularMarketPrice") is None:
        # Try fast_info as fallback
        try:
            fast = yf_ticker.fast_info
            current_price = float(fast.get("lastPrice", 0.0) or fast.get("previousClose", 0.0))
        except Exception:
            current_price = 0.0
    else:
        current_price = float(info.get("regularMarketPrice", 0.0))

    result = TickerInfo(
        ticker=validated,
        name=info.get("shortName", info.get("longName", validated)),
        sector=info.get("sector", "Unknown"),
        asset_class=_infer_asset_class(info),
        current_price=current_price,
        currency=info.get("currency", "USD"),
    )

    _cache.set(cache_key, result, MarketDataCache.PRICE_TTL)
    return result


def _infer_asset_class(info: dict) -> str:
    """Infer asset class from yfinance info dict.

    Parameters
    ----------
    info : dict
        The raw yfinance info dictionary.

    Returns
    -------
    str
        Asset class label.
    """
    quote_type = info.get("quoteType", "").upper()
    category = (info.get("category") or "").lower()
    name = (info.get("shortName") or "").lower()

    if "bond" in category or "treasury" in name or "fixed income" in category:
        return "Fixed Income"
    if "commodity" in category or "gold" in name or "silver" in name:
        return "Commodity"
    if "real estate" in category or "reit" in name:
        return "Real Estate"
    if quote_type == "ETF":
        return "ETF"
    if quote_type == "EQUITY":
        return "Equity"
    return "Other"


def get_current_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current prices for multiple tickers.

    Parameters
    ----------
    tickers : list[str]
        List of ticker symbols.

    Returns
    -------
    dict[str, float]
        Mapping of ticker to current price.
    """
    prices: dict[str, float] = {}
    for t in tickers:
        validated = _validate_ticker(t)
        cache_key = f"current_price_{validated}"
        cached = _cache.get(cache_key)
        if cached is not None:
            prices[validated] = cached  # type: ignore[assignment]
            continue
        try:
            yf_ticker = yf.Ticker(validated)
            fast = yf_ticker.fast_info
            price = float(fast["lastPrice"])
            prices[validated] = price
            _cache.set(cache_key, price, MarketDataCache.PRICE_TTL)
        except Exception as e:
            logger.error("Failed to fetch price for %s: %s", validated, e)
            raise ValueError(f"Could not fetch current price for '{validated}'.") from e
    return prices
