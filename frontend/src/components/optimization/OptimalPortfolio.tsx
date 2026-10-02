import type { OptimizationOutput } from '../../types/portfolio';
import { formatPercent, formatRatio } from '../../utils/formatters';

interface OptimalPortfolioProps {
  optimization: OptimizationOutput;
}

export function OptimalPortfolio({ optimization }: OptimalPortfolioProps) {
  const { current_portfolio_point, optimal_portfolio, min_variance_portfolio, risk_parity_portfolio, suggested_portfolio } = optimization;

  // Gather all tickers across portfolios
  const allTickers = Array.from(
    new Set([
      ...Object.keys(optimal_portfolio.weights),
      ...Object.keys(min_variance_portfolio.weights),
      ...Object.keys(risk_parity_portfolio.weights),
      ...Object.keys(suggested_portfolio.weights),
    ])
  ).sort();

  // Find current weights from suggested (it has the same tickers as current)
  const currentWeights: Record<string, number> = {};
  for (const rc of Object.keys(suggested_portfolio.weights)) {
    // We don't have current weights per-asset at this level,
    // so we'll show suggested vs optimal comparison
    currentWeights[rc] = 0;
  }

  return (
    <div className="space-y-6">
      {/* Summary comparison cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Current', ret: current_portfolio_point.expected_return, vol: current_portfolio_point.volatility, sharpe: null },
          { label: 'Max Sharpe', ret: optimal_portfolio.expected_return, vol: optimal_portfolio.volatility, sharpe: optimal_portfolio.sharpe_ratio },
          { label: 'Min Variance', ret: min_variance_portfolio.expected_return, vol: min_variance_portfolio.volatility, sharpe: null },
          { label: 'Risk Parity', ret: risk_parity_portfolio.expected_return, vol: risk_parity_portfolio.volatility, sharpe: null },
        ].map((p) => (
          <div key={p.label} className="bg-surface-card rounded-sm border border-border-default p-3">
            <p className="text-[10px] text-text-muted uppercase tracking-wide mb-1.5">{p.label}</p>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-xs text-text-secondary">Return</span>
                <span className="font-data text-sm text-accent-positive">{formatPercent(p.ret)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-text-secondary">Volatility</span>
                <span className="font-data text-sm text-text-primary">{formatPercent(p.vol)}</span>
              </div>
              {p.sharpe !== null && (
                <div className="flex justify-between">
                  <span className="text-xs text-text-secondary">Sharpe</span>
                  <span className="font-data text-sm text-accent-neutral">{formatRatio(p.sharpe)}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Allocation table: suggested vs other portfolios */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Allocation Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted uppercase tracking-wider border-b border-border-default">
                <th className="pb-2 pr-4">Ticker</th>
                <th className="pb-2 pr-4 text-right">Max Sharpe</th>
                <th className="pb-2 pr-4 text-right">Min Variance</th>
                <th className="pb-2 pr-4 text-right">Risk Parity</th>
                <th className="pb-2 text-right">Suggested</th>
              </tr>
            </thead>
            <tbody>
              {allTickers.map((ticker) => (
                <tr key={ticker} className="border-b border-border-subtle">
                  <td className="py-2 pr-4 font-data text-accent-neutral font-medium">{ticker}</td>
                  <td className="py-2 pr-4 text-right font-data text-text-primary">
                    {formatPercent(optimal_portfolio.weights[ticker] ?? 0)}
                  </td>
                  <td className="py-2 pr-4 text-right font-data text-text-primary">
                    {formatPercent(min_variance_portfolio.weights[ticker] ?? 0)}
                  </td>
                  <td className="py-2 pr-4 text-right font-data text-text-primary">
                    {formatPercent(risk_parity_portfolio.weights[ticker] ?? 0)}
                  </td>
                  <td className="py-2 text-right font-data text-accent-positive font-medium">
                    {formatPercent(suggested_portfolio.weights[ticker] ?? 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rationale */}
      {suggested_portfolio.rationale.length > 0 && (
        <div className="bg-surface-card rounded-sm border border-border-default p-4">
          <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Suggested Changes</h3>
          <div className="space-y-2">
            {suggested_portfolio.rationale.map((r, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-text-primary">
                <span className="text-accent-neutral mt-0.5 shrink-0">&#8594;</span>
                {r}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
