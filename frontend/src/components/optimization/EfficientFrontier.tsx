import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { FrontierPoint, PortfolioPoint, WeightedPortfolio } from '../../types/portfolio';
import { formatPercent, formatRatio } from '../../utils/formatters';

interface EfficientFrontierProps {
  frontier: FrontierPoint[];
  currentPoint: PortfolioPoint;
  optimalPortfolio: WeightedPortfolio;
  minVariancePoint: { expected_return: number; volatility: number };
}

interface HoveredPoint {
  x: number;
  y: number;
  data: FrontierPoint;
}

const MARGIN = { top: 24, right: 24, bottom: 48, left: 56 };

export function EfficientFrontier({
  frontier,
  currentPoint,
  optimalPortfolio,
  minVariancePoint,
}: EfficientFrontierProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<HoveredPoint | null>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

  // Responsive sizing
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      setDimensions({ width, height: Math.min(width * 0.6, 450) });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!svgRef.current || frontier.length < 2) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    // Collect all points for domain computation
    const allVols = [
      ...frontier.map((p) => p.volatility),
      currentPoint.volatility,
      optimalPortfolio.volatility,
    ];
    const allRets = [
      ...frontier.map((p) => p.expected_return),
      currentPoint.expected_return,
      optimalPortfolio.expected_return,
    ];

    const xPad = (d3.max(allVols)! - d3.min(allVols)!) * 0.15 || 0.01;
    const yPad = (d3.max(allRets)! - d3.min(allRets)!) * 0.15 || 0.01;

    const xScale = d3
      .scaleLinear()
      .domain([d3.min(allVols)! - xPad, d3.max(allVols)! + xPad])
      .range([0, innerW]);

    const yScale = d3
      .scaleLinear()
      .domain([d3.min(allRets)! - yPad, d3.max(allRets)! + yPad])
      .range([innerH, 0]);

    const g = svg
      .append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid lines
    g.append('g')
      .attr('class', 'grid')
      .selectAll('line')
      .data(yScale.ticks(6))
      .join('line')
      .attr('x1', 0)
      .attr('x2', innerW)
      .attr('y1', (d) => yScale(d))
      .attr('y2', (d) => yScale(d))
      .attr('stroke', '#1e1e1e')
      .attr('stroke-dasharray', '2,4');

    g.append('g')
      .attr('class', 'grid')
      .selectAll('line')
      .data(xScale.ticks(6))
      .join('line')
      .attr('x1', (d) => xScale(d))
      .attr('x2', (d) => xScale(d))
      .attr('y1', 0)
      .attr('y2', innerH)
      .attr('stroke', '#1e1e1e')
      .attr('stroke-dasharray', '2,4');

    // Axes
    const xAxis = d3.axisBottom(xScale).ticks(6).tickFormat((d) => formatPercent(d as number, 1));
    const yAxis = d3.axisLeft(yScale).ticks(6).tickFormat((d) => formatPercent(d as number, 1));

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(xAxis)
      .call((sel) => {
        sel.selectAll('text').attr('fill', '#52525b').attr('font-size', '10px');
        sel.selectAll('line').attr('stroke', '#1e1e1e');
        sel.select('.domain').attr('stroke', '#1e1e1e');
      });

    g.append('g')
      .call(yAxis)
      .call((sel) => {
        sel.selectAll('text').attr('fill', '#52525b').attr('font-size', '10px');
        sel.selectAll('line').attr('stroke', '#1e1e1e');
        sel.select('.domain').attr('stroke', '#1e1e1e');
      });

    // Axis labels
    svg
      .append('text')
      .attr('x', MARGIN.left + innerW / 2)
      .attr('y', height - 6)
      .attr('text-anchor', 'middle')
      .attr('fill', '#52525b')
      .attr('font-size', '10px')
      .text('Volatility (Annualized)');

    svg
      .append('text')
      .attr('transform', `rotate(-90)`)
      .attr('x', -(MARGIN.top + innerH / 2))
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', '#52525b')
      .attr('font-size', '10px')
      .text('Expected Return (Annualized)');

    // Efficient frontier curve
    const line = d3
      .line<FrontierPoint>()
      .x((d) => xScale(d.volatility))
      .y((d) => yScale(d.expected_return))
      .curve(d3.curveCatmullRom.alpha(0.5));

    g.append('path')
      .datum(frontier)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', '#00dc82')
      .attr('stroke-width', 2)
      .attr('stroke-linecap', 'round');

    // Frontier dots (invisible but hoverable)
    g.selectAll('.frontier-dot')
      .data(frontier)
      .join('circle')
      .attr('class', 'frontier-dot')
      .attr('cx', (d) => xScale(d.volatility))
      .attr('cy', (d) => yScale(d.expected_return))
      .attr('r', 5)
      .attr('fill', 'transparent')
      .attr('stroke', 'transparent')
      .attr('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        const rect = svgRef.current!.getBoundingClientRect();
        setHovered({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
          data: d,
        });
      })
      .on('mouseleave', () => setHovered(null));

    // Current portfolio (red)
    g.append('circle')
      .attr('cx', xScale(currentPoint.volatility))
      .attr('cy', yScale(currentPoint.expected_return))
      .attr('r', 6)
      .attr('fill', '#ef4444')
      .attr('stroke', '#09090b')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', xScale(currentPoint.volatility) + 10)
      .attr('y', yScale(currentPoint.expected_return) + 4)
      .attr('fill', '#ef4444')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('font-family', 'JetBrains Mono')
      .text('CURRENT');

    // Optimal / Max Sharpe (terminal green)
    g.append('circle')
      .attr('cx', xScale(optimalPortfolio.volatility))
      .attr('cy', yScale(optimalPortfolio.expected_return))
      .attr('r', 6)
      .attr('fill', '#00dc82')
      .attr('stroke', '#09090b')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', xScale(optimalPortfolio.volatility) + 10)
      .attr('y', yScale(optimalPortfolio.expected_return) + 4)
      .attr('fill', '#00dc82')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('font-family', 'JetBrains Mono')
      .text('MAX SHARPE');

    // Min variance (cyan)
    g.append('circle')
      .attr('cx', xScale(minVariancePoint.volatility))
      .attr('cy', yScale(minVariancePoint.expected_return))
      .attr('r', 5)
      .attr('fill', '#06b6d4')
      .attr('stroke', '#09090b')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', xScale(minVariancePoint.volatility) + 10)
      .attr('y', yScale(minVariancePoint.expected_return) + 4)
      .attr('fill', '#06b6d4')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('font-family', 'JetBrains Mono')
      .text('MIN VAR');
  }, [frontier, currentPoint, optimalPortfolio, minVariancePoint, dimensions]);

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">
        Efficient Frontier
      </h3>
      <p className="text-[10px] text-text-muted mb-3">
        Hover over the curve to see portfolio allocations at each risk/return point.
      </p>

      <div ref={containerRef} className="relative">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="overflow-visible"
        />

        {/* Hover tooltip */}
        {hovered && (
          <div
            className="absolute z-10 bg-surface-card border border-border-default rounded-sm p-2.5 shadow-lg pointer-events-none text-[11px]"
            style={{
              left: Math.min(hovered.x + 16, dimensions.width - 200),
              top: hovered.y - 10,
            }}
          >
            <div className="space-y-1">
              <div className="flex justify-between gap-4">
                <span className="text-text-muted">Return</span>
                <span className="font-data text-text-primary">
                  {formatPercent(hovered.data.expected_return)}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-text-muted">Volatility</span>
                <span className="font-data text-text-primary">
                  {formatPercent(hovered.data.volatility)}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-text-muted">Sharpe</span>
                <span className="font-data text-text-primary">
                  {formatRatio(hovered.data.sharpe_ratio)}
                </span>
              </div>
              <div className="border-t border-border-default mt-1 pt-1">
                {Object.entries(hovered.data.weights)
                  .filter(([, w]) => w > 0.001)
                  .sort(([, a], [, b]) => b - a)
                  .map(([ticker, weight]) => (
                    <div key={ticker} className="flex justify-between gap-4">
                      <span className="text-accent-neutral font-data">{ticker}</span>
                      <span className="font-data text-text-secondary">
                        {formatPercent(weight)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-5 mt-3 text-[10px] text-text-muted uppercase tracking-wide">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#ef4444]" /> Current
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#00dc82]" /> Max Sharpe
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#06b6d4]" /> Min Variance
        </span>
      </div>
    </div>
  );
}
