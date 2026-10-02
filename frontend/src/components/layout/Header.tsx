export function Header() {
  return (
    <header className="h-12 border-b border-border-default bg-surface-card flex items-center justify-between px-5 shrink-0">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-sm bg-accent-neutral/10 flex items-center justify-center">
          <svg
            className="w-4 h-4 text-accent-neutral"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
            />
          </svg>
        </div>
        <h1 className="text-sm font-semibold text-accent-neutral uppercase tracking-wider font-mono">
          Portfolio Optimizer
        </h1>
      </div>
      <span className="text-[10px] text-text-muted uppercase tracking-wide">
        Educational purposes only — not financial advice
      </span>
    </header>
  );
}
