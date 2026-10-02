"""Historical stress scenario definitions and analysis.

Defines major market stress periods and computes estimated portfolio
returns under each scenario. Uses per-ticker market beta to differentiate
how each asset would react, rather than a single flat "equity" return.
"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray

SCENARIOS: list[dict] = [
    {
        "name": "2008 Financial Crisis",
        "period": "Sep 2008 – Mar 2009",
        "description": "Equity crash, credit freeze, global recession",
        "equity_return": -0.45,
        "bond_return": 0.08,
        "commodity_return": -0.30,
        "reit_return": -0.60,
    },
    {
        "name": "COVID Crash",
        "period": "Feb 2020 – Mar 2020",
        "description": "Sharp V-shaped decline from pandemic shock",
        "equity_return": -0.34,
        "bond_return": 0.05,
        "commodity_return": -0.25,
        "reit_return": -0.30,
    },
    {
        "name": "Dot-com Bust",
        "period": "Mar 2000 – Oct 2002",
        "description": "Tech bubble collapse, slow multi-year bleed",
        "equity_return": -0.45,
        "bond_return": 0.20,
        "commodity_return": 0.05,
        "reit_return": 0.10,
    },
    {
        "name": "Rate Shock 2022",
        "period": "Jan 2022 – Oct 2022",
        "description": "Rising rates, bonds and stocks declined together",
        "equity_return": -0.25,
        "bond_return": -0.18,
        "commodity_return": 0.15,
        "reit_return": -0.28,
    },
    {
        "name": "Stagflation 1970s",
        "period": "Jan 1973 – Oct 1974",
        "description": "High inflation combined with recession",
        "equity_return": -0.42,
        "bond_return": -0.08,
        "commodity_return": 0.50,
        "reit_return": -0.20,
    },
    {
        "name": "Bull Run 2017",
        "period": "Jan 2017 – Dec 2017",
        "description": "Low volatility, strong equity returns globally",
        "equity_return": 0.22,
        "bond_return": 0.04,
        "commodity_return": 0.12,
        "reit_return": 0.10,
    },
]

# Known asset classes for common tickers
TICKER_ASSET_CLASS: dict[str, str] = {
    # US Equity ETFs
    "SPY": "equity", "QQQ": "equity", "IWM": "equity", "DIA": "equity",
    "VOO": "equity", "VTI": "equity", "IVV": "equity",
    "SMH": "equity", "XLK": "equity", "XLF": "equity", "XLE": "equity",
    "XLV": "equity", "XLI": "equity", "XLP": "equity", "XLY": "equity",
    "XLB": "equity", "XLRE": "reit",
    # Factor ETFs
    "MTUM": "equity", "VLUE": "equity", "QUAL": "equity", "SIZE": "equity",
    # International Equity
    "VEA": "equity", "VWO": "equity", "EFA": "equity", "EEM": "equity",
    # Bonds
    "TLT": "bond", "IEF": "bond", "SHY": "bond", "TIP": "bond",
    "LQD": "bond", "AGG": "bond", "BND": "bond", "HYG": "bond",
    # Commodities
    "GLD": "commodity", "SLV": "commodity", "DBC": "commodity",
    "USO": "commodity", "UNG": "commodity",
    # REITs
    "VNQ": "reit", "VNQI": "reit", "IYR": "reit",
    "DLR": "reit", "AMT": "reit", "O": "reit", "PLD": "reit",
    # Utilities (defensive equity)
    "XLU": "equity",
}

# Default betas for known asset classes (used when we can't compute from data)
DEFAULT_BETAS: dict[str, float] = {
    "equity": 1.0,
    "bond": -0.2,
    "commodity": 0.3,
    "reit": 1.2,
}


def _estimate_betas(daily_returns: pd.DataFrame) -> dict[str, float]:
    """Estimate each ticker's beta to the equal-weight portfolio.

    Uses the portfolio's own equal-weight return as a market proxy,
    so this works for any mix of assets without needing SPY data.

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns for all tickers.

    Returns
    -------
    dict[str, float]
        Ticker → beta mapping.
    """
    market = daily_returns.mean(axis=1)  # equal-weight proxy
    market_var = market.var()
    if market_var < 1e-12:
        return {col: 1.0 for col in daily_returns.columns}

    betas = {}
    for col in daily_returns.columns:
        cov = daily_returns[col].cov(market)
        betas[col] = float(cov / market_var)
    return betas


def _get_asset_class(ticker: str) -> str:
    """Map a ticker to its asset class."""
    return TICKER_ASSET_CLASS.get(ticker.upper(), "equity")


def _scenario_return_for_ticker(
    ticker: str,
    scenario: dict,
    beta: float,
) -> float:
    """Compute per-ticker scenario return using asset class + beta scaling.

    For equities, the scenario return is scaled by the ticker's beta,
    so high-beta stocks (COIN, SMH) crash harder and rally more.
    For bonds/commodities/REITs, the base class return is used directly.
    """
    asset_class = _get_asset_class(ticker)

    if asset_class == "equity":
        base = scenario.get("equity_return", 0.0)
        # Scale by beta: beta=1.5 means 50% more extreme than market
        return base * beta
    else:
        key = f"{asset_class}_return"
        return scenario.get(key, scenario.get("equity_return", 0.0))


def compute_scenario_returns(
    tickers: list[str],
    weights: NDArray[np.float64],
    daily_returns: pd.DataFrame | None = None,
) -> list[dict]:
    """Compute portfolio returns under each historical stress scenario.

    Uses per-ticker betas estimated from daily returns to differentiate
    how each asset reacts. High-beta assets (COIN, SMH) get amplified
    scenario returns; low-beta assets (XLU) get dampened ones.

    Parameters
    ----------
    tickers : list[str]
        Asset tickers in portfolio order.
    weights : ndarray
        Asset weights matching ticker order.
    daily_returns : pd.DataFrame, optional
        Daily returns for beta estimation. If None, uses default betas.

    Returns
    -------
    list[dict]
        One entry per scenario with name, description, and portfolio return.
    """
    # Estimate betas from actual data if available
    if daily_returns is not None and len(daily_returns) > 60:
        estimated_betas = _estimate_betas(daily_returns)
    else:
        estimated_betas = {}

    # Get beta for each ticker (estimated > default by asset class)
    betas = []
    for t in tickers:
        if t in estimated_betas:
            betas.append(estimated_betas[t])
        else:
            ac = _get_asset_class(t)
            betas.append(DEFAULT_BETAS.get(ac, 1.0))

    results = []
    for scenario in SCENARIOS:
        asset_returns = np.array([
            _scenario_return_for_ticker(t, scenario, betas[i])
            for i, t in enumerate(tickers)
        ])
        portfolio_ret = float(weights @ asset_returns)
        results.append({
            "name": scenario["name"],
            "description": scenario["description"],
            "portfolio_return": portfolio_ret,
        })
    return results
