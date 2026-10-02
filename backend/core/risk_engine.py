"""Risk engine for portfolio analysis.

Computes risk metrics including annualized return/volatility, Sharpe ratio,
max drawdown, VaR, CVaR, covariance estimation with Ledoit-Wolf shrinkage,
and marginal risk contributions per asset.
"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.covariance import LedoitWolf

from backend.config import RISK_FREE_RATE, TRADING_DAYS_PER_YEAR


def annualized_return(daily_returns: pd.DataFrame | pd.Series) -> float | pd.Series:
    """Compute geometric annualized return from daily returns.

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.

    Returns
    -------
    float or pd.Series
        Annualized geometric return.
    """
    total = (1 + daily_returns).prod()
    n_days = len(daily_returns)
    return total ** (TRADING_DAYS_PER_YEAR / n_days) - 1


def annualized_volatility(daily_returns: pd.DataFrame | pd.Series) -> float | pd.Series:
    """Compute annualized volatility from daily returns.

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.

    Returns
    -------
    float or pd.Series
        Annualized volatility.
    """
    return daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def sharpe_ratio(
    daily_returns: pd.DataFrame | pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> float | pd.Series:
    """Compute annualized Sharpe ratio.

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.
    risk_free_rate : float
        Annualized risk-free rate.

    Returns
    -------
    float or pd.Series
        Sharpe ratio.
    """
    ann_ret = annualized_return(daily_returns)
    ann_vol = annualized_volatility(daily_returns)
    return (ann_ret - risk_free_rate) / ann_vol


def max_drawdown(daily_returns: pd.DataFrame | pd.Series) -> float | pd.Series:
    """Compute maximum drawdown from daily returns.

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.

    Returns
    -------
    float or pd.Series
        Maximum drawdown as a positive fraction (e.g., 0.20 = 20% drawdown).
    """
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdowns = (cumulative - running_max) / running_max
    return -drawdowns.min()


def value_at_risk(
    daily_returns: pd.DataFrame | pd.Series,
    confidence: float = 0.95,
) -> float | pd.Series:
    """Compute historical Value at Risk.

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.
    confidence : float
        Confidence level (e.g., 0.95 for 95%).

    Returns
    -------
    float or pd.Series
        VaR as a positive number representing the loss at the given percentile.
    """
    quantile = daily_returns.quantile(1 - confidence)
    return -quantile


def conditional_value_at_risk(
    daily_returns: pd.DataFrame | pd.Series,
    confidence: float = 0.95,
) -> float | pd.Series:
    """Compute Conditional Value at Risk (Expected Shortfall).

    Parameters
    ----------
    daily_returns : pd.DataFrame or pd.Series
        Daily simple returns.
    confidence : float
        Confidence level (e.g., 0.95 for 95%).

    Returns
    -------
    float or pd.Series
        CVaR as a positive number.
    """
    var = -value_at_risk(daily_returns, confidence)  # Get the negative quantile back
    if isinstance(daily_returns, pd.DataFrame):
        result = {}
        for col in daily_returns.columns:
            tail = daily_returns[col][daily_returns[col] <= var[col]]
            result[col] = -tail.mean() if len(tail) > 0 else 0.0
        return pd.Series(result)
    tail = daily_returns[daily_returns <= var]
    return -tail.mean() if len(tail) > 0 else 0.0


def covariance_matrix_ledoit_wolf(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Estimate covariance matrix using Ledoit-Wolf shrinkage.

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns with columns as asset tickers.

    Returns
    -------
    pd.DataFrame
        Shrinkage-estimated covariance matrix (daily scale).
    """
    lw = LedoitWolf()
    lw.fit(daily_returns.values)
    return pd.DataFrame(
        lw.covariance_,
        index=daily_returns.columns,
        columns=daily_returns.columns,
    )


def annualized_covariance_matrix(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Compute annualized covariance matrix with Ledoit-Wolf shrinkage.

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns with columns as asset tickers.

    Returns
    -------
    pd.DataFrame
        Annualized covariance matrix.
    """
    daily_cov = covariance_matrix_ledoit_wolf(daily_returns)
    return daily_cov * TRADING_DAYS_PER_YEAR


def portfolio_return(weights: NDArray[np.float64], expected_returns: NDArray[np.float64]) -> float:
    """Compute portfolio expected return.

    Parameters
    ----------
    weights : ndarray
        Asset weights.
    expected_returns : ndarray
        Expected annualized returns per asset.

    Returns
    -------
    float
        Portfolio expected return.
    """
    return float(weights @ expected_returns)


def portfolio_volatility(
    weights: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
) -> float:
    """Compute portfolio volatility.

    Parameters
    ----------
    weights : ndarray
        Asset weights.
    cov_matrix : ndarray
        Annualized covariance matrix.

    Returns
    -------
    float
        Portfolio volatility (annualized).
    """
    return float(np.sqrt(weights @ cov_matrix @ weights))


def risk_contribution(
    weights: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute each asset's contribution to total portfolio risk.

    Parameters
    ----------
    weights : ndarray
        Asset weights.
    cov_matrix : ndarray
        Annualized covariance matrix.

    Returns
    -------
    ndarray
        Array of risk contributions (sum equals portfolio volatility).
    """
    port_vol = portfolio_volatility(weights, cov_matrix)
    if port_vol == 0:
        return np.zeros_like(weights)
    marginal = cov_matrix @ weights / port_vol
    return weights * marginal


def percentage_risk_contribution(
    weights: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute each asset's percentage contribution to total portfolio risk.

    Parameters
    ----------
    weights : ndarray
        Asset weights.
    cov_matrix : ndarray
        Annualized covariance matrix.

    Returns
    -------
    ndarray
        Array of percentage risk contributions (sum equals 1.0).
    """
    rc = risk_contribution(weights, cov_matrix)
    total = rc.sum()
    if total == 0:
        return np.zeros_like(weights)
    return rc / total


def portfolio_diagnostics(
    weights: NDArray[np.float64],
    daily_returns: pd.DataFrame,
    risk_free_rate: float = RISK_FREE_RATE,
) -> dict:
    """Compute comprehensive portfolio diagnostics.

    Parameters
    ----------
    weights : ndarray
        Asset weights.
    daily_returns : pd.DataFrame
        Daily returns with columns as asset tickers.
    risk_free_rate : float
        Annualized risk-free rate.

    Returns
    -------
    dict
        Dictionary containing all diagnostic metrics.
    """
    portfolio_daily = daily_returns @ weights

    ann_ret = float(annualized_return(portfolio_daily))
    ann_vol = float(annualized_volatility(portfolio_daily))
    sr = (ann_ret - risk_free_rate) / ann_vol if ann_vol > 0 else 0.0
    mdd = float(max_drawdown(portfolio_daily))
    var_95 = float(value_at_risk(portfolio_daily, 0.95))
    cvar_95 = float(conditional_value_at_risk(portfolio_daily, 0.95))

    ann_cov = annualized_covariance_matrix(daily_returns)
    rc = risk_contribution(weights, ann_cov.values)
    prc = percentage_risk_contribution(weights, ann_cov.values)

    tickers = daily_returns.columns.tolist()

    return {
        "expected_return": ann_ret,
        "volatility": ann_vol,
        "sharpe_ratio": sr,
        "max_drawdown_historical": mdd,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "risk_contributions": [
            {
                "ticker": tickers[i],
                "weight": float(weights[i]),
                "marginal_risk_contribution": float(rc[i]),
                "percentage_risk_contribution": float(prc[i]),
            }
            for i in range(len(tickers))
        ],
        "correlation_matrix": daily_returns.corr().values.tolist(),
    }
