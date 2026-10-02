# Portfolio Optimizer

A full-stack web tool that takes your current investment positions and returns a quantitative diagnostic: risk decomposition, an optimized allocation, historical stress tests, a Monte Carlo projection, and a concrete rebalancing plan.

> **Disclaimer:** This project is for educational and analytical purposes only. It is **not** financial advice. Outputs are model estimates based on historical data and do not predict future results.

**Stack:** Python 3.11 · FastAPI · NumPy / pandas / SciPy / scikit-learn · yfinance · React 19 · TypeScript · Tailwind · Recharts · D3 · Zustand · Vite

---

## What it does

You enter tickers, share counts and (optionally) cost basis. The backend downloads about 5 years of daily prices and runs this pipeline:

| Step | Module | What happens |
|------|--------|--------------|
| 1. Data | `backend/data/market_data.py` | yfinance download with in-memory TTL cache, ticker validation, data-quality filtering |
| 2. Diagnostics | `backend/core/risk_engine.py` | Annualized return/volatility, Sharpe, max drawdown, VaR/CVaR (95%), per-asset risk contributions, correlation matrix, concentration (HHI, effective N) |
| 3. Optimization | `backend/core/optimizer.py` | Max-Sharpe and min-variance portfolios plus a 50-point efficient frontier, under min/max weight, required and excluded tickers |
| 4. Recommendations | `backend/core/recommender.py` | Scores candidate ETFs from an expansion universe by the Sharpe improvement from *adding* (5%) or *swapping in* for the weakest asset |
| 5. Stress tests | `backend/core/scenarios.py`, `monte_carlo.py` | 6 historical scenarios (2008, COVID, dot-com, 2022 rates, 1970s stagflation, 2017 bull) plus a correlated Monte Carlo simulation |
| 6. Rebalancing | `backend/core/rebalancer.py` | Trade list, turnover, transaction-cost estimate, tax-loss-harvesting swaps (e.g. SPY → VOO), rebalance bands |

The frontend is a single-page dashboard with six tabs: **Portfolio Input, Diagnostic, Optimization, Stress Test, Rebalance, Monitoring**. The efficient frontier is an interactive D3 chart (hover for allocations, click for details).

## How it works

- **Covariance:** Ledoit-Wolf shrinkage (`sklearn.covariance.LedoitWolf`) instead of the raw sample covariance, which is unstable when assets are highly correlated or history is short.
- **Optimization:** SciPy SLSQP. The efficient frontier is built by minimizing variance at 50 target returns between the minimum-variance return and the highest single-asset return.
- **Risk contribution:** `RC_i = w_i · (Σw)_i / σ_p`, reported as marginal and percentage contribution.
- **Monte Carlo:** Correlated normal draws via Cholesky decomposition of the covariance matrix (with a small regularizer for near-singular matrices). Reports terminal-value percentiles (P5–P95), probability of loss, expected max drawdown, and sample paths for the fan chart.
- **Scenarios:** Each scenario defines asset-class returns (equity, bond, commodity, REIT). Equities are scaled by each ticker's beta against an equal-weight proxy of the portfolio, so a high-beta stock falls harder than a utility.
- **Rebalancing:** Trades are the difference between current and target weights at current prices. Tax-loss harvesting uses a static map of similar-but-not-identical ETFs.

## Project structure

```
portfolio_optimization/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, /api/health
│   ├── config.py               # Constants (risk-free rate, frontier points, ...)
│   ├── api/
│   │   ├── routes/             # portfolio.py (POST /analyze), market_data.py
│   │   └── schemas/            # Pydantic request/response models
│   ├── core/                   # optimizer, risk_engine, monte_carlo,
│   │                           # scenarios, recommender, rebalancer
│   ├── data/market_data.py     # yfinance wrapper + cache
│   ├── tests/                  # 126 pytest tests (7 need network)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/         # layout, portfolio, analysis, optimization,
│       │                       # stress-test, rebalance
│       ├── store/              # Zustand store
│       ├── types/ utils/       # TypeScript types, formatters, validators
│       └── App.tsx
├── pytest.ini
```

## Running it

Requires Python 3.11+ and Node 18+.

```bash
# Backend (from the repo root)
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000   # docs at /docs

# Frontend (second terminal)
cd frontend
npm install
npm run dev                                               # http://localhost:5173
```

The Vite dev server proxies `/api` to `127.0.0.1:8000`.

### Tests

```bash
pytest backend/tests -m "not network"    # 119 tests, no internet needed
pytest backend/tests                     # also runs the yfinance tests
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/portfolio/analyze` | Full pipeline: diagnostics, optimization, stress test, rebalance, monitoring |
| GET | `/api/market-data/{ticker}` | Price, returns and basic stats for one ticker |
| GET | `/api/health` | Health check |

## Findings

These are conclusions about the methods and their behavior, drawn from building and testing the tool. I did not include sample portfolio numbers because they would depend on the date the data is pulled. Run your own portfolio and add a screenshot below.

1. **Plain mean-variance is dominated by the return estimates, not the covariance.** Expected returns are each asset's historical annualized return. The max-Sharpe solution therefore piles into whatever did best over the lookback window, and the `DEFAULT_MAX_POSITION_WEIGHT = 0.35` cap does much of the real work of keeping the result diversified. This is the classic "error-maximizer" problem and the main motivation for Black-Litterman.
2. **Covariance shrinkage matters most for small samples and correlated assets.** Ledoit-Wolf keeps the optimizer stable with 5 years of daily data and ETFs that overlap heavily (SPY/QQQ/VOO). The edge-case tests (highly correlated assets, single asset, infeasible constraints) are there because those are where an unshrunk estimate breaks.
3. **Risk contribution tells a different story than weights.** A portfolio that looks balanced by dollars can get most of its variance from one or two volatile positions. The diagnostic flags this directly (for example when a few assets account for most of the risk).
4. **Recommendations are greedy and in-sample.** The recommender evaluates one candidate at a time against the existing portfolio. It does not re-optimize the whole portfolio around the candidate, and it judges Sharpe on the same history it was fit on, so treat suggestions as ideas to investigate.
5. **Stress tests are stylized, not replayed.** Scenarios apply fixed asset-class shocks scaled by beta. They show directional exposure (for example, how a bond-heavy portfolio does in the 2022 scenario versus 2008), but they are not a reconstruction of actual price paths.
6. **Verified behavior:** the 119 offline tests cover the optimizer constraints, risk metrics against known values, Monte Carlo reproducibility with fixed seeds, the recommender, and the API contract.

*Add a screenshot of the efficient frontier and diagnostic tab here, e.g. `docs/screenshots/frontier.png`.*

## Status and limitations

Not yet implemented:

- Black-Litterman: the API accepts `views`, but they are not applied to the returns.
- True risk parity: the response currently uses inverse-volatility weights as an approximation.
- Fama-French factor model: `factor_exposures` is returned empty.
- Kelly sizing, Student-t Monte Carlo (it uses normal draws), PDF export, real-time prices.
- The rebalance and monitoring endpoints exist only inside `/analyze`; there are no standalone `/optimize` or `/rebalance` routes.
- The risk-free rate is a fixed constant (4.5%), not fetched live.

## License

Add a license of your choice (MIT is common for portfolio projects).
