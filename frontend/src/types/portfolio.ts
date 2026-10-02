// ── Request Types ─────────────────────────────────────────────

export interface Position {
  ticker: string;
  shares: number;
  cost_basis?: number;
}

export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type RebalanceFrequency = 'monthly' | 'quarterly' | 'annual' | 'band-based';

export interface PortfolioConstraints {
  max_single_position: number;
  min_position_size: number;
  excluded_tickers?: string[];
  required_tickers?: string[];
  max_turnover?: number;
}

export interface UserPreferences {
  investment_horizon_years: number;
  max_drawdown_tolerance: number;
  risk_profile: RiskProfile;
  rebalance_frequency: RebalanceFrequency;
  include_tax_optimization: boolean;
  benchmark: string;
  constraints?: PortfolioConstraints;
}

export interface MarketView {
  ticker: string;
  expected_return: number;
  confidence: number;
}

export interface PortfolioInput {
  positions: Position[];
  preferences: UserPreferences;
  views?: MarketView[];
}

// ── Response Types ────────────────────────────────────────────

export interface RiskContributionItem {
  ticker: string;
  weight: number;
  marginal_risk_contribution: number;
  percentage_risk_contribution: number;
}

export interface FactorExposureItem {
  factor: string;
  beta: number;
  t_stat: number;
}

export interface ConcentrationMetrics {
  herfindahl_index: number;
  effective_num_assets: number;
  top3_weight: number;
}

export interface DiagnosticOutput {
  total_value: number;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown_historical: number;
  var_95: number;
  cvar_95: number;
  risk_contributions: RiskContributionItem[];
  factor_exposures: FactorExposureItem[];
  concentration_metrics: ConcentrationMetrics;
  correlation_matrix: number[][];
  warnings: string[];
}

export interface FrontierPoint {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  weights: Record<string, number>;
}

export interface PortfolioPoint {
  expected_return: number;
  volatility: number;
}

export interface WeightedPortfolio {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
}

export interface MinVariancePortfolio {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
}

export interface RiskParityPortfolio {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  risk_contributions: Record<string, number>;
}

export interface SuggestedPortfolio {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  rationale: string[];
}

export interface NewAssetSuggestion {
  ticker: string;
  name: string;
  asset_class: string;
  reason: string;
  sharpe_improvement: number;
  action: 'add' | 'replace';
  replaces_ticker: string | null;
}

export interface OptimizationOutput {
  efficient_frontier: FrontierPoint[];
  current_portfolio_point: PortfolioPoint;
  optimal_portfolio: WeightedPortfolio;
  min_variance_portfolio: MinVariancePortfolio;
  risk_parity_portfolio: RiskParityPortfolio;
  suggested_portfolio: SuggestedPortfolio;
  new_assets_suggested: NewAssetSuggestion[];
}

export interface ScenarioItem {
  name: string;
  current_portfolio_return: number;
  optimized_portfolio_return: number;
  description: string;
}

export interface MonteCarloPercentiles {
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export interface MonteCarloOutput {
  percentiles: MonteCarloPercentiles;
  probability_of_loss: number;
  expected_max_drawdown: number;
  sample_paths: number[][];
}

export interface StressTestOutput {
  scenarios: ScenarioItem[];
  monte_carlo: MonteCarloOutput;
}

export interface TradeItem {
  ticker: string;
  action: 'buy' | 'sell';
  shares: number;
  estimated_value: number;
  current_weight: number;
  target_weight: number;
}

export interface TaxLossItem {
  ticker: string;
  unrealized_loss: number;
  replacement_ticker: string;
  estimated_tax_savings: number;
}

export interface RebalanceOutput {
  trades: TradeItem[];
  estimated_transaction_costs: number;
  tax_loss_harvesting: TaxLossItem[];
  turnover: number;
}

export interface RebalanceBand {
  lower: number;
  upper: number;
}

export interface MonitoringOutput {
  rebalance_bands: Record<string, RebalanceBand>;
  alerts: string[];
  next_review_date: string;
  risk_budget_rules: string[];
}

export interface PortfolioAnalysis {
  diagnostic: DiagnosticOutput;
  optimization: OptimizationOutput;
  stress_test: StressTestOutput;
  rebalance: RebalanceOutput;
  monitoring: MonitoringOutput;
}

export interface TickerInfoResponse {
  ticker: string;
  name: string;
  sector: string;
  asset_class: string;
  current_price: number;
  currency: string;
  returns_1y: number | null;
  returns_3y: number | null;
  returns_5y: number | null;
  volatility: number | null;
}

// ── UI State Types ────────────────────────────────────────────

export type AppTab = 'input' | 'diagnostic' | 'optimization' | 'stress-test' | 'rebalance' | 'monitoring';
