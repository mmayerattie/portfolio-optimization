import { useState, useRef, useEffect, useCallback } from 'react';

// ── Static ticker database ───────────────────────────────────

interface TickerEntry {
  symbol: string;
  name: string;
}

const TICKER_DATABASE: TickerEntry[] = [
  // ── Special ──
  { symbol: 'CASH', name: 'Cash (USD) — enter dollar amount as shares' },
  // ── US Equity ETFs ──
  { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust' },
  { symbol: 'VOO', name: 'Vanguard S&P 500 ETF' },
  { symbol: 'IVV', name: 'iShares Core S&P 500 ETF' },
  { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF' },
  { symbol: 'QQQ', name: 'Invesco QQQ Trust' },
  { symbol: 'QQQM', name: 'Invesco Nasdaq 100 ETF' },
  { symbol: 'IWM', name: 'iShares Russell 2000 ETF' },
  { symbol: 'IWF', name: 'iShares Russell 1000 Growth ETF' },
  { symbol: 'IWD', name: 'iShares Russell 1000 Value ETF' },
  { symbol: 'VUG', name: 'Vanguard Growth ETF' },
  { symbol: 'VTV', name: 'Vanguard Value ETF' },
  { symbol: 'VIG', name: 'Vanguard Dividend Appreciation ETF' },
  { symbol: 'VYM', name: 'Vanguard High Dividend Yield ETF' },
  { symbol: 'SCHD', name: 'Schwab US Dividend Equity ETF' },
  { symbol: 'DIA', name: 'SPDR Dow Jones Industrial Average ETF' },
  { symbol: 'MDY', name: 'SPDR S&P MidCap 400 ETF' },
  { symbol: 'IJH', name: 'iShares Core S&P Mid-Cap ETF' },
  { symbol: 'IJR', name: 'iShares Core S&P Small-Cap ETF' },
  { symbol: 'RSP', name: 'Invesco S&P 500 Equal Weight ETF' },
  { symbol: 'SPLG', name: 'SPDR Portfolio S&P 500 ETF' },
  // ── Sector ETFs ──
  { symbol: 'XLK', name: 'Technology Select Sector SPDR' },
  { symbol: 'XLF', name: 'Financial Select Sector SPDR' },
  { symbol: 'XLV', name: 'Health Care Select Sector SPDR' },
  { symbol: 'XLE', name: 'Energy Select Sector SPDR' },
  { symbol: 'XLY', name: 'Consumer Discretionary Select Sector SPDR' },
  { symbol: 'XLP', name: 'Consumer Staples Select Sector SPDR' },
  { symbol: 'XLI', name: 'Industrial Select Sector SPDR' },
  { symbol: 'XLU', name: 'Utilities Select Sector SPDR' },
  { symbol: 'XLB', name: 'Materials Select Sector SPDR' },
  { symbol: 'XLRE', name: 'Real Estate Select Sector SPDR' },
  { symbol: 'XLC', name: 'Communication Services Select Sector SPDR' },
  { symbol: 'SMH', name: 'VanEck Semiconductor ETF' },
  { symbol: 'XBI', name: 'SPDR S&P Biotech ETF' },
  { symbol: 'ITB', name: 'iShares US Home Construction ETF' },
  { symbol: 'XHB', name: 'SPDR S&P Homebuilders ETF' },
  { symbol: 'KRE', name: 'SPDR S&P Regional Banking ETF' },
  // ── International Equity ETFs ──
  { symbol: 'VEA', name: 'Vanguard FTSE Developed Markets ETF' },
  { symbol: 'VWO', name: 'Vanguard FTSE Emerging Markets ETF' },
  { symbol: 'VXUS', name: 'Vanguard Total International Stock ETF' },
  { symbol: 'EFA', name: 'iShares MSCI EAFE ETF' },
  { symbol: 'EEM', name: 'iShares MSCI Emerging Markets ETF' },
  { symbol: 'IEMG', name: 'iShares Core MSCI Emerging Markets ETF' },
  { symbol: 'ACWI', name: 'iShares MSCI ACWI ETF' },
  { symbol: 'IXUS', name: 'iShares Core MSCI Total International ETF' },
  { symbol: 'FXI', name: 'iShares China Large-Cap ETF' },
  { symbol: 'EWJ', name: 'iShares MSCI Japan ETF' },
  { symbol: 'EWZ', name: 'iShares MSCI Brazil ETF' },
  { symbol: 'EWG', name: 'iShares MSCI Germany ETF' },
  { symbol: 'EWU', name: 'iShares MSCI United Kingdom ETF' },
  { symbol: 'INDA', name: 'iShares MSCI India ETF' },
  { symbol: 'KWEB', name: 'KraneShares CSI China Internet ETF' },
  // ── Fixed Income ETFs ──
  { symbol: 'AGG', name: 'iShares Core US Aggregate Bond ETF' },
  { symbol: 'BND', name: 'Vanguard Total Bond Market ETF' },
  { symbol: 'TLT', name: 'iShares 20+ Year Treasury Bond ETF' },
  { symbol: 'IEF', name: 'iShares 7-10 Year Treasury Bond ETF' },
  { symbol: 'SHY', name: 'iShares 1-3 Year Treasury Bond ETF' },
  { symbol: 'SHV', name: 'iShares Short Treasury Bond ETF' },
  { symbol: 'TIP', name: 'iShares TIPS Bond ETF' },
  { symbol: 'LQD', name: 'iShares iBoxx Investment Grade Corporate Bond ETF' },
  { symbol: 'HYG', name: 'iShares iBoxx High Yield Corporate Bond ETF' },
  { symbol: 'JNK', name: 'SPDR Bloomberg High Yield Bond ETF' },
  { symbol: 'MUB', name: 'iShares National Muni Bond ETF' },
  { symbol: 'VCSH', name: 'Vanguard Short-Term Corporate Bond ETF' },
  { symbol: 'VCIT', name: 'Vanguard Intermediate-Term Corporate Bond ETF' },
  { symbol: 'VGSH', name: 'Vanguard Short-Term Treasury ETF' },
  { symbol: 'VGIT', name: 'Vanguard Intermediate-Term Treasury ETF' },
  { symbol: 'VGLT', name: 'Vanguard Long-Term Treasury ETF' },
  { symbol: 'BNDX', name: 'Vanguard Total International Bond ETF' },
  { symbol: 'EMB', name: 'iShares JP Morgan USD Emerging Markets Bond ETF' },
  { symbol: 'GOVT', name: 'iShares US Treasury Bond ETF' },
  { symbol: 'BIL', name: 'SPDR Bloomberg 1-3 Month T-Bill ETF' },
  // ── Commodities & Real Assets ──
  { symbol: 'GLD', name: 'SPDR Gold Shares' },
  { symbol: 'IAU', name: 'iShares Gold Trust' },
  { symbol: 'SLV', name: 'iShares Silver Trust' },
  { symbol: 'DBC', name: 'Invesco DB Commodity Index Tracking Fund' },
  { symbol: 'GSG', name: 'iShares GSCI Commodity Dynamic Roll Strategy ETF' },
  { symbol: 'USO', name: 'United States Oil Fund' },
  { symbol: 'UNG', name: 'United States Natural Gas Fund' },
  { symbol: 'PDBC', name: 'Invesco Optimum Yield Diversified Commodity Strategy ETF' },
  // ── REITs ──
  { symbol: 'VNQ', name: 'Vanguard Real Estate ETF' },
  { symbol: 'VNQI', name: 'Vanguard Global ex-US Real Estate ETF' },
  { symbol: 'IYR', name: 'iShares US Real Estate ETF' },
  { symbol: 'SCHH', name: 'Schwab US REIT ETF' },
  // ── Factor ETFs ──
  { symbol: 'MTUM', name: 'iShares MSCI USA Momentum Factor ETF' },
  { symbol: 'VLUE', name: 'iShares MSCI USA Value Factor ETF' },
  { symbol: 'QUAL', name: 'iShares MSCI USA Quality Factor ETF' },
  { symbol: 'SIZE', name: 'iShares MSCI USA Size Factor ETF' },
  { symbol: 'USMV', name: 'iShares MSCI USA Min Vol Factor ETF' },
  { symbol: 'DGRO', name: 'iShares Core Dividend Growth ETF' },
  // ── Multi-Asset / Allocation ──
  { symbol: 'AOR', name: 'iShares Core Growth Allocation ETF' },
  { symbol: 'AOA', name: 'iShares Core Aggressive Allocation ETF' },
  { symbol: 'AOM', name: 'iShares Core Moderate Allocation ETF' },
  { symbol: 'AOK', name: 'iShares Core Conservative Allocation ETF' },
  // ── Leveraged / Inverse (use with caution) ──
  { symbol: 'TQQQ', name: 'ProShares UltraPro QQQ' },
  { symbol: 'SQQQ', name: 'ProShares UltraPro Short QQQ' },
  { symbol: 'UPRO', name: 'ProShares UltraPro S&P 500' },
  { symbol: 'SPXU', name: 'ProShares UltraPro Short S&P 500' },
  { symbol: 'TNA', name: 'Direxion Daily Small Cap Bull 3X' },
  { symbol: 'TMF', name: 'Direxion Daily 20+ Year Treasury Bull 3X' },
  // ── Popular Stocks: Mega-Cap Tech ──
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  { symbol: 'GOOGL', name: 'Alphabet Inc. Class A' },
  { symbol: 'GOOG', name: 'Alphabet Inc. Class C' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  { symbol: 'META', name: 'Meta Platforms Inc.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'AVGO', name: 'Broadcom Inc.' },
  { symbol: 'ORCL', name: 'Oracle Corporation' },
  { symbol: 'ADBE', name: 'Adobe Inc.' },
  { symbol: 'CRM', name: 'Salesforce Inc.' },
  { symbol: 'AMD', name: 'Advanced Micro Devices Inc.' },
  { symbol: 'INTC', name: 'Intel Corporation' },
  { symbol: 'CSCO', name: 'Cisco Systems Inc.' },
  { symbol: 'NFLX', name: 'Netflix Inc.' },
  // ── Popular Stocks: Financials ──
  { symbol: 'BRK.B', name: 'Berkshire Hathaway Class B' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'MA', name: 'Mastercard Inc.' },
  { symbol: 'BAC', name: 'Bank of America Corporation' },
  { symbol: 'GS', name: 'Goldman Sachs Group Inc.' },
  { symbol: 'MS', name: 'Morgan Stanley' },
  { symbol: 'WFC', name: 'Wells Fargo & Company' },
  { symbol: 'C', name: 'Citigroup Inc.' },
  { symbol: 'BLK', name: 'BlackRock Inc.' },
  { symbol: 'SCHW', name: 'Charles Schwab Corporation' },
  { symbol: 'AXP', name: 'American Express Company' },
  // ── Popular Stocks: Healthcare ──
  { symbol: 'UNH', name: 'UnitedHealth Group Inc.' },
  { symbol: 'JNJ', name: 'Johnson & Johnson' },
  { symbol: 'LLY', name: 'Eli Lilly and Company' },
  { symbol: 'PFE', name: 'Pfizer Inc.' },
  { symbol: 'ABBV', name: 'AbbVie Inc.' },
  { symbol: 'MRK', name: 'Merck & Co. Inc.' },
  { symbol: 'TMO', name: 'Thermo Fisher Scientific Inc.' },
  { symbol: 'ABT', name: 'Abbott Laboratories' },
  { symbol: 'AMGN', name: 'Amgen Inc.' },
  { symbol: 'BMY', name: 'Bristol-Myers Squibb Company' },
  { symbol: 'ISRG', name: 'Intuitive Surgical Inc.' },
  // ── Popular Stocks: Consumer / Retail ──
  { symbol: 'WMT', name: 'Walmart Inc.' },
  { symbol: 'PG', name: 'Procter & Gamble Company' },
  { symbol: 'KO', name: 'Coca-Cola Company' },
  { symbol: 'PEP', name: 'PepsiCo Inc.' },
  { symbol: 'COST', name: 'Costco Wholesale Corporation' },
  { symbol: 'HD', name: 'Home Depot Inc.' },
  { symbol: 'MCD', name: 'McDonald\'s Corporation' },
  { symbol: 'NKE', name: 'Nike Inc.' },
  { symbol: 'SBUX', name: 'Starbucks Corporation' },
  { symbol: 'LOW', name: 'Lowe\'s Companies Inc.' },
  { symbol: 'TGT', name: 'Target Corporation' },
  { symbol: 'TJX', name: 'TJX Companies Inc.' },
  // ── Popular Stocks: Industrials / Energy ──
  { symbol: 'XOM', name: 'Exxon Mobil Corporation' },
  { symbol: 'CVX', name: 'Chevron Corporation' },
  { symbol: 'COP', name: 'ConocoPhillips' },
  { symbol: 'CAT', name: 'Caterpillar Inc.' },
  { symbol: 'BA', name: 'Boeing Company' },
  { symbol: 'LMT', name: 'Lockheed Martin Corporation' },
  { symbol: 'RTX', name: 'RTX Corporation' },
  { symbol: 'GE', name: 'GE Aerospace' },
  { symbol: 'HON', name: 'Honeywell International Inc.' },
  { symbol: 'UPS', name: 'United Parcel Service Inc.' },
  { symbol: 'DE', name: 'Deere & Company' },
  { symbol: 'UNP', name: 'Union Pacific Corporation' },
  // ── Popular Stocks: Communication / Media ──
  { symbol: 'DIS', name: 'Walt Disney Company' },
  { symbol: 'CMCSA', name: 'Comcast Corporation' },
  { symbol: 'T', name: 'AT&T Inc.' },
  { symbol: 'VZ', name: 'Verizon Communications Inc.' },
  { symbol: 'TMUS', name: 'T-Mobile US Inc.' },
  // ── Popular Stocks: Other Notable ──
  { symbol: 'BX', name: 'Blackstone Inc.' },
  { symbol: 'COIN', name: 'Coinbase Global Inc.' },
  { symbol: 'SQ', name: 'Block Inc.' },
  { symbol: 'PYPL', name: 'PayPal Holdings Inc.' },
  { symbol: 'SHOP', name: 'Shopify Inc.' },
  { symbol: 'SNOW', name: 'Snowflake Inc.' },
  { symbol: 'PLTR', name: 'Palantir Technologies Inc.' },
  { symbol: 'UBER', name: 'Uber Technologies Inc.' },
  { symbol: 'ABNB', name: 'Airbnb Inc.' },
  { symbol: 'NOW', name: 'ServiceNow Inc.' },
  { symbol: 'PANW', name: 'Palo Alto Networks Inc.' },
  { symbol: 'CRWD', name: 'CrowdStrike Holdings Inc.' },
  { symbol: 'ZS', name: 'Zscaler Inc.' },
  { symbol: 'DDOG', name: 'Datadog Inc.' },
  { symbol: 'NET', name: 'Cloudflare Inc.' },
  { symbol: 'MELI', name: 'MercadoLibre Inc.' },
  { symbol: 'SE', name: 'Sea Limited' },
  { symbol: 'ROKU', name: 'Roku Inc.' },
  { symbol: 'SNAP', name: 'Snap Inc.' },
  { symbol: 'PINS', name: 'Pinterest Inc.' },
  { symbol: 'RIVN', name: 'Rivian Automotive Inc.' },
  { symbol: 'LCID', name: 'Lucid Group Inc.' },
  { symbol: 'F', name: 'Ford Motor Company' },
  { symbol: 'GM', name: 'General Motors Company' },
  { symbol: 'LI', name: 'Li Auto Inc.' },
  { symbol: 'NIO', name: 'NIO Inc.' },
  { symbol: 'SOFI', name: 'SoFi Technologies Inc.' },
  { symbol: 'HOOD', name: 'Robinhood Markets Inc.' },
  { symbol: 'AFRM', name: 'Affirm Holdings Inc.' },
  { symbol: 'ARM', name: 'Arm Holdings plc' },
  { symbol: 'SMCI', name: 'Super Micro Computer Inc.' },
  { symbol: 'MU', name: 'Micron Technology Inc.' },
  { symbol: 'QCOM', name: 'Qualcomm Inc.' },
  { symbol: 'TXN', name: 'Texas Instruments Inc.' },
  { symbol: 'LRCX', name: 'Lam Research Corporation' },
  { symbol: 'AMAT', name: 'Applied Materials Inc.' },
  { symbol: 'KLAC', name: 'KLA Corporation' },
  { symbol: 'MRVL', name: 'Marvell Technology Inc.' },
  { symbol: 'ON', name: 'ON Semiconductor Corporation' },
  // ── Utilities / Staples ──
  { symbol: 'NEE', name: 'NextEra Energy Inc.' },
  { symbol: 'SO', name: 'Southern Company' },
  { symbol: 'DUK', name: 'Duke Energy Corporation' },
  { symbol: 'D', name: 'Dominion Energy Inc.' },
  { symbol: 'CL', name: 'Colgate-Palmolive Company' },
  { symbol: 'MMM', name: '3M Company' },
  { symbol: 'SPGI', name: 'S&P Global Inc.' },
  { symbol: 'ICE', name: 'Intercontinental Exchange Inc.' },
  { symbol: 'CME', name: 'CME Group Inc.' },
  { symbol: 'MCO', name: 'Moody\'s Corporation' },
  { symbol: 'APD', name: 'Air Products and Chemicals Inc.' },
  { symbol: 'SHW', name: 'Sherwin-Williams Company' },
  { symbol: 'FCX', name: 'Freeport-McMoRan Inc.' },
  { symbol: 'NEM', name: 'Newmont Corporation' },
];

// ── Component ────────────────────────────────────────────────

interface TickerSearchProps {
  value: string;
  onChange: (ticker: string) => void;
}

const MAX_RESULTS = 8;

export function TickerSearch({ value, onChange }: TickerSearchProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Filter tickers by symbol OR name
  const query = value.trim().toUpperCase();
  const filtered: TickerEntry[] =
    query.length === 0
      ? []
      : TICKER_DATABASE.filter(
          (t) =>
            t.symbol.includes(query) ||
            t.name.toUpperCase().includes(query),
        ).slice(0, MAX_RESULTS);

  // Show dropdown when there are matches and the input is focused
  const showDropdown = isOpen && filtered.length > 0;

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll the highlighted item into view
  useEffect(() => {
    if (highlightIndex >= 0 && listRef.current) {
      const items = listRef.current.children;
      if (items[highlightIndex]) {
        (items[highlightIndex] as HTMLElement).scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightIndex]);

  const selectTicker = useCallback(
    (symbol: string) => {
      onChange(symbol);
      setIsOpen(false);
      setHighlightIndex(-1);
      inputRef.current?.blur();
    },
    [onChange],
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!showDropdown) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < filtered.length) {
          selectTicker(filtered[highlightIndex].symbol);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightIndex(-1);
        break;
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value.toUpperCase());
          setIsOpen(true);
          setHighlightIndex(-1);
        }}
        onFocus={() => {
          if (query.length > 0) setIsOpen(true);
        }}
        onKeyDown={handleKeyDown}
        placeholder="SPY"
        autoComplete="off"
        className="w-full bg-surface-primary border border-border-default rounded-md px-3 py-1.5 text-sm font-mono text-accent-neutral placeholder-text-muted focus:outline-none focus:border-accent-neutral/50 transition-colors"
      />

      {showDropdown && (
        <ul
          ref={listRef}
          role="listbox"
          className="absolute z-50 left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-sm border border-border-default bg-surface-card shadow-lg shadow-black/40"
        >
          {filtered.map((entry, idx) => {
            const isHighlighted = idx === highlightIndex;
            return (
              <li
                key={`${entry.symbol}-${idx}`}
                role="option"
                aria-selected={isHighlighted}
                onMouseDown={(e) => {
                  // Prevent the input blur from firing before selection
                  e.preventDefault();
                  selectTicker(entry.symbol);
                }}
                onMouseEnter={() => setHighlightIndex(idx)}
                className={`flex items-center gap-3 px-3 py-2 cursor-pointer text-sm transition-colors ${
                  isHighlighted
                    ? 'bg-surface-hover text-text-primary'
                    : 'text-text-secondary hover:bg-surface-hover/60'
                }`}
              >
                <span className="font-mono font-medium text-accent-neutral w-14 shrink-0">
                  {entry.symbol}
                </span>
                <span className="truncate text-text-secondary text-xs">
                  {entry.name}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
