"""Pydantic schemas for portfolio input and analysis response."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RiskProfile(str, Enum):
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"


class RebalanceFrequency(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"
    band_based = "band-based"


# ── Request Models ──────────────────────────────────────────────


class Position(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares held")
    cost_basis: float | None = Field(None, ge=0, description="Average purchase price per share")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class PortfolioConstraints(BaseModel):
    max_single_position: float = Field(0.35, ge=0.01, le=1.0)
    min_position_size: float = Field(0.02, ge=0.0, le=0.5)
    excluded_tickers: list[str] = Field(default_factory=list)
    required_tickers: list[str] = Field(default_factory=list)
    max_turnover: float | None = Field(None, ge=0.0, le=1.0)


class UserPreferences(BaseModel):
    investment_horizon_years: int = Field(5, ge=1, le=30)
    max_drawdown_tolerance: float = Field(0.20, ge=0.01, le=1.0)
    risk_profile: RiskProfile = RiskProfile.moderate
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.quarterly
    include_tax_optimization: bool = False
    benchmark: str = "SPY"
    constraints: PortfolioConstraints | None = None


class MarketView(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    expected_return: float = Field(..., description="Annualized expected return")
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class PortfolioInput(BaseModel):
    positions: list[Position] = Field(..., min_length=1)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    views: list[MarketView] | None = None

    @field_validator("positions")
    @classmethod
    def no_duplicate_tickers(cls, v: list[Position]) -> list[Position]:
        tickers = [p.ticker for p in v]
        if len(tickers) != len(set(tickers)):
            raise ValueError("Duplicate tickers are not allowed.")
        return v


# ── Response Models ─────────────────────────────────────────────


class RiskContributionItem(BaseModel):
    ticker: str
    weight: float
    marginal_risk_contribution: float
    percentage_risk_contribution: float


class FactorExposureItem(BaseModel):
    factor: str
    beta: float
    t_stat: float


class ConcentrationMetrics(BaseModel):
    herfindahl_index: float
    effective_num_assets: float
    top3_weight: float


class DiagnosticOutput(BaseModel):
    total_value: float
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown_historical: float
    var_95: float
    cvar_95: float
    risk_contributions: list[RiskContributionItem]
    factor_exposures: list[FactorExposureItem]
    concentration_metrics: ConcentrationMetrics
    correlation_matrix: list[list[float]]
    warnings: list[str]


class FrontierPoint(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


class PortfolioPoint(BaseModel):
    expected_return: float
    volatility: float


class WeightedPortfolio(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float


class MinVariancePortfolio(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float


class RiskParityPortfolio(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    risk_contributions: dict[str, float]


class SuggestedPortfolio(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    rationale: list[str]


class NewAssetSuggestion(BaseModel):
    ticker: str
    name: str
    asset_class: str
    reason: str
    sharpe_improvement: float = 0.0
    action: str = "add"  # "add" or "replace"
    replaces_ticker: str | None = None


class OptimizationOutput(BaseModel):
    efficient_frontier: list[FrontierPoint]
    current_portfolio_point: PortfolioPoint
    optimal_portfolio: WeightedPortfolio
    min_variance_portfolio: MinVariancePortfolio
    risk_parity_portfolio: RiskParityPortfolio
    suggested_portfolio: SuggestedPortfolio
    new_assets_suggested: list[NewAssetSuggestion]


class ScenarioItem(BaseModel):
    name: str
    current_portfolio_return: float
    optimized_portfolio_return: float
    description: str


class MonteCarloPercentiles(BaseModel):
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float


class MonteCarloOutput(BaseModel):
    percentiles: MonteCarloPercentiles
    probability_of_loss: float
    expected_max_drawdown: float
    sample_paths: list[list[float]]


class StressTestOutput(BaseModel):
    scenarios: list[ScenarioItem]
    monte_carlo: MonteCarloOutput


class TradeItem(BaseModel):
    ticker: str
    action: str  # "buy" or "sell"
    shares: float
    estimated_value: float
    current_weight: float
    target_weight: float


class TaxLossItem(BaseModel):
    ticker: str
    unrealized_loss: float
    replacement_ticker: str
    estimated_tax_savings: float


class RebalanceOutput(BaseModel):
    trades: list[TradeItem]
    estimated_transaction_costs: float
    tax_loss_harvesting: list[TaxLossItem]
    turnover: float


class RebalanceBand(BaseModel):
    lower: float
    upper: float


class MonitoringOutput(BaseModel):
    rebalance_bands: dict[str, RebalanceBand]
    alerts: list[str]
    next_review_date: str
    risk_budget_rules: list[str]


class PortfolioAnalysis(BaseModel):
    diagnostic: DiagnosticOutput
    optimization: OptimizationOutput
    stress_test: StressTestOutput
    rebalance: RebalanceOutput
    monitoring: MonitoringOutput


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: str | None = None


class TickerInfoResponse(BaseModel):
    ticker: str
    name: str
    sector: str
    asset_class: str
    current_price: float
    currency: str
    returns_1y: float | None = None
    returns_3y: float | None = None
    returns_5y: float | None = None
    volatility: float | None = None
