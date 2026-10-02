import { usePortfolioStore } from '../../store/portfolioStore';
import type { AppTab } from '../../types/portfolio';

interface NavItem {
  id: AppTab;
  label: string;
  icon: string;
  requiresAnalysis: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'input', label: 'Portfolio Input', icon: 'M12 4.5v15m7.5-7.5h-15', requiresAnalysis: false },
  { id: 'diagnostic', label: 'Diagnostic', icon: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z', requiresAnalysis: true },
  { id: 'optimization', label: 'Optimization', icon: 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941', requiresAnalysis: true },
  { id: 'stress-test', label: 'Stress Test', icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z', requiresAnalysis: true },
  { id: 'rebalance', label: 'Rebalance', icon: 'M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5', requiresAnalysis: true },
  { id: 'monitoring', label: 'Monitoring', icon: 'M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0', requiresAnalysis: true },
];

export function Sidebar() {
  const { activeTab, setActiveTab, analysis } = usePortfolioStore();

  return (
    <nav className="w-52 border-r border-border-default bg-surface-card flex flex-col shrink-0">
      <div className="flex-1 py-2 space-y-0.5 px-2">
        {NAV_ITEMS.map((item) => {
          const disabled = item.requiresAnalysis && !analysis;
          const active = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => !disabled && setActiveTab(item.id)}
              disabled={disabled}
              className={`
                w-full flex items-center gap-2.5 px-2.5 py-2 rounded-sm text-xs font-medium
                transition-colors duration-100 text-left
                ${active
                  ? 'bg-accent-neutral/10 text-accent-neutral border-l-2 border-accent-neutral'
                  : disabled
                    ? 'text-text-muted cursor-not-allowed opacity-40'
                    : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary cursor-pointer'
                }
              `}
            >
              <svg
                className="w-4 h-4 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="p-3 border-t border-border-default">
        <p className="text-[9px] text-text-muted leading-relaxed">
          This tool is for educational purposes only. It is not financial advice.
          Past performance does not guarantee future results.
        </p>
      </div>
    </nav>
  );
}
