import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { RiskContributionItem } from '../../types/portfolio';
import { formatPercent } from '../../utils/formatters';

// Colors for bars — cycle through these (Bloomberg terminal palette)
const BAR_COLORS = [
  '#00dc82', // terminal green
  '#f59e0b', // amber
  '#06b6d4', // cyan
  '#e879f9', // magenta
  '#ef4444', // red
  '#22d3ee', // light cyan
  '#fbbf24', // gold
  '#a78bfa', // violet
];

interface RiskContributionProps {
  contributions: RiskContributionItem[];
}

interface ChartDataItem {
  ticker: string;
  weight: number;
  riskPct: number;
}

export function RiskContribution({ contributions }: RiskContributionProps) {
  const data: ChartDataItem[] = contributions
    .map((c) => ({
      ticker: c.ticker,
      weight: c.weight * 100,
      riskPct: c.percentage_risk_contribution * 100,
    }))
    .sort((a, b) => b.riskPct - a.riskPct);

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">
        Risk Contribution by Asset
      </h3>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 20, bottom: 0, left: 50 }}
          >
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              tick={{ fill: '#52525b', fontSize: 11 }}
              axisLine={{ stroke: '#1e1e1e' }}
              tickLine={{ stroke: '#1e1e1e' }}
            />
            <YAxis
              type="category"
              dataKey="ticker"
              tick={{ fill: '#a1a1aa', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111318',
                border: '1px solid #1e1e1e',
                borderRadius: '2px',
                fontSize: '11px',
              }}
              labelStyle={{ color: '#e4e4e7', fontWeight: 600 }}
              formatter={(value) => {
                return [`${Number(value).toFixed(1)}%`, 'Risk Contribution'];
              }}
            />
            <Bar dataKey="riskPct" name="riskPct" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((_, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend table */}
      <div className="mt-4 border-t border-border-default pt-3">
        <div className="grid grid-cols-3 gap-2 text-xs text-text-muted mb-1">
          <span>Asset</span>
          <span className="text-right">Weight</span>
          <span className="text-right">Risk Contribution</span>
        </div>
        {data.map((d, i) => (
          <div key={d.ticker} className="grid grid-cols-3 gap-2 text-sm py-1">
            <span className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: BAR_COLORS[i % BAR_COLORS.length] }}
              />
              <span className="font-data text-text-primary">{d.ticker}</span>
            </span>
            <span className="text-right font-data text-text-secondary">
              {formatPercent(d.weight / 100)}
            </span>
            <span className="text-right font-data text-text-primary">
              {formatPercent(d.riskPct / 100)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
