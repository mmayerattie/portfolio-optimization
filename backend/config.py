"""Configuration constants for the portfolio optimization engine."""

RISK_FREE_RATE: float = 0.045
TRADING_DAYS_PER_YEAR: int = 252
DEFAULT_LOOKBACK_YEARS: int = 5
MIN_HISTORY_DAYS: int = 756
MONTE_CARLO_SIMULATIONS: int = 10_000
MONTE_CARLO_DISPLAY_PATHS: int = 20
EFFICIENT_FRONTIER_POINTS: int = 50
DEFAULT_MAX_POSITION_WEIGHT: float = 0.35
DEFAULT_MIN_POSITION_WEIGHT: float = 0.02
REBALANCE_BAND_WIDTH: float = 0.05

EXPANSION_UNIVERSE: list[str] = [
    "SPY", "QQQ", "IWM", "VEA", "VWO",
    "TLT", "IEF", "SHY", "TIP", "LQD",
    "GLD", "SLV", "DBC",
    "VNQ", "VNQI",
    "MTUM", "VLUE", "QUAL", "SIZE",
]
