"""FastAPI application entry point for the Portfolio Optimizer API."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.portfolio import router as portfolio_router
from backend.api.routes.market_data import router as market_data_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Portfolio Optimizer API",
    description=(
        "Quantitative portfolio analysis tool providing diagnostics, "
        "optimization, stress testing, and rebalancing recommendations. "
        "For educational purposes only — not financial advice."
    ),
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_router)
app.include_router(market_data_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
