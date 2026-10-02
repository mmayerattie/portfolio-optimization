import type { MonitoringOutput } from '../../types/portfolio';
import { formatPercent } from '../../utils/formatters';

interface AlertsPanelProps {
  monitoring: MonitoringOutput;
}

export function AlertsPanel({ monitoring }: AlertsPanelProps) {
  const { rebalance_bands, alerts, next_review_date, risk_budget_rules } = monitoring;

  return (
    <div className="space-y-4">
      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="bg-accent-warning/5 border border-accent-warning/20 rounded-sm p-4">
          <h3 className="text-xs font-medium text-accent-warning uppercase tracking-wide mb-2">Active Alerts</h3>
          <div className="space-y-2">
            {alerts.map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-text-primary">
                <svg className="w-4 h-4 text-accent-warning mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
                </svg>
                {a}
              </div>
            ))}
          </div>
        </div>
      )}

      {alerts.length === 0 && (
        <div className="bg-accent-positive/5 border border-accent-positive/20 rounded-sm p-3">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-accent-positive" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-accent-positive font-medium uppercase tracking-wide">All positions within rebalance bands.</p>
          </div>
        </div>
      )}

      {/* Next Review */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1.5">Next Review Date</h3>
        <p className="text-xl font-data text-accent-neutral">{next_review_date}</p>
      </div>

      {/* Rebalance Bands */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Rebalance Trigger Bands</h3>
        <p className="text-xs text-text-muted mb-3">
          If any asset drifts outside its band, a rebalance is triggered.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted uppercase tracking-wider border-b border-border-default">
                <th className="pb-2 pr-4">Ticker</th>
                <th className="pb-2 pr-4 text-right">Lower Bound</th>
                <th className="pb-2 text-right">Upper Bound</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(rebalance_bands).map(([ticker, band]) => (
                <tr key={ticker} className="border-b border-border-subtle">
                  <td className="py-2 pr-4 font-data font-medium text-accent-neutral">{ticker}</td>
                  <td className="py-2 pr-4 text-right font-data text-text-primary">
                    {formatPercent(band.lower)}
                  </td>
                  <td className="py-2 text-right font-data text-text-primary">
                    {formatPercent(band.upper)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Risk Budget Rules */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Risk Budget Rules</h3>
        <div className="space-y-2">
          {risk_budget_rules.map((rule, i) => (
            <div key={i} className="flex items-start gap-3 text-sm text-text-primary">
              <span className="font-data text-accent-neutral shrink-0 w-5 text-right">{i + 1}.</span>
              {rule}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
