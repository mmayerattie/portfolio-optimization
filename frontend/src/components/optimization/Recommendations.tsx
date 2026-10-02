import type { NewAssetSuggestion } from '../../types/portfolio';
import { formatRatio } from '../../utils/formatters';

interface RecommendationsProps {
  suggestions: NewAssetSuggestion[];
}

export function Recommendations({ suggestions }: RecommendationsProps) {
  if (suggestions.length === 0) {
    return (
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">
          Asset Recommendations
        </h3>
        <p className="text-sm text-text-muted py-3 text-center">
          No improvements found in the expansion universe for your current portfolio.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">
        Asset Recommendations
      </h3>
      <p className="text-[10px] text-text-muted mb-4">
        Assets that could improve your portfolio's risk-adjusted returns, ranked by Sharpe ratio improvement.
      </p>

      <div className="space-y-3">
        {suggestions.map((s) => (
          <div
            key={s.ticker}
            className="border border-border-default rounded-sm p-3 hover:border-accent-positive/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                {/* Header: ticker + action badge */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-data text-accent-positive font-semibold text-sm">
                    {s.ticker}
                  </span>
                  <span
                    className={`
                      text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-sm
                      ${s.action === 'replace'
                        ? 'bg-accent-warning/15 text-accent-warning'
                        : 'bg-accent-positive/15 text-accent-positive'
                      }
                    `}
                  >
                    {s.action === 'replace' ? `Replace ${s.replaces_ticker}` : 'Add 5%'}
                  </span>
                  <span className="text-[10px] text-text-muted px-1.5 py-0.5 rounded-sm bg-surface-hover">
                    {s.asset_class}
                  </span>
                </div>

                {/* Name */}
                <p className="text-xs text-text-secondary mb-1.5">{s.name}</p>

                {/* Reason */}
                <p className="text-xs text-text-primary leading-relaxed">{s.reason}</p>
              </div>

              {/* Sharpe improvement */}
              <div className="text-right shrink-0">
                <p className="text-[10px] text-text-muted uppercase tracking-wide">Sharpe</p>
                <p className="font-data text-lg text-accent-positive font-semibold">
                  +{formatRatio(s.sharpe_improvement, 3)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-text-muted mt-3">
        Recommendations are based on historical data. Past performance does not guarantee future results.
      </p>
    </div>
  );
}
