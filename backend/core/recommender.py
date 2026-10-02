"""Asset recommendation engine for portfolio improvement suggestions.

Evaluates candidate tickers from an expansion universe and recommends
additions or replacements that would improve the portfolio's risk-adjusted
returns (Sharpe ratio). Candidates are scored by the Sharpe improvement
they would produce if added or if they replaced the weakest asset.
"""

import logging

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from backend.config import RISK_FREE_RATE
from backend.core.risk_engine import portfolio_return, portfolio_volatility

logger = logging.getLogger(__name__)


# Mapping of well-known tickers to (display name, asset class).
# Used as a fallback when live metadata is not available.
_TICKER_METADATA: dict[str, tuple[str, str]] = {
    "SPY": ("SPDR S&P 500 ETF", "Equity"),
    "QQQ": ("Invesco QQQ Trust", "Equity"),
    "IWM": ("iShares Russell 2000 ETF", "Equity"),
    "VEA": ("Vanguard FTSE Developed Markets ETF", "Equity"),
    "VWO": ("Vanguard FTSE Emerging Markets ETF", "Equity"),
    "TLT": ("iShares 20+ Year Treasury Bond ETF", "Fixed Income"),
    "IEF": ("iShares 7-10 Year Treasury Bond ETF", "Fixed Income"),
    "SHY": ("iShares 1-3 Year Treasury Bond ETF", "Fixed Income"),
    "TIP": ("iShares TIPS Bond ETF", "Fixed Income"),
    "LQD": ("iShares Investment Grade Corporate Bond ETF", "Fixed Income"),
    "GLD": ("SPDR Gold Shares", "Commodity"),
    "SLV": ("iShares Silver Trust", "Commodity"),
    "DBC": ("Invesco DB Commodity Index Tracking Fund", "Commodity"),
    "VNQ": ("Vanguard Real Estate ETF", "Real Estate"),
    "VNQI": ("Vanguard Global ex-US Real Estate ETF", "Real Estate"),
    "MTUM": ("iShares MSCI USA Momentum Factor ETF", "Factor"),
    "VLUE": ("iShares MSCI USA Value Factor ETF", "Factor"),
    "QUAL": ("iShares MSCI USA Quality Factor ETF", "Factor"),
    "SIZE": ("iShares MSCI USA Size Factor ETF", "Factor"),
}


def _compute_sharpe(
    weights: NDArray[np.float64],
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    risk_free_rate: float = RISK_FREE_RATE,
) -> float:
    """Compute the Sharpe ratio for a given weight vector.

    Parameters
    ----------
    weights : ndarray
        Portfolio weights.
    expected_returns : ndarray
        Annualized expected returns per asset.
    cov_matrix : ndarray
        Annualized covariance matrix.
    risk_free_rate : float
        Annualized risk-free rate.

    Returns
    -------
    float
        Portfolio Sharpe ratio.
    """
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, cov_matrix)
    if vol < 1e-12:
        return 0.0
    return (ret - risk_free_rate) / vol


def _find_worst_asset_index(
    tickers: list[str],
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
) -> int:
    """Find the index of the asset with the worst individual Sharpe ratio.

    Parameters
    ----------
    tickers : list[str]
        Current portfolio tickers.
    expected_returns : ndarray
        Annualized expected returns for each asset in ``tickers``.
    cov_matrix : ndarray
        Annualized covariance matrix for the assets in ``tickers``.

    Returns
    -------
    int
        Index of the worst risk-adjusted asset.
    """
    individual_sharpes = []
    for i in range(len(tickers)):
        vol_i = float(np.sqrt(cov_matrix[i, i]))
        if vol_i < 1e-12:
            individual_sharpes.append(0.0)
        else:
            individual_sharpes.append(
                (float(expected_returns[i]) - RISK_FREE_RATE) / vol_i
            )
    return int(np.argmin(individual_sharpes))


def recommend_assets(
    tickers: list[str],
    weights: NDArray[np.float64],
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    daily_returns: pd.DataFrame,
    expansion_tickers: list[str],
    max_suggestions: int = 5,
) -> list[dict]:
    """Recommend assets to add or swap into the portfolio.

    For every candidate ticker in ``expansion_tickers`` that is not already in
    the portfolio, two hypothetical portfolios are evaluated:

    1. **Replace** -- the worst risk-adjusted asset is swapped for the candidate
       (keeping the same weight).
    2. **Add** -- a 5 % allocation is carved out for the candidate by reducing
       all existing weights proportionally.

    Suggestions are ranked by the best Sharpe improvement (across either
    action) and the top ``max_suggestions`` are returned.

    Parameters
    ----------
    tickers : list[str]
        Current portfolio tickers.
    weights : ndarray
        Current portfolio weights (must sum to 1).
    expected_returns : ndarray
        Annualized expected returns for each ticker in ``tickers``.
    cov_matrix : ndarray
        Annualized covariance matrix for the assets in ``tickers``.
    daily_returns : pd.DataFrame
        Daily returns DataFrame whose columns include both the current
        portfolio tickers **and** any expansion candidates that were
        successfully fetched.  Columns not present will be silently skipped.
    expansion_tickers : list[str]
        Candidate tickers to evaluate.
    max_suggestions : int
        Maximum number of suggestions to return.

    Returns
    -------
    list[dict]
        Each dict has keys: ``ticker``, ``name``, ``asset_class``, ``reason``,
        ``sharpe_improvement``, ``action`` (``'add'`` or ``'replace'``),
        ``replaces_ticker`` (set only when action is ``'replace'``).
    """
    n_current = len(tickers)
    if n_current == 0:
        return []

    tickers_upper = [t.upper() for t in tickers]
    current_sharpe = _compute_sharpe(weights, expected_returns, cov_matrix)

    worst_idx = _find_worst_asset_index(tickers, expected_returns, cov_matrix)
    worst_ticker = tickers[worst_idx]
    worst_weight = float(weights[worst_idx])

    candidates: list[dict] = []

    for candidate in expansion_tickers:
        candidate_upper = candidate.upper()

        # Skip if already in the portfolio
        if candidate_upper in tickers_upper:
            continue

        # The candidate must be present in daily_returns
        if candidate_upper not in daily_returns.columns:
            continue

        # Build combined returns for the original tickers + candidate
        combined_cols = tickers + [candidate_upper]
        available_cols = [c for c in combined_cols if c in daily_returns.columns]
        if len(available_cols) != len(combined_cols):
            continue  # Missing data for some portfolio tickers too -- skip
        combined_returns = daily_returns[available_cols]

        # Compute annualized stats for the combined universe
        from backend.core.risk_engine import (  # noqa: E402
            annualized_covariance_matrix,
            annualized_return,
        )

        combined_ann_ret = np.array(annualized_return(combined_returns))
        combined_ann_cov = annualized_covariance_matrix(combined_returns).values

        cand_idx = len(tickers)  # index of candidate in combined arrays

        best_improvement = -np.inf
        best_action = "add"
        best_reason = ""
        replaces: str | None = None

        # ── Strategy 1: Replace the worst asset ──────────────────
        if worst_weight > 1e-8 and n_current >= 2:
            replace_weights = np.zeros(len(combined_cols))
            for i in range(n_current):
                if i == worst_idx:
                    replace_weights[i] = 0.0
                else:
                    replace_weights[i] = float(weights[i])
            replace_weights[cand_idx] = worst_weight
            # Renormalize (should already sum to 1, but be safe)
            w_sum = replace_weights.sum()
            if w_sum > 1e-12:
                replace_weights /= w_sum

            replace_sharpe = _compute_sharpe(
                replace_weights, combined_ann_ret, combined_ann_cov
            )
            improvement = replace_sharpe - current_sharpe
            if improvement > best_improvement:
                best_improvement = improvement
                best_action = "replace"
                replaces = worst_ticker

                cand_ret = float(combined_ann_ret[cand_idx])
                cand_vol = float(np.sqrt(combined_ann_cov[cand_idx, cand_idx]))
                best_reason = (
                    f"Replacing {worst_ticker} with {candidate_upper} improves "
                    f"the portfolio Sharpe ratio by {improvement:+.3f}. "
                    f"{candidate_upper} has annualized return {cand_ret:.1%} "
                    f"and volatility {cand_vol:.1%}."
                )

        # ── Strategy 2: Add with 5% allocation ──────────────────
        add_fraction = 0.05
        add_weights = np.zeros(len(combined_cols))
        for i in range(n_current):
            add_weights[i] = float(weights[i]) * (1.0 - add_fraction)
        add_weights[cand_idx] = add_fraction
        # Renormalize
        w_sum = add_weights.sum()
        if w_sum > 1e-12:
            add_weights /= w_sum

        add_sharpe = _compute_sharpe(
            add_weights, combined_ann_ret, combined_ann_cov
        )
        add_improvement = add_sharpe - current_sharpe
        if add_improvement > best_improvement:
            best_improvement = add_improvement
            best_action = "add"
            replaces = None

            cand_ret = float(combined_ann_ret[cand_idx])
            cand_vol = float(np.sqrt(combined_ann_cov[cand_idx, cand_idx]))
            best_reason = (
                f"Adding a 5% allocation to {candidate_upper} improves "
                f"the portfolio Sharpe ratio by {add_improvement:+.3f}. "
                f"{candidate_upper} has annualized return {cand_ret:.1%} "
                f"and volatility {cand_vol:.1%}."
            )

        if best_improvement <= 0:
            continue  # No improvement -- skip this candidate

        name, asset_class = _TICKER_METADATA.get(
            candidate_upper, (candidate_upper, "Other")
        )

        suggestion: dict = {
            "ticker": candidate_upper,
            "name": name,
            "asset_class": asset_class,
            "reason": best_reason,
            "sharpe_improvement": round(float(best_improvement), 4),
            "action": best_action,
        }
        if best_action == "replace" and replaces is not None:
            suggestion["replaces_ticker"] = replaces

        candidates.append(suggestion)

    # Sort by Sharpe improvement descending, then take top N
    candidates.sort(key=lambda c: c["sharpe_improvement"], reverse=True)
    return candidates[:max_suggestions]
