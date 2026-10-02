interface CorrelationMatrixProps {
  matrix: number[][];
  tickers: string[];
}

/**
 * Interpolate between cyan (-1) → near-black (0) → red (+1).
 * Bloomberg-style terminal palette.
 */
function correlationColor(value: number): string {
  if (value >= 0) {
    // 0 → 1: near-black (#111318) → red (#ef4444)
    const t = Math.min(value, 1);
    const r = Math.round(17 + t * (239 - 17));
    const g = Math.round(19 + t * (68 - 19));
    const b = Math.round(24 + t * (68 - 24));
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    // -1 → 0: cyan (#06b6d4) → near-black (#111318)
    const t = Math.min(-value, 1);
    const r = Math.round(17 - t * (17 - 6));
    const g = Math.round(19 + t * (182 - 19));
    const b = Math.round(24 + t * (212 - 24));
    return `rgb(${r}, ${g}, ${b})`;
  }
}

function textColorForBg(value: number): string {
  return Math.abs(value) > 0.5 ? '#e4e4e7' : '#52525b';
}

export function CorrelationMatrix({ matrix, tickers }: CorrelationMatrixProps) {
  if (matrix.length === 0) return null;

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">
        Correlation Matrix
      </h3>

      <div className="overflow-x-auto">
        <table className="border-collapse">
          <thead>
            <tr>
              <th className="w-16" />
              {tickers.map((t) => (
                <th
                  key={t}
                  className="px-2 py-2 text-xs font-data text-text-muted text-center min-w-[56px]"
                >
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={tickers[i]}>
                <td className="px-2 py-1 text-xs font-data text-text-muted text-right pr-3">
                  {tickers[i]}
                </td>
                {row.map((val, j) => (
                  <td
                    key={j}
                    className="px-2 py-2 text-center text-xs font-data min-w-[56px] rounded-sm"
                    style={{
                      backgroundColor: correlationColor(val),
                      color: textColorForBg(val),
                    }}
                    title={`${tickers[i]} / ${tickers[j]}: ${val.toFixed(4)}`}
                  >
                    {val.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Color scale legend */}
      <div className="mt-3 flex items-center gap-2 text-[10px] text-text-muted">
        <span>-1.0</span>
        <div
          className="flex-1 h-2.5 rounded-sm"
          style={{
            background: 'linear-gradient(to right, rgb(6,182,212), rgb(17,19,24), rgb(239,68,68))',
          }}
        />
        <span>+1.0</span>
      </div>
    </div>
  );
}
