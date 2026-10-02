"""Market data endpoints for individual ticker lookups."""

import logging

import numpy as np
from fastapi import APIRouter, HTTPException

from backend.api.schemas.portfolio import ErrorResponse, TickerInfoResponse
from backend.data.market_data import (
    compute_daily_returns,
    fetch_historical_prices,
    fetch_ticker_info,
)
from backend.core.risk_engine import annualized_return, annualized_volatility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market-data", tags=["market-data"])


@router.get(
    "/{ticker}",
    response_model=TickerInfoResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_ticker_data(ticker: str) -> TickerInfoResponse:
    """Fetch current price, historical returns, and basic stats for a ticker."""
    try:
        info = fetch_ticker_info(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Compute historical returns if possible
    returns_1y = None
    returns_3y = None
    returns_5y = None
    vol = None

    try:
        prices = fetch_historical_prices([ticker], lookback_years=5)
        daily_rets = compute_daily_returns(prices)
        col = daily_rets.columns[0]

        vol = float(annualized_volatility(daily_rets[col]))

        # 1-year return (last ~252 days)
        if len(daily_rets) >= 252:
            returns_1y = float(annualized_return(daily_rets[col].iloc[-252:]))
        # 3-year return (last ~756 days)
        if len(daily_rets) >= 756:
            returns_3y = float(annualized_return(daily_rets[col].iloc[-756:]))
        # 5-year return (all data)
        if len(daily_rets) >= 1260:
            returns_5y = float(annualized_return(daily_rets[col]))

    except (ValueError, Exception) as e:
        logger.warning("Could not compute historical stats for %s: %s", ticker, e)

    return TickerInfoResponse(
        ticker=info.ticker,
        name=info.name,
        sector=info.sector,
        asset_class=info.asset_class,
        current_price=info.current_price,
        currency=info.currency,
        returns_1y=round(returns_1y, 4) if returns_1y is not None else None,
        returns_3y=round(returns_3y, 4) if returns_3y is not None else None,
        returns_5y=round(returns_5y, 4) if returns_5y is not None else None,
        volatility=round(vol, 4) if vol is not None else None,
    )
