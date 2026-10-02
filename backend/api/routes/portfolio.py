"""Portfolio analysis endpoint — the main pipeline.

Receives positions and preferences, runs diagnostics, optimization,
stress testing, rebalancing, and monitoring rule generation.
"""

import logging
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.api.schemas.portfolio import (
    ConcentrationMetrics,
    DiagnosticOutput,
    ErrorResponse,
    FrontierPoint,
    MinVariancePortfolio,
    MonitoringOutput,
    MonteCarloOutput,
    MonteCarloPercentiles,
    NewAssetSuggestion,
    OptimizationOutput,
    PortfolioAnalysis,
    PortfolioInput,
    PortfolioPoint,
    RebalanceOutput,
    RiskContributionItem,
    RiskParityPortfolio,
    ScenarioItem,
    StressTestOutput,
    SuggestedPortfolio,
    TradeItem,
    TaxLossItem,
    WeightedPortfolio,
)
from backend.config import (
    DEFAULT_MAX_POSITION_WEIGHT,
    DEFAULT_MIN_POSITION_WEIGHT,
    EXPANSION_UNIVERSE,
    RISK_FREE_RATE,
)
from backend.core.monte_carlo import simulate as mc_simulate
from backend.core.recommender import recommend_assets
from backend.core.optimizer import (
    OptimizationConstraints,
    efficient_frontier,
    maximize_sharpe_ratio,
    minimize_variance,
)
from backend.core.rebalancer import (
    compute_rebalance_bands,
    compute_tax_loss_harvesting,
    compute_trades,
    compute_turnover,
    estimate_transaction_costs,
)
from backend.core.risk_engine import (
    annualized_covariance_matrix,
    annualized_return,
    annualized_volatility,
    conditional_value_at_risk,
    max_drawdown,
    percentage_risk_contribution,
    portfolio_diagnostics,
    portfolio_return,
    portfolio_volatility,
    risk_contribution,
    value_at_risk,
)
from backend.core.scenarios import compute_scenario_returns
from backend.data.market_data import (
    compute_daily_returns,
    fetch_historical_prices,
    get_current_prices,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def _build_constraints(input_data: PortfolioInput, tickers: list[str]) -> OptimizationConstraints:
    """Convert user preferences into optimizer constraints."""
    user_constraints = input_data.preferences.constraints
    if user_constraints is None:
        return OptimizationConstraints(
            min_weight=DEFAULT_MIN_POSITION_WEIGHT,
            max_weight=DEFAULT_MAX_POSITION_WEIGHT,
        )

    excluded_indices = []
    for t in (user_constraints.excluded_tickers or []):
        t_upper = t.upper()
        if t_upper in tickers:
            excluded_indices.append(tickers.index(t_upper))

    required_indices = []
    for t in (user_constraints.required_tickers or []):
        t_upper = t.upper()
        if t_upper in tickers:
            required_indices.append(tickers.index(t_upper))

    return OptimizationConstraints(
        min_weight=user_constraints.min_position_size,
        max_weight=user_constraints.max_single_position,
        excluded_indices=excluded_indices if excluded_indices else None,
        required_indices=required_indices if required_indices else None,
    )


def _generate_warnings(
    weights: np.ndarray,
    tickers: list[str],
    prc: np.ndarray,
    diagnostics: dict,
) -> list[str]:
    """Generate human-readable warnings about portfolio concentration and risk."""
    warnings = []

    # Check if top 2 assets dominate risk
    sorted_risk = sorted(zip(tickers, prc), key=lambda x: x[1], reverse=True)
    top2_risk = sum(r for _, r in sorted_risk[:2])
    if top2_risk > 0.70:
        names = ", ".join(t for t, _ in sorted_risk[:2])
        warnings.append(
            f"{top2_risk:.0%} of portfolio risk comes from just 2 assets ({names})."
        )

    # Check concentration
    hhi = float(np.sum(weights ** 2))
    if hhi > 0.30:
        warnings.append(
            "Portfolio is highly concentrated (HHI > 0.30). Consider diversifying."
        )

    # Check if Sharpe ratio is poor
    if diagnostics["sharpe_ratio"] < 0.3:
        warnings.append(
            "Portfolio Sharpe ratio is below 0.3 — risk-adjusted returns are low."
        )

    # Check if max drawdown is severe
    if diagnostics["max_drawdown_historical"] > 0.30:
        warnings.append(
            f"Historical max drawdown of {diagnostics['max_drawdown_historical']:.1%} is severe."
        )

    return warnings


def _generate_rationale(
    tickers: list[str],
    current_weights: np.ndarray,
    suggested_weights: np.ndarray,
) -> list[str]:
    """Generate human-readable rationale for suggested weight changes."""
    rationale = []
    for i, ticker in enumerate(tickers):
        delta = suggested_weights[i] - current_weights[i]
        if abs(delta) < 0.01:
            continue
        direction = "Increase" if delta > 0 else "Decrease"
        rationale.append(
            f"{direction} {ticker} from {current_weights[i]:.1%} to "
            f"{suggested_weights[i]:.1%} ({delta:+.1%})"
        )
    return rationale


def _compute_concentration(weights: np.ndarray) -> ConcentrationMetrics:
    """Compute concentration metrics for the portfolio."""
    hhi = float(np.sum(weights ** 2))
    eff_n = 1.0 / hhi if hhi > 0 else 0.0
    sorted_w = sorted(weights, reverse=True)
    top3 = float(sum(sorted_w[:3]))
    return ConcentrationMetrics(
        herfindahl_index=round(hhi, 4),
        effective_num_assets=round(eff_n, 2),
        top3_weight=round(top3, 4),
    )


def _next_review_date(frequency: str) -> str:
    """Compute the next review date based on rebalance frequency."""
    now = datetime.now()
    deltas = {
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annual": timedelta(days=365),
        "band-based": timedelta(days=30),  # Check monthly even for band-based
    }
    delta = deltas.get(frequency, timedelta(days=90))
    return (now + delta).strftime("%Y-%m-%d")


def _generate_risk_budget_rules(
    max_dd_tolerance: float,
    risk_profile: str,
) -> list[str]:
    """Generate monitoring risk budget rules based on user preferences."""
    rules = []
    rules.append(
        f"If portfolio drawdown exceeds {max_dd_tolerance:.0%}, "
        f"consider reducing equity exposure by 5-10%."
    )
    if risk_profile == "conservative":
        rules.append("Maintain minimum 40% allocation to fixed income.")
        rules.append("If VaR exceeds 2.5% daily, review risk exposure.")
    elif risk_profile == "moderate":
        rules.append("Maintain minimum 20% allocation to fixed income or low-vol assets.")
    else:
        rules.append("Monitor single-position concentration — cap individual names at 35%.")

    rules.append("Review factor exposures quarterly to avoid unintended tilts.")
    return rules


@router.post(
    "/analyze",
    response_model=PortfolioAnalysis,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_portfolio(input_data: PortfolioInput) -> PortfolioAnalysis:
    """Run the full portfolio analysis pipeline.

    Steps:
    1. Fetch market data for all tickers
    2. Compute diagnostics (risk metrics, correlations)
    3. Run mean-variance optimization + efficient frontier
    4. Run Monte Carlo simulation and scenario analysis
    5. Generate rebalance plan and monitoring rules
    """
    # Normalize tickers: dots → hyphens for Yahoo Finance compatibility (BRK.B → BRK-B)
    tickers = [p.ticker.replace(".", "-") for p in input_data.positions]
    shares_list = [p.shares for p in input_data.positions]
    cost_bases = [p.cost_basis for p in input_data.positions]

    # Filter out CASH — it has zero return/risk and corrupts the covariance estimator
    filtered = [
        (t, s, c) for t, s, c in zip(tickers, shares_list, cost_bases)
        if t.upper() != "CASH"
    ]
    if not filtered:
        raise HTTPException(status_code=400, detail="Portfolio must contain at least one non-cash position.")

    tickers = [t for t, _, _ in filtered]
    shares_list = [s for _, s, _ in filtered]
    cost_bases = [c for _, _, c in filtered]

    # ── Step 1: Fetch market data ────────────────────────────────
    try:
        prices = fetch_historical_prices(tickers)
        daily_returns = compute_daily_returns(prices)
        current_prices = get_current_prices(tickers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Data quality check: drop tickers with >50% zero-return days ──
    bad_tickers = set()
    for col in daily_returns.columns:
        zero_pct = (daily_returns[col] == 0).mean()
        if zero_pct > 0.50:
            bad_tickers.add(col)
    if bad_tickers:
        logger.warning("Dropping tickers with unreliable data (>50%% zero days): %s", bad_tickers)
        daily_returns = daily_returns.drop(columns=list(bad_tickers))

    # ── CRITICAL: align tickers/shares/cost_bases to daily_returns column order ──
    # yfinance may return columns in different order than user input.
    # All downstream math (covariance, weights, risk contributions) must be aligned.
    col_order = daily_returns.columns.tolist()
    ticker_to_input: dict[str, tuple[float, float | None]] = {
        t: (s, c) for t, s, c in zip(tickers, shares_list, cost_bases)
        if t in col_order
    }
    tickers = col_order
    shares_list = [ticker_to_input[t][0] for t in tickers]
    cost_bases = [ticker_to_input[t][1] for t in tickers]

    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers with reliable data remaining after quality check.")

    # ── Compute current weights ──────────────────────────────────
    position_values = np.array([
        shares_list[i] * current_prices[tickers[i]]
        for i in range(len(tickers))
    ])
    total_value = float(position_values.sum())
    if total_value <= 0:
        raise HTTPException(status_code=400, detail="Portfolio total value must be positive.")

    current_weights = position_values / total_value

    # ── Step 2: Diagnostics ──────────────────────────────────────
    diag = portfolio_diagnostics(current_weights, daily_returns)
    ann_cov = annualized_covariance_matrix(daily_returns)
    expected_returns = np.array(annualized_return(daily_returns))

    prc = percentage_risk_contribution(current_weights, ann_cov.values)
    warnings = _generate_warnings(current_weights, tickers, prc, diag)
    concentration = _compute_concentration(current_weights)

    diagnostic = DiagnosticOutput(
        total_value=round(total_value, 2),
        expected_return=round(diag["expected_return"], 4),
        volatility=round(diag["volatility"], 4),
        sharpe_ratio=round(diag["sharpe_ratio"], 4),
        max_drawdown_historical=round(diag["max_drawdown_historical"], 4),
        var_95=round(diag["var_95"], 4),
        cvar_95=round(diag["cvar_95"], 4),
        risk_contributions=[
            RiskContributionItem(**rc) for rc in diag["risk_contributions"]
        ],
        factor_exposures=[],  # Phase 2 — factor model not yet implemented
        concentration_metrics=concentration,
        correlation_matrix=diag["correlation_matrix"],
        warnings=warnings,
    )

    # ── Step 3: Optimization ─────────────────────────────────────
    constraints = _build_constraints(input_data, tickers)

    try:
        max_sharpe = maximize_sharpe_ratio(
            expected_returns, ann_cov.values, constraints
        )
        min_var = minimize_variance(ann_cov.values, constraints)

        # Fill in min_var expected return
        min_var_ret = portfolio_return(min_var.weights, expected_returns)

        frontier = efficient_frontier(
            expected_returns, ann_cov.values, constraints
        )
    except Exception as e:
        logger.error("Optimization failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {e}",
        )

    # Build weight dicts
    def weights_dict(w: np.ndarray) -> dict[str, float]:
        return {tickers[i]: round(float(w[i]), 4) for i in range(len(tickers))}

    # ── Expansion universe: fetch data for recommendation engine ──
    expansion_candidates = [t for t in EXPANSION_UNIVERSE if t.upper() not in [tk.upper() for tk in tickers]]
    combined_daily_returns = daily_returns.copy()

    if expansion_candidates:
        try:
            exp_prices = fetch_historical_prices(expansion_candidates)
            exp_returns = compute_daily_returns(exp_prices)
            # Align on common dates
            common_index = combined_daily_returns.index.intersection(exp_returns.index)
            combined_daily_returns = pd.concat(
                [combined_daily_returns.loc[common_index], exp_returns.loc[common_index]],
                axis=1,
            )
        except Exception:
            # If bulk fetch fails, try tickers individually
            for exp_ticker in expansion_candidates:
                try:
                    t_prices = fetch_historical_prices([exp_ticker])
                    t_returns = compute_daily_returns(t_prices)
                    common_index = combined_daily_returns.index.intersection(t_returns.index)
                    if len(common_index) > 0:
                        combined_daily_returns = pd.concat(
                            [combined_daily_returns.loc[common_index], t_returns.loc[common_index]],
                            axis=1,
                        )
                except Exception:
                    logger.debug("Skipping expansion ticker %s: data unavailable", exp_ticker)

    # Run recommendation engine
    try:
        recommendations = recommend_assets(
            tickers=tickers,
            weights=current_weights,
            expected_returns=expected_returns,
            cov_matrix=ann_cov.values,
            daily_returns=combined_daily_returns,
            expansion_tickers=expansion_candidates,
            max_suggestions=5,
        )
    except Exception:
        logger.warning("Recommendation engine failed; returning empty suggestions", exc_info=True)
        recommendations = []

    new_assets_suggested = [
        NewAssetSuggestion(
            ticker=rec["ticker"],
            name=rec["name"],
            asset_class=rec["asset_class"],
            reason=rec["reason"],
            sharpe_improvement=rec.get("sharpe_improvement", 0.0),
            action=rec.get("action", "add"),
            replaces_ticker=rec.get("replaces_ticker"),
        )
        for rec in recommendations
    ]

    # Simple risk parity approximation: inverse-vol weighting
    # Replace zero vols (e.g., CASH) with a tiny value to avoid Inf
    individual_vols = annualized_volatility(daily_returns)
    safe_vols = np.where(individual_vols.values > 1e-10, individual_vols.values, 1e-10)
    inv_vol = 1.0 / safe_vols
    rp_weights = inv_vol / inv_vol.sum()
    rp_ret = portfolio_return(rp_weights, expected_returns)
    rp_vol = portfolio_volatility(rp_weights, ann_cov.values)
    rp_rc = risk_contribution(rp_weights, ann_cov.values)
    rp_rc_dict = {tickers[i]: round(float(rp_rc[i]), 4) for i in range(len(tickers))}

    # Suggested portfolio = max Sharpe for now
    suggested_weights = max_sharpe.weights
    rationale = _generate_rationale(tickers, current_weights, suggested_weights)

    current_ret = portfolio_return(current_weights, expected_returns)
    current_vol = portfolio_volatility(current_weights, ann_cov.values)

    optimization = OptimizationOutput(
        efficient_frontier=[
            FrontierPoint(
                expected_return=round(p.expected_return, 4),
                volatility=round(p.volatility, 4),
                sharpe_ratio=round(p.sharpe_ratio, 4),
                weights=weights_dict(p.weights),
            )
            for p in frontier
        ],
        current_portfolio_point=PortfolioPoint(
            expected_return=round(current_ret, 4),
            volatility=round(current_vol, 4),
        ),
        optimal_portfolio=WeightedPortfolio(
            weights=weights_dict(max_sharpe.weights),
            expected_return=round(max_sharpe.expected_return, 4),
            volatility=round(max_sharpe.volatility, 4),
            sharpe_ratio=round(max_sharpe.sharpe_ratio, 4),
        ),
        min_variance_portfolio=MinVariancePortfolio(
            weights=weights_dict(min_var.weights),
            expected_return=round(min_var_ret, 4),
            volatility=round(min_var.volatility, 4),
        ),
        risk_parity_portfolio=RiskParityPortfolio(
            weights=weights_dict(rp_weights),
            expected_return=round(rp_ret, 4),
            volatility=round(rp_vol, 4),
            risk_contributions=rp_rc_dict,
        ),
        suggested_portfolio=SuggestedPortfolio(
            weights=weights_dict(suggested_weights),
            expected_return=round(max_sharpe.expected_return, 4),
            volatility=round(max_sharpe.volatility, 4),
            sharpe_ratio=round(max_sharpe.sharpe_ratio, 4),
            rationale=rationale,
        ),
        new_assets_suggested=new_assets_suggested,
    )

    # ── Step 4: Stress Testing ───────────────────────────────────
    horizon = input_data.preferences.investment_horizon_years

    mc_result = mc_simulate(
        expected_returns=expected_returns,
        cov_matrix=ann_cov.values,
        weights=suggested_weights,
        horizon_years=horizon,
        initial_value=total_value,
    )

    current_scenarios = compute_scenario_returns(tickers, current_weights, daily_returns)
    optimized_scenarios = compute_scenario_returns(tickers, suggested_weights, daily_returns)

    stress_test = StressTestOutput(
        scenarios=[
            ScenarioItem(
                name=cs["name"],
                current_portfolio_return=round(cs["portfolio_return"], 4),
                optimized_portfolio_return=round(os["portfolio_return"], 4),
                description=cs["description"],
            )
            for cs, os in zip(current_scenarios, optimized_scenarios)
        ],
        monte_carlo=MonteCarloOutput(
            percentiles=MonteCarloPercentiles(
                p5=round(mc_result.percentiles["p5"], 2),
                p25=round(mc_result.percentiles["p25"], 2),
                p50=round(mc_result.percentiles["p50"], 2),
                p75=round(mc_result.percentiles["p75"], 2),
                p95=round(mc_result.percentiles["p95"], 2),
            ),
            probability_of_loss=round(mc_result.probability_of_loss, 4),
            expected_max_drawdown=round(mc_result.expected_max_drawdown, 4),
            sample_paths=[
                [round(float(v), 2) for v in path]
                for path in mc_result.sample_paths
            ],
        ),
    )

    # ── Step 5: Rebalance Plan ───────────────────────────────────
    trades = compute_trades(
        tickers, current_weights, suggested_weights, total_value, current_prices
    )
    tx_costs = estimate_transaction_costs(trades)
    turnover = compute_turnover(current_weights, suggested_weights)

    tlh: list[dict] = []
    if input_data.preferences.include_tax_optimization:
        tlh = compute_tax_loss_harvesting(
            tickers, shares_list, cost_bases, current_prices
        )

    rebalance = RebalanceOutput(
        trades=[TradeItem(**t) for t in trades],
        estimated_transaction_costs=tx_costs,
        tax_loss_harvesting=[TaxLossItem(**t) for t in tlh],
        turnover=round(turnover, 4),
    )

    # ── Step 6: Monitoring Rules ─────────────────────────────────
    bands = compute_rebalance_bands(tickers, suggested_weights)
    freq = input_data.preferences.rebalance_frequency.value
    next_review = _next_review_date(freq)
    risk_rules = _generate_risk_budget_rules(
        input_data.preferences.max_drawdown_tolerance,
        input_data.preferences.risk_profile.value,
    )

    # Generate alerts based on current state
    alerts: list[str] = []
    for i, ticker in enumerate(tickers):
        band = bands[ticker]
        cw = float(current_weights[i])
        if cw < band["lower"] or cw > band["upper"]:
            alerts.append(
                f"{ticker} weight ({cw:.1%}) is outside rebalance band "
                f"[{band['lower']:.1%}, {band['upper']:.1%}]."
            )

    monitoring = MonitoringOutput(
        rebalance_bands={
            k: {"lower": v["lower"], "upper": v["upper"]}
            for k, v in bands.items()
        },
        alerts=alerts,
        next_review_date=next_review,
        risk_budget_rules=risk_rules,
    )

    result = PortfolioAnalysis(
        diagnostic=diagnostic,
        optimization=optimization,
        stress_test=stress_test,
        rebalance=rebalance,
        monitoring=monitoring,
    )

    # Sanitize NaN/Inf values that can't be serialized to JSON
    def _sanitize(obj: object) -> object:
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return 0.0
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    return PortfolioAnalysis(**_sanitize(result.model_dump()))
