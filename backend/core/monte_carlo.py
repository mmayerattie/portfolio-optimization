"""Monte Carlo simulation engine for portfolio projections.

Generates correlated random return paths using Cholesky decomposition
of the covariance matrix, then projects portfolio value over the
investment horizon.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.config import (
    MONTE_CARLO_DISPLAY_PATHS,
    MONTE_CARLO_SIMULATIONS,
    TRADING_DAYS_PER_YEAR,
)


@dataclass
class MonteCarloResult:
    """Results of a Monte Carlo simulation.

    Attributes
    ----------
    percentiles : dict[str, float]
        Terminal value percentiles (p5, p25, p50, p75, p95) as returns.
    probability_of_loss : float
        Probability of ending below starting value.
    expected_max_drawdown : float
        Average maximum drawdown across all simulations.
    sample_paths : NDArray[np.float64]
        Subset of simulated portfolio value paths for visualization.
        Shape: (n_display_paths, n_steps).
    all_terminal_values : NDArray[np.float64]
        Terminal portfolio values for all simulations.
    """

    percentiles: dict[str, float]
    probability_of_loss: float
    expected_max_drawdown: float
    sample_paths: NDArray[np.float64]
    all_terminal_values: NDArray[np.float64]


def _cholesky_decompose(cov_matrix: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute Cholesky decomposition, handling near-singular matrices.

    Parameters
    ----------
    cov_matrix : ndarray
        Covariance matrix (must be positive semi-definite).

    Returns
    -------
    ndarray
        Lower triangular Cholesky factor L such that L @ L.T = cov_matrix.
    """
    # Add tiny regularization for numerical stability
    n = cov_matrix.shape[0]
    regularized = cov_matrix + np.eye(n) * 1e-10
    return np.linalg.cholesky(regularized)


def simulate(
    expected_returns: NDArray[np.float64],
    cov_matrix: NDArray[np.float64],
    weights: NDArray[np.float64],
    horizon_years: int,
    initial_value: float = 1.0,
    n_simulations: int = MONTE_CARLO_SIMULATIONS,
    n_display_paths: int = MONTE_CARLO_DISPLAY_PATHS,
    seed: int | None = None,
) -> MonteCarloResult:
    """Run Monte Carlo simulation of portfolio value over time.

    Generates correlated daily returns using multivariate normal distribution
    with Cholesky decomposition, then projects portfolio value paths.

    Parameters
    ----------
    expected_returns : ndarray
        Annualized expected returns per asset.
    cov_matrix : ndarray
        Annualized covariance matrix.
    weights : ndarray
        Portfolio weights.
    horizon_years : int
        Investment horizon in years.
    initial_value : float
        Starting portfolio value.
    n_simulations : int
        Number of simulation paths.
    n_display_paths : int
        Number of representative paths to return for visualization.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    MonteCarloResult
        Simulation results including percentiles, paths, and risk metrics.
    """
    rng = np.random.default_rng(seed)
    n_assets = len(expected_returns)
    n_days = horizon_years * TRADING_DAYS_PER_YEAR

    # Convert annualized parameters to daily
    daily_returns = expected_returns / TRADING_DAYS_PER_YEAR
    daily_cov = cov_matrix / TRADING_DAYS_PER_YEAR

    # Cholesky decomposition for correlated draws
    chol = _cholesky_decompose(daily_cov)

    # Portfolio daily expected return and draws
    port_daily_mu = float(weights @ daily_returns)

    # Generate all random draws at once: (n_simulations, n_days, n_assets)
    z = rng.standard_normal((n_simulations, n_days, n_assets))

    # Correlate the draws: multiply each (n_assets,) vector by chol.T
    # Result: correlated daily asset returns
    correlated = z @ chol.T  # (n_simulations, n_days, n_assets)

    # Add daily expected returns
    correlated += daily_returns  # Broadcasting: (n_assets,)

    # Compute portfolio daily returns: weighted sum across assets
    port_daily_returns = correlated @ weights  # (n_simulations, n_days)

    # Compute cumulative portfolio values
    port_values = initial_value * np.cumprod(1 + port_daily_returns, axis=1)

    # Prepend initial value column
    initial_col = np.full((n_simulations, 1), initial_value)
    port_values_full = np.concatenate([initial_col, port_values], axis=1)

    # Terminal values
    terminal_values = port_values_full[:, -1]

    # Percentiles as total returns
    percentiles = {
        "p5": float(np.percentile(terminal_values, 5)),
        "p25": float(np.percentile(terminal_values, 25)),
        "p50": float(np.percentile(terminal_values, 50)),
        "p75": float(np.percentile(terminal_values, 75)),
        "p95": float(np.percentile(terminal_values, 95)),
    }

    # Probability of loss
    prob_loss = float(np.mean(terminal_values < initial_value))

    # Expected max drawdown across simulations
    running_max = np.maximum.accumulate(port_values_full, axis=1)
    drawdowns = (port_values_full - running_max) / running_max
    max_drawdowns = -np.min(drawdowns, axis=1)
    expected_mdd = float(np.mean(max_drawdowns))

    # Select representative sample paths (evenly spaced by terminal value)
    n_display = min(n_display_paths, n_simulations)
    sorted_indices = np.argsort(terminal_values)
    sample_indices = sorted_indices[
        np.linspace(0, n_simulations - 1, n_display, dtype=int)
    ]
    sample_paths = port_values_full[sample_indices]

    return MonteCarloResult(
        percentiles=percentiles,
        probability_of_loss=prob_loss,
        expected_max_drawdown=expected_mdd,
        sample_paths=sample_paths,
        all_terminal_values=terminal_values,
    )
