import { Layout } from './components/layout/Layout';
import { PortfolioInput } from './components/portfolio/PortfolioInput';
import { PreferencesPanel } from './components/portfolio/PreferencesPanel';
import { DiagnosticDashboard } from './components/analysis/DiagnosticDashboard';
import { EfficientFrontier } from './components/optimization/EfficientFrontier';
import { OptimalPortfolio } from './components/optimization/OptimalPortfolio';
import { Recommendations } from './components/optimization/Recommendations';
import { ScenarioAnalysis } from './components/stress-test/ScenarioAnalysis';
import { MonteCarloChart } from './components/stress-test/MonteCarloChart';
import { RebalancePlan } from './components/rebalance/RebalancePlan';
import { AlertsPanel } from './components/rebalance/AlertsPanel';
import { usePortfolioStore } from './store/portfolioStore';

function Disclaimer() {
  return (
    <p className="text-[10px] text-text-muted mt-8">
      This tool is for educational purposes only. It is not financial advice.
      Past performance does not guarantee future results. All projections are
      based on historical data and statistical models that may not reflect
      future market conditions.
    </p>
  );
}

function InputPage() {
  return (
    <div className="flex gap-6 max-w-6xl">
      <div className="flex-1">
        <PortfolioInput />
      </div>
      <div className="w-72 shrink-0">
        <PreferencesPanel />
      </div>
    </div>
  );
}

function OptimizationPage() {
  const { analysis } = usePortfolioStore();
  if (!analysis) return null;

  const { optimization } = analysis;

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">Portfolio Optimization</h2>
        <p className="text-sm text-text-secondary mt-1">
          Efficient frontier, optimal allocations, and portfolio comparisons.
        </p>
      </div>

      <EfficientFrontier
        frontier={optimization.efficient_frontier}
        currentPoint={optimization.current_portfolio_point}
        optimalPortfolio={optimization.optimal_portfolio}
        minVariancePoint={optimization.min_variance_portfolio}
      />

      <OptimalPortfolio optimization={optimization} />

      <Recommendations suggestions={optimization.new_assets_suggested} />
      <Disclaimer />
    </div>
  );
}

function StressTestPage() {
  const { analysis, preferences } = usePortfolioStore();
  if (!analysis) return null;

  const { stress_test } = analysis;

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">Stress Testing</h2>
        <p className="text-sm text-text-secondary mt-1">
          How your portfolio would perform under historical crises and simulated scenarios.
        </p>
      </div>

      <ScenarioAnalysis scenarios={stress_test.scenarios} />
      <MonteCarloChart
        monteCarlo={stress_test.monte_carlo}
        horizonYears={preferences.investment_horizon_years}
      />
      <Disclaimer />
    </div>
  );
}

function RebalancePage() {
  const { analysis } = usePortfolioStore();
  if (!analysis) return null;

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">Rebalance Plan</h2>
        <p className="text-sm text-text-secondary mt-1">
          Concrete trades to move from your current allocation to the suggested portfolio.
        </p>
      </div>

      <RebalancePlan rebalance={analysis.rebalance} />
      <Disclaimer />
    </div>
  );
}

function MonitoringPage() {
  const { analysis } = usePortfolioStore();
  if (!analysis) return null;

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">Monitoring Rules</h2>
        <p className="text-sm text-text-secondary mt-1">
          Ongoing alerts, rebalance triggers, and risk budget rules.
        </p>
      </div>

      <AlertsPanel monitoring={analysis.monitoring} />
      <Disclaimer />
    </div>
  );
}

export function App() {
  const { activeTab } = usePortfolioStore();

  return (
    <Layout>
      {activeTab === 'input' && <InputPage />}
      {activeTab === 'diagnostic' && <DiagnosticDashboard />}
      {activeTab === 'optimization' && <OptimizationPage />}
      {activeTab === 'stress-test' && <StressTestPage />}
      {activeTab === 'rebalance' && <RebalancePage />}
      {activeTab === 'monitoring' && <MonitoringPage />}
    </Layout>
  );
}
