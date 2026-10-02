"""Mean-variance portfolio optimizer.

Implements maximum Sharpe ratio, minimum variance, and efficient frontier
generation with support for weight constraints, required/excluded tickers.
Uses scipy.optimize.minimize with SLSQP for constrained optimization.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize

from backend.config import (
    EFFICIENT_FRONTIER_POINTS,
    RISK_FREE_RATE,
)
from backend.core.risk_engine import (
    portfolio_return,
    portfolio_volatility,
)


@dataclass
class OptimizationConstraints:
    """Constraints for portfolio optimization.

    Attributes
    ----------
    min_weight : float
        Minimum weight per asset (default 0.0).
    max_weight : float
        Maximum weight per asset.
    required_indices : list[int]
        Indices of assets that must have weight > min_weight.
    excluded_indices : list[int]
        Indices of assets that must have weight = 0.
    """

    min_weight: float = 0.0
    max_weight: float = 1.0
    required_indices: list[int] | None = None
    excluded_indices: list[int] | None = None


@dataclass
class OptimizedPortfolio:
    """Result of a portfolio optimization.

    Attributes
    ----------
    weights : ndarray
        Optimal asset weights.
    expected_return : float
        Portfolio expected return.
    volatility : float
        Portfolio volatility.
    sharpe_ratio : float
        Portfolio Sharpe ratio.
    """

    weights: NDArray[np.float64]
    expected_return: float
    volatility: float
    sharpe_ratio: float


def _build_bounds(
    n_assets: int,
    constraints: OptimizationConstraints,
) -> list[tuple[float, float]]:
    """Build per-asset (lower, upper) weight bounds.

    Parameters
    ----------
    n_assets : int
        Number of assets.
    constraints : OptimizationConstraints
        Optimization constraints.

    Returns
    -------
    list[tuple[float, float]]
        Bounds for each asset.
    """
    excluded = set(constraints.excluded_indices or [])
    bounds = []
    for i in range(n_assets):
        if i in excluded:
            bounds.append((0.0, 0.0))
        else:
            bounds.append((constraints.min_weight, constraints.max_weight))
    return bounds


def _initial_weights(n_assets: int, constraints: OptimizationConstraints) -> NDArray[np.float64]:
    """Generate feasible initial weights.

    Parameters
    ----------
    n_assets : int
        Number of assets.
    constraints : OptimizationConstraints
        Optimization constraints.

    Returns
    -------
    ndarray
        Initial weight vector.
    """
    excluded = set(constraints.excluded_indices or [])
    n_active = n_assets - len(excluded)
    if n_active <= 0:
        return np.zeros(n_assets)
    w = np.zeros(n_assets)
    active_weight = 1.0 / n_active
    for i in range(n_assets):
        if i not in excluded:
            w[i] = active_weight
    return w


def maximize_sharpe_ratio(
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    constraints: OptimizationConstraints | None = None,
    risk_free_rate: float = RISK_FREE_RATE,
) -> OptimizedPortfolio:
    """Find the portfolio that maximizes the Sharpe ratio.

    Parameters
    ----------
    expected_returns : ndarray
        Annualized expected returns per asset.
    cov_matrix : ndarray
        Annualized covariance matrix.
    constraints : OptimizationConstraints, optional
        Weight constraints.
    risk_free_rate : float
        Annualized risk-free rate.

    Returns
    -------
    OptimizedPortfolio
        The maximum Sharpe ratio portfolio.
    """
    if constraints is None:
        constraints = OptimizationConstraints()

    n = len(expected_returns)
    bounds = _build_bounds(n, constraints)

    def neg_sharpe(w: NDArray[np.float64]) -> float:
        ret = portfolio_return(w, expected_returns)
        vol = portfolio_volatility(w, cov_matrix)
        if vol < 1e-12:
            return 0.0
        return -(ret - risk_free_rate) / vol

    eq_constraint = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    scipy_constraints = [eq_constraint]

    # Required tickers must have weight > min_weight
    required = constraints.required_indices or []
    for idx in required:
        scipy_constraints.append(
            {"type": "ineq", "fun": lambda w, i=idx: w[i] - constraints.min_weight - 1e-6}
        )

    w0 = _initial_weights(n, constraints)
    result = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=scipy_constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    weights = np.maximum(result.x, 0.0)  # Clean tiny negatives
    weights /= weights.sum()  # Re-normalize

    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, cov_matrix)
    sr = (ret - risk_free_rate) / vol if vol > 1e-12 else 0.0

    return OptimizedPortfolio(
        weights=weights,
        expected_return=ret,
        volatility=vol,
        sharpe_ratio=sr,
    )


def minimize_variance(
    cov_matrix: NDArray[np.float64],
    constraints: OptimizationConstraints | None = None,
) -> OptimizedPortfolio:
    """Find the minimum variance portfolio.

    Parameters
    ----------
    cov_matrix : ndarray
        Annualized covariance matrix.
    constraints : OptimizationConstraints, optional
        Weight constraints.

    Returns
    -------
    OptimizedPortfolio
        The minimum variance portfolio. Note: expected_return is set to 0
        since we don't need expected returns for this optimization.
    """
    if constraints is None:
        constraints = OptimizationConstraints()

    n = cov_matrix.shape[0]
    bounds = _build_bounds(n, constraints)

    def port_var(w: NDArray[np.float64]) -> float:
        return float(w @ cov_matrix @ w)

    eq_constraint = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    w0 = _initial_weights(n, constraints)

    result = minimize(
        port_var,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=[eq_constraint],
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    weights = np.maximum(result.x, 0.0)
    weights /= weights.sum()

    vol = portfolio_volatility(weights, cov_matrix)

    return OptimizedPortfolio(
        weights=weights,
        expected_return=0.0,  # Not computed here
        volatility=vol,
        sharpe_ratio=0.0,
    )


def _minimize_variance_at_target_return(
    target_return: float,
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    constraints: OptimizationConstraints,
) -> OptimizedPortfolio | None:
    """Find the minimum variance portfolio for a given target return.

    Parameters
    ----------
    target_return : float
        Target portfolio return.
    expected_returns : ndarray
        Annualized expected returns per asset.
    cov_matrix : ndarray
        Annualized covariance matrix.
    constraints : OptimizationConstraints
        Weight constraints.

    Returns
    -------
    OptimizedPortfolio or None
        The optimized portfolio, or None if infeasible.
    """
    n = len(expected_returns)
    bounds = _build_bounds(n, constraints)

    def port_var(w: NDArray[np.float64]) -> float:
        return float(w @ cov_matrix @ w)

    scipy_constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "eq", "fun": lambda w: portfolio_return(w, expected_returns) - target_return},
    ]

    w0 = _initial_weights(n, constraints)
    result = minimize(
        port_var,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=scipy_constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not result.success:
        return None

    weights = np.maximum(result.x, 0.0)
    weight_sum = weights.sum()
    if weight_sum < 1e-6:
        return None
    weights /= weight_sum

    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, cov_matrix)

    return OptimizedPortfolio(
        weights=weights,
        expected_return=ret,
        volatility=vol,
        sharpe_ratio=0.0,  # Will be computed by caller
    )


def efficient_frontier(
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    constraints: OptimizationConstraints | None = None,
    risk_free_rate: float = RISK_FREE_RATE,
    n_points: int = EFFICIENT_FRONTIER_POINTS,
) -> list[OptimizedPortfolio]:
    """Generate points along the efficient frontier.

    Parameters
    ----------
    expected_returns : ndarray
        Annualized expected returns per asset.
    cov_matrix : ndarray
        Annualized covariance matrix.
    constraints : OptimizationConstraints, optional
        Weight constraints.
    risk_free_rate : float
        Annualized risk-free rate.
    n_points : int
        Number of points on the frontier.

    Returns
    -------
    list[OptimizedPortfolio]
        Points along the efficient frontier, sorted by volatility.
    """
    if constraints is None:
        constraints = OptimizationConstraints()

    # Find the min variance portfolio to get the lower bound for returns
    min_var = minimize_variance(cov_matrix, constraints)
    min_var_return = portfolio_return(min_var.weights, expected_returns)

    # Upper bound: max feasible return (concentrated in highest-return non-excluded asset)
    excluded = set(constraints.excluded_indices or [])
    active_returns = [
        expected_returns[i] for i in range(len(expected_returns)) if i not in excluded
    ]
    max_return = max(active_returns) if active_returns else min_var_return

    # Generate target returns
    target_returns = np.linspace(min_var_return, max_return, n_points)

    frontier_points: list[OptimizedPortfolio] = []
    for target in target_returns:
        result = _minimize_variance_at_target_return(
            target, expected_returns, cov_matrix, constraints
        )
        if result is not None:
            sr = (
                (result.expected_return - risk_free_rate) / result.volatility
                if result.volatility > 1e-12
                else 0.0
            )
            result.sharpe_ratio = sr
            frontier_points.append(result)

    # Sort by volatility
    frontier_points.sort(key=lambda p: p.volatility)
    return frontier_points
