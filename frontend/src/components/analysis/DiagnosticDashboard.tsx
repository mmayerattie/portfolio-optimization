import { usePortfolioStore } from '../../store/portfolioStore';
import { formatPercent, formatCurrency, formatRatio } from '../../utils/formatters';
import { RiskContribution } from './RiskContribution';
import { CorrelationMatrix } from './CorrelationMatrix';

interface MetricCardProps {
  label: string;
  value: string;
  color?: 'positive' | 'negative' | 'neutral' | 'default';
}

function MetricCard({ label, value, color = 'default' }: MetricCardProps) {
  const colorClasses = {
    positive: 'text-accent-positive',
    negative: 'text-accent-negative',
    neutral: 'text-accent-neutral',
    default: 'text-text-primary',
  };

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-3">
      <p className="text-[10px] text-text-muted uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-lg font-semibold font-data ${colorClasses[color]}`}>{value}</p>
    </div>
  );
}

export function DiagnosticDashboard() {
  const { analysis } = usePortfolioStore();
  if (!analysis) return null;

  const { diagnostic } = analysis;
  const tickers = diagnostic.risk_contributions.map((r) => r.ticker);

  const sharpeColor = diagnostic.sharpe_ratio >= 1 ? 'positive' : diagnostic.sharpe_ratio >= 0.5 ? 'neutral' : 'negative';

  return (
    <div className="space-y-4 max-w-6xl">
      <div>
        <h2 className="text-base font-semibold text-accent-neutral uppercase tracking-wide">Portfolio Diagnostic</h2>
        <p className="text-xs text-text-muted mt-0.5">
          Current portfolio risk and return analysis.
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Total Value"
          value={formatCurrency(diagnostic.total_value)}
          color="neutral"
        />
        <MetricCard
          label="Expected Return"
          value={formatPercent(diagnostic.expected_return)}
          color={diagnostic.expected_return >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard
          label="Volatility"
          value={formatPercent(diagnostic.volatility)}
          color="default"
        />
        <MetricCard
          label="Sharpe Ratio"
          value={formatRatio(diagnostic.sharpe_ratio)}
          color={sharpeColor}
        />
      </div>

      {/* Risk Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <MetricCard
          label="Max Drawdown (Historical)"
          value={formatPercent(diagnostic.max_drawdown_historical)}
          color="negative"
        />
        <MetricCard
          label="Value at Risk (95%)"
          value={formatPercent(diagnostic.var_95)}
          color="negative"
        />
        <MetricCard
          label="CVaR / Expected Shortfall (95%)"
          value={formatPercent(diagnostic.cvar_95)}
          color="negative"
        />
      </div>

      {/* Concentration Metrics */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Concentration</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-[10px] text-text-muted uppercase tracking-wide">Herfindahl Index</p>
            <p className="text-base font-data text-text-primary">
              {diagnostic.concentration_metrics.herfindahl_index.toFixed(4)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-text-muted uppercase tracking-wide">Effective # Assets</p>
            <p className="text-base font-data text-text-primary">
              {diagnostic.concentration_metrics.effective_num_assets.toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-text-muted uppercase tracking-wide">Top 3 Weight</p>
            <p className="text-base font-data text-text-primary">
              {formatPercent(diagnostic.concentration_metrics.top3_weight)}
            </p>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {diagnostic.warnings.length > 0 && (
        <div className="bg-accent-warning/5 border border-accent-warning/20 rounded-sm p-3 space-y-1.5">
          <h3 className="text-xs font-medium text-accent-warning uppercase tracking-wide">Warnings</h3>
          {diagnostic.warnings.map((w, i) => (
            <p key={i} className="text-sm text-text-secondary flex items-start gap-2">
              <span className="text-accent-warning mt-0.5">&#9679;</span>
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Risk Contribution Chart */}
      <RiskContribution
        contributions={diagnostic.risk_contributions}
      />

      {/* Correlation Matrix */}
      <CorrelationMatrix
        matrix={diagnostic.correlation_matrix}
        tickers={tickers}
      />

      {/* Disclaimer */}
      <p className="text-[10px] text-text-muted">
        This tool is for educational purposes only. It is not financial advice.
        Past performance does not guarantee future results.
      </p>
    </div>
  );
}
