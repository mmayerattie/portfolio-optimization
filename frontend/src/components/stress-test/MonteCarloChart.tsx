import { useMemo } from 'react';
import {
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts';
import type { MonteCarloOutput } from '../../types/portfolio';
import { formatCurrency, formatPercent } from '../../utils/formatters';

interface MonteCarloChartProps {
  monteCarlo: MonteCarloOutput;
  horizonYears: number;
}

interface FanDataPoint {
  month: number;
  year: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export function MonteCarloChart({ monteCarlo, horizonYears }: MonteCarloChartProps) {
  // Build fan chart data from percentiles of sample paths at each time step.
  // The sample_paths are sorted by terminal value, so we can compute running percentiles.
  const fanData = useMemo<FanDataPoint[]>(() => {
    const paths = monteCarlo.sample_paths;
    if (paths.length === 0) return [];

    const nSteps = paths[0].length;
    // Sample every ~21 trading days (monthly) for performance
    const step = Math.max(1, Math.floor(nSteps / (horizonYears * 12)));
    const data: FanDataPoint[] = [];

    for (let i = 0; i < nSteps; i += step) {
      const values = paths.map((p) => p[i]).sort((a, b) => a - b);
      const n = values.length;
      data.push({
        month: Math.round(i / 21),
        year: +(i / 252).toFixed(1),
        p5: values[Math.floor(n * 0.05)] ?? values[0],
        p25: values[Math.floor(n * 0.25)] ?? values[0],
        p50: values[Math.floor(n * 0.5)] ?? values[0],
        p75: values[Math.floor(n * 0.75)] ?? values[n - 1],
        p95: values[Math.floor(n * 0.95)] ?? values[n - 1],
      });
    }

    // Always include the last step
    const lastIdx = nSteps - 1;
    const lastValues = paths.map((p) => p[lastIdx]).sort((a, b) => a - b);
    const n = lastValues.length;
    data.push({
      month: Math.round(lastIdx / 21),
      year: +(lastIdx / 252).toFixed(1),
      p5: lastValues[Math.floor(n * 0.05)] ?? lastValues[0],
      p25: lastValues[Math.floor(n * 0.25)] ?? lastValues[0],
      p50: lastValues[Math.floor(n * 0.5)] ?? lastValues[0],
      p75: lastValues[Math.floor(n * 0.75)] ?? lastValues[n - 1],
      p95: lastValues[Math.floor(n * 0.95)] ?? lastValues[n - 1],
    });

    return data;
  }, [monteCarlo.sample_paths, horizonYears]);

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">
        Monte Carlo Simulation
      </h3>
      <p className="text-[10px] text-text-muted mb-3">
        {monteCarlo.sample_paths.length} sample paths over {horizonYears} year{horizonYears > 1 ? 's' : ''}.
        Bands show P5/P25/P50/P75/P95 percentiles.
      </p>

      {/* Summary metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div>
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Median Terminal Value</p>
          <p className="text-base font-data text-text-primary">
            {formatCurrency(monteCarlo.percentiles.p50)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Probability of Loss</p>
          <p className="text-base font-data text-accent-negative">
            {formatPercent(monteCarlo.probability_of_loss)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-text-muted uppercase tracking-wide">Expected Max Drawdown</p>
          <p className="text-base font-data text-accent-warning">
            {formatPercent(monteCarlo.expected_max_drawdown)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-text-muted uppercase tracking-wide">P5 / P95 Range</p>
          <p className="text-base font-data text-text-primary">
            {formatCurrency(monteCarlo.percentiles.p5)} – {formatCurrency(monteCarlo.percentiles.p95)}
          </p>
        </div>
      </div>

      {/* Fan chart */}
      {fanData.length > 0 && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={fanData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
              <XAxis
                dataKey="year"
                tick={{ fill: '#52525b', fontSize: 10 }}
                axisLine={{ stroke: '#1e1e1e' }}
                tickLine={{ stroke: '#1e1e1e' }}
                label={{ value: 'Years', position: 'insideBottom', offset: -5, fill: '#52525b', fontSize: 10 }}
              />
              <YAxis
                tick={{ fill: '#52525b', fontSize: 10 }}
                axisLine={{ stroke: '#1e1e1e' }}
                tickLine={{ stroke: '#1e1e1e' }}
                tickFormatter={(v: number) => {
                  if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
                  if (v >= 1000) return `$${(v / 1000).toFixed(0)}K`;
                  return `$${v.toFixed(0)}`;
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111318',
                  border: '1px solid #1e1e1e',
                  borderRadius: '2px',
                  fontSize: '11px',
                }}
                labelFormatter={(label) => `Year ${label}`}
                formatter={(value, name) => {
                  const labels: Record<string, string> = {
                    p5: 'P5 (worst case)',
                    p25: 'P25',
                    p50: 'Median (P50)',
                    p75: 'P75',
                    p95: 'P95 (best case)',
                  };
                  return [formatCurrency(Number(value)), labels[String(name)] ?? String(name)];
                }}
              />

              {/* P5-P95 band */}
              <Area dataKey="p95" stroke="none" fill="#00dc82" fillOpacity={0.06} />
              <Area dataKey="p5" stroke="none" fill="#09090b" fillOpacity={1} />

              {/* P25-P75 band */}
              <Area dataKey="p75" stroke="none" fill="#00dc82" fillOpacity={0.12} />
              <Area dataKey="p25" stroke="none" fill="#09090b" fillOpacity={1} />

              {/* Median line */}
              <Line
                dataKey="p50"
                stroke="#00dc82"
                strokeWidth={2}
                dot={false}
                type="monotone"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
