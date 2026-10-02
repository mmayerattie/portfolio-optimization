import { useState } from 'react';
import { usePortfolioStore } from '../../store/portfolioStore';
import { TickerSearch } from './TickerSearch';

export function PortfolioInput() {
  const {
    positions,
    addPosition,
    removePosition,
    updatePosition,
    analyzePortfolio,
    isLoading,
    error,
  } = usePortfolioStore();

  return (
    <div className="space-y-4 max-w-4xl">
      <div>
        <h2 className="text-base font-semibold text-accent-neutral uppercase tracking-wide">Portfolio Input</h2>
        <p className="text-xs text-text-muted mt-0.5">
          Enter your positions and preferences, then click Analyze.
        </p>
      </div>

      {/* Positions Table */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide">Positions</h3>
          <button
            onClick={addPosition}
            className="text-xs font-medium text-accent-neutral hover:text-accent-neutral/80 transition-colors cursor-pointer"
          >
            + Add Position
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-text-muted text-xs uppercase tracking-wider border-b border-border-default">
                <th className="pb-2 pr-3 w-36">Ticker</th>
                <th className="pb-2 pr-3 w-32">Shares</th>
                <th className="pb-2 pr-3 w-40">
                  <CostBasisHeader />
                </th>
                <th className="pb-2 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos, i) => (
                <tr key={i} className="border-b border-border-subtle group">
                  <td className="py-2 pr-3">
                    <TickerSearch
                      value={pos.ticker}
                      onChange={(ticker) => updatePosition(i, 'ticker', ticker)}
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      type="number"
                      value={pos.shares || ''}
                      onChange={(e) => updatePosition(i, 'shares', parseFloat(e.target.value) || 0)}
                      placeholder="100"
                      min="0"
                      step="1"
                      className="w-full bg-surface-primary border border-border-default rounded-md px-3 py-1.5 text-sm font-data text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-neutral/50 transition-colors"
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      type="number"
                      value={pos.cost_basis ?? ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        updatePosition(i, 'cost_basis', val === '' ? undefined : parseFloat(val));
                      }}
                      placeholder="Optional"
                      min="0"
                      step="0.01"
                      className="w-full bg-surface-primary border border-border-default rounded-md px-3 py-1.5 text-sm font-data text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-neutral/50 transition-colors"
                    />
                  </td>
                  <td className="py-2">
                    {positions.length > 1 && (
                      <button
                        onClick={() => removePosition(i)}
                        className="opacity-0 group-hover:opacity-100 text-accent-negative/70 hover:text-accent-negative transition-all cursor-pointer"
                        title="Remove position"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && (
        <div className="bg-accent-negative/10 border border-accent-negative/30 rounded-sm px-3 py-2.5 text-xs text-accent-negative">
          {error}
        </div>
      )}

      <button
        onClick={() => { void analyzePortfolio(); }}
        disabled={isLoading}
        className={`
          px-5 py-2 rounded-sm font-medium text-xs uppercase tracking-wider transition-all
          ${isLoading
            ? 'bg-accent-neutral/30 text-text-muted cursor-wait'
            : 'bg-accent-neutral hover:bg-accent-neutral/90 text-surface-primary cursor-pointer'
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Analyzing...
          </span>
        ) : (
          'Analyze Portfolio'
        )}
      </button>
    </div>
  );
}

// ── Cost Basis column header with help tooltip ───────────────

function CostBasisHeader() {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span className="inline-flex items-center gap-1">
      Avg. Purchase Price ($)
      <span
        className="relative"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <svg
          className="w-3.5 h-3.5 text-text-muted hover:text-text-secondary transition-colors cursor-help"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <circle cx="12" cy="12" r="10" />
          <path strokeLinecap="round" d="M12 16v-1m0-3a2 2 0 10-2-2" />
          <circle cx="12" cy="16" r="0.5" fill="currentColor" />
        </svg>
        {showTooltip && (
          <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 px-3 py-2 rounded-sm bg-surface-hover border border-border-default text-xs text-text-primary font-normal normal-case tracking-normal leading-relaxed shadow-lg shadow-black/40 pointer-events-none">
            Your average purchase price per share. Used for tax-loss harvesting analysis. Leave blank if unknown.
          </span>
        )}
      </span>
    </span>
  );
}
