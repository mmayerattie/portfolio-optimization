"""Rebalancing logic for computing trades and tax-loss harvesting suggestions."""

import numpy as np
from numpy.typing import NDArray

from backend.config import REBALANCE_BAND_WIDTH

# Tax-loss harvesting replacement map: similar ETFs for wash-sale avoidance
TLH_REPLACEMENTS: dict[str, str] = {
    "SPY": "VOO", "VOO": "IVV", "IVV": "SPY",
    "QQQ": "QQQM", "QQQM": "QQQ",
    "IWM": "VTWO", "VTWO": "IWM",
    "VEA": "IEFA", "IEFA": "VEA",
    "VWO": "IEMG", "IEMG": "VWO",
    "TLT": "VGLT", "VGLT": "TLT",
    "IEF": "VGIT", "VGIT": "IEF",
    "SHY": "VGSH", "VGSH": "SHY",
    "LQD": "VCIT", "VCIT": "LQD",
    "GLD": "IAU", "IAU": "GLD",
    "VNQ": "IYR", "IYR": "VNQ",
    "AGG": "BND", "BND": "AGG",
}

ESTIMATED_COMMISSION_PER_TRADE: float = 0.0  # Most brokers are commission-free
ESTIMATED_SPREAD_BPS: float = 2.0  # ~2bps average spread cost
TAX_RATE_SHORT_TERM: float = 0.37
TAX_RATE_LONG_TERM: float = 0.20


def compute_trades(
    tickers: list[str],
    current_weights: NDArray[np.float64],
    target_weights: NDArray[np.float64],
    total_value: float,
    current_prices: dict[str, float],
) -> list[dict]:
    """Compute the trade list to move from current to target allocation.

    Parameters
    ----------
    tickers : list[str]
        Ticker symbols.
    current_weights : ndarray
        Current portfolio weights.
    target_weights : ndarray
        Target portfolio weights.
    total_value : float
        Total portfolio value.
    current_prices : dict[str, float]
        Current price per ticker.

    Returns
    -------
    list[dict]
        Trade list with ticker, action, shares, value, and weight changes.
    """
    trades = []
    for i, ticker in enumerate(tickers):
        delta_weight = float(target_weights[i] - current_weights[i])
        if abs(delta_weight) < 1e-6:
            continue

        delta_value = delta_weight * total_value
        price = current_prices.get(ticker, 0.0)
        if price <= 0:
            continue

        shares = abs(delta_value) / price
        trades.append({
            "ticker": ticker,
            "action": "buy" if delta_weight > 0 else "sell",
            "shares": round(shares, 2),
            "estimated_value": round(abs(delta_value), 2),
            "current_weight": round(float(current_weights[i]), 4),
            "target_weight": round(float(target_weights[i]), 4),
        })

    return trades


def estimate_transaction_costs(trades: list[dict]) -> float:
    """Estimate total transaction costs from spread."""
    total_value = sum(t["estimated_value"] for t in trades)
    return round(total_value * ESTIMATED_SPREAD_BPS / 10_000, 2)


def compute_turnover(
    current_weights: NDArray[np.float64],
    target_weights: NDArray[np.float64],
) -> float:
    """Compute portfolio turnover as sum of absolute weight changes / 2."""
    return float(np.sum(np.abs(target_weights - current_weights)) / 2)


def compute_tax_loss_harvesting(
    tickers: list[str],
    shares: list[float],
    cost_bases: list[float | None],
    current_prices: dict[str, float],
) -> list[dict]:
    """Identify tax-loss harvesting opportunities.

    Parameters
    ----------
    tickers : list[str]
        Ticker symbols.
    shares : list[float]
        Current shares held.
    cost_bases : list[float | None]
        Cost basis per share (None if unknown).
    current_prices : dict[str, float]
        Current market prices.

    Returns
    -------
    list[dict]
        Tax-loss harvesting suggestions.
    """
    suggestions = []
    for i, ticker in enumerate(tickers):
        cb = cost_bases[i]
        if cb is None:
            continue

        price = current_prices.get(ticker, 0.0)
        if price <= 0 or price >= cb:
            continue

        unrealized_loss = (cb - price) * shares[i]
        if unrealized_loss < 10:  # Skip trivial losses
            continue

        replacement = TLH_REPLACEMENTS.get(ticker)
        if replacement is None:
            continue

        estimated_tax_savings = round(unrealized_loss * TAX_RATE_LONG_TERM, 2)

        suggestions.append({
            "ticker": ticker,
            "unrealized_loss": round(unrealized_loss, 2),
            "replacement_ticker": replacement,
            "estimated_tax_savings": estimated_tax_savings,
        })

    return suggestions


def compute_rebalance_bands(
    tickers: list[str],
    target_weights: NDArray[np.float64],
    band_width: float = REBALANCE_BAND_WIDTH,
) -> dict[str, dict[str, float]]:
    """Compute rebalance trigger bands for each asset.

    Parameters
    ----------
    tickers : list[str]
        Ticker symbols.
    target_weights : ndarray
        Target weights.
    band_width : float
        Band width (e.g., 0.05 = +/-5%).

    Returns
    -------
    dict
        Mapping of ticker to {lower, upper} band.
    """
    bands = {}
    for i, ticker in enumerate(tickers):
        tw = float(target_weights[i])
        bands[ticker] = {
            "lower": round(max(0.0, tw - band_width), 4),
            "upper": round(min(1.0, tw + band_width), 4),
        }
    return bands
