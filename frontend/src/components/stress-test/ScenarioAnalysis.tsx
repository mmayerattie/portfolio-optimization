import type { ScenarioItem } from '../../types/portfolio';
import { formatPercent } from '../../utils/formatters';

interface ScenarioAnalysisProps {
  scenarios: ScenarioItem[];
}

function returnColor(value: number): string {
  if (value >= 0.05) return 'text-accent-positive bg-accent-positive/10';
  if (value >= 0) return 'text-accent-positive/70 bg-accent-positive/5';
  if (value >= -0.15) return 'text-accent-negative/70 bg-accent-negative/5';
  return 'text-accent-negative bg-accent-negative/10';
}

export function ScenarioAnalysis({ scenarios }: ScenarioAnalysisProps) {
  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">
        Historical Scenario Analysis
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-muted uppercase tracking-wider border-b border-border-default">
              <th className="pb-2 pr-4">Scenario</th>
              <th className="pb-2 pr-4 text-right">Current Portfolio</th>
              <th className="pb-2 pr-4 text-right">Optimized</th>
              <th className="pb-2 text-right">Improvement</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s) => {
              const delta = s.optimized_portfolio_return - s.current_portfolio_return;
              return (
                <tr key={s.name} className="border-b border-border-subtle">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-text-primary">{s.name}</div>
                    <div className="text-xs text-text-muted mt-0.5">{s.description}</div>
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <span className={`font-data px-2 py-0.5 rounded ${returnColor(s.current_portfolio_return)}`}>
                      {formatPercent(s.current_portfolio_return)}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <span className={`font-data px-2 py-0.5 rounded ${returnColor(s.optimized_portfolio_return)}`}>
                      {formatPercent(s.optimized_portfolio_return)}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <span className={`font-data text-xs ${delta >= 0 ? 'text-accent-positive' : 'text-accent-negative'}`}>
                      {delta >= 0 ? '+' : ''}{formatPercent(delta)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
