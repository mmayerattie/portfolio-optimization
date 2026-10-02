import type { RebalanceOutput } from '../../types/portfolio';
import { formatCurrency, formatPercent } from '../../utils/formatters';

interface RebalancePlanProps {
  rebalance: RebalanceOutput;
}

export function RebalancePlan({ rebalance }: RebalancePlanProps) {
  const { trades, estimated_transaction_costs, tax_loss_harvesting, turnover } = rebalance;

  return (
    <div className="space-y-4">
      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-card rounded-sm border border-border-default p-3">
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Total Trades</p>
          <p className="text-xl font-data text-text-primary">{trades.length}</p>
        </div>
        <div className="bg-surface-card rounded-sm border border-border-default p-3">
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Est. Transaction Costs</p>
          <p className="text-xl font-data text-text-primary">{formatCurrency(estimated_transaction_costs)}</p>
        </div>
        <div className="bg-surface-card rounded-sm border border-border-default p-3">
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Portfolio Turnover</p>
          <p className="text-xl font-data text-text-primary">{formatPercent(turnover)}</p>
        </div>
      </div>

      {/* Trade list */}
      <div className="bg-surface-card rounded-sm border border-border-default p-4">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Trade List</h3>

        {trades.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">
            No trades needed — portfolio is already at target weights.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-text-muted uppercase tracking-wider border-b border-border-default">
                  <th className="pb-2 pr-4">Ticker</th>
                  <th className="pb-2 pr-4">Action</th>
                  <th className="pb-2 pr-4 text-right">Shares</th>
                  <th className="pb-2 pr-4 text-right">Value</th>
                  <th className="pb-2 pr-4 text-right">Current Wt</th>
                  <th className="pb-2 text-right">Target Wt</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t) => (
                  <tr key={t.ticker} className="border-b border-border-subtle">
                    <td className="py-2.5 pr-4 font-data font-medium text-accent-neutral">
                      {t.ticker}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span
                        className={`
                          inline-flex items-center px-1.5 py-0.5 rounded-sm text-[10px] font-semibold uppercase tracking-wider
                          ${t.action === 'buy'
                            ? 'bg-accent-positive/10 text-accent-positive'
                            : 'bg-accent-negative/10 text-accent-negative'
                          }
                        `}
                      >
                        {t.action}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-right font-data text-text-primary">
                      {t.shares.toFixed(2)}
                    </td>
                    <td className="py-2.5 pr-4 text-right font-data text-text-primary">
                      {formatCurrency(t.estimated_value)}
                    </td>
                    <td className="py-2.5 pr-4 text-right font-data text-text-secondary">
                      {formatPercent(t.current_weight)}
                    </td>
                    <td className="py-2.5 text-right font-data text-text-primary">
                      {formatPercent(t.target_weight)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Tax-loss harvesting */}
      {tax_loss_harvesting.length > 0 && (
        <div className="bg-surface-card rounded-sm border border-border-default p-4">
          <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Tax-Loss Harvesting Opportunities</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-text-muted uppercase tracking-wider border-b border-border-default">
                  <th className="pb-2 pr-4">Sell</th>
                  <th className="pb-2 pr-4">Replace With</th>
                  <th className="pb-2 pr-4 text-right">Unrealized Loss</th>
                  <th className="pb-2 text-right">Est. Tax Savings</th>
                </tr>
              </thead>
              <tbody>
                {tax_loss_harvesting.map((tlh) => (
                  <tr key={tlh.ticker} className="border-b border-border-subtle">
                    <td className="py-2.5 pr-4 font-data text-accent-negative font-medium">
                      {tlh.ticker}
                    </td>
                    <td className="py-2.5 pr-4 font-data text-accent-positive font-medium">
                      {tlh.replacement_ticker}
                    </td>
                    <td className="py-2.5 pr-4 text-right font-data text-accent-negative">
                      {formatCurrency(tlh.unrealized_loss)}
                    </td>
                    <td className="py-2.5 text-right font-data text-accent-positive">
                      {formatCurrency(tlh.estimated_tax_savings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-text-muted mt-3">
            Replacement tickers are similar ETFs that avoid wash-sale rule violations.
            Consult a tax professional before executing.
          </p>
        </div>
      )}
    </div>
  );
}
