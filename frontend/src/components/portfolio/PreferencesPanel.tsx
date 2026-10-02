import { usePortfolioStore } from '../../store/portfolioStore';
import type { RiskProfile, RebalanceFrequency } from '../../types/portfolio';

export function PreferencesPanel() {
  const { preferences, setPreferences } = usePortfolioStore();

  return (
    <div className="bg-surface-card rounded-sm border border-border-default p-4 space-y-4">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide">Preferences</h3>

      {/* Investment Horizon */}
      <div>
        <label className="flex items-center justify-between text-xs text-text-muted mb-1.5">
          <span>Investment Horizon</span>
          <span className="font-data text-text-primary">{preferences.investment_horizon_years} years</span>
        </label>
        <input
          type="range"
          min={1}
          max={30}
          value={preferences.investment_horizon_years}
          onChange={(e) => setPreferences({ investment_horizon_years: parseInt(e.target.value) })}
          className="w-full h-1.5 bg-border-default rounded-full appearance-none cursor-pointer accent-accent-neutral"
        />
        <div className="flex justify-between text-[10px] text-text-muted mt-0.5">
          <span>1y</span>
          <span>30y</span>
        </div>
      </div>

      {/* Max Drawdown Tolerance */}
      <div>
        <label className="flex items-center justify-between text-xs text-text-muted mb-1.5">
          <span>Max Drawdown Tolerance</span>
          <span className="font-data text-text-primary">{(preferences.max_drawdown_tolerance * 100).toFixed(0)}%</span>
        </label>
        <input
          type="range"
          min={5}
          max={50}
          value={preferences.max_drawdown_tolerance * 100}
          onChange={(e) => setPreferences({ max_drawdown_tolerance: parseInt(e.target.value) / 100 })}
          className="w-full h-1.5 bg-border-default rounded-full appearance-none cursor-pointer accent-accent-neutral"
        />
        <div className="flex justify-between text-[10px] text-text-muted mt-0.5">
          <span>5%</span>
          <span>50%</span>
        </div>
      </div>

      {/* Risk Profile */}
      <div>
        <label className="block text-xs text-text-muted mb-1.5">Risk Profile</label>
        <div className="flex gap-2">
          {(['conservative', 'moderate', 'aggressive'] as RiskProfile[]).map((profile) => (
            <button
              key={profile}
              onClick={() => setPreferences({ risk_profile: profile })}
              className={`
                flex-1 py-1.5 rounded-md text-xs font-medium capitalize transition-colors cursor-pointer
                ${preferences.risk_profile === profile
                  ? 'bg-accent-neutral/20 text-accent-neutral border border-accent-neutral/40'
                  : 'bg-surface-primary text-text-secondary border border-border-default hover:border-border-default/80'
                }
              `}
            >
              {profile}
            </button>
          ))}
        </div>
      </div>

      {/* Rebalance Frequency */}
      <div>
        <label className="block text-xs text-text-muted mb-1.5">Rebalance Frequency</label>
        <select
          value={preferences.rebalance_frequency}
          onChange={(e) => setPreferences({ rebalance_frequency: e.target.value as RebalanceFrequency })}
          className="w-full bg-surface-primary border border-border-default rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent-neutral/50 cursor-pointer"
        >
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
          <option value="annual">Annual</option>
          <option value="band-based">Band-based</option>
        </select>
      </div>

      {/* Benchmark */}
      <div>
        <label className="block text-xs text-text-muted mb-1.5">Benchmark</label>
        <input
          type="text"
          value={preferences.benchmark}
          onChange={(e) => setPreferences({ benchmark: e.target.value.toUpperCase() })}
          className="w-full bg-surface-primary border border-border-default rounded-md px-3 py-1.5 text-sm font-data text-text-primary focus:outline-none focus:border-accent-neutral/50"
        />
      </div>

      {/* Tax Optimization Toggle */}
      <label className="flex items-center justify-between cursor-pointer">
        <span className="text-xs text-text-muted">Include Tax Optimization</span>
        <button
          onClick={() => setPreferences({ include_tax_optimization: !preferences.include_tax_optimization })}
          className={`
            relative w-9 h-5 rounded-full transition-colors cursor-pointer
            ${preferences.include_tax_optimization ? 'bg-accent-neutral' : 'bg-border-default'}
          `}
        >
          <span
            className={`
              absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform
              ${preferences.include_tax_optimization ? 'translate-x-4' : 'translate-x-0'}
            `}
          />
        </button>
      </label>
    </div>
  );
}
