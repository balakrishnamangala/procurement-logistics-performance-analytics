"""FastAPI application for the Logistics Control Tower."""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional

from src.api.schemas import (
    HealthResponse, DashboardResponse, ScorecardResponse,
    ShipmentMetrics, TrendResponse, KPITile,
)
from src.api.routes import control_tower_router, scorecard_router

app = FastAPI(
    title="Logistics Control Tower & Supplier Risk Scorecard",
    description="Real-time logistics monitoring and supplier risk assessment API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(control_tower_router, prefix="/api/v1/control-tower", tags=["Control Tower"])
app.include_router(scorecard_router, prefix="/api/v1/scorecard", tags=["Supplier Scorecard"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(),
    )


@app.get("/")
async def root():
    return {
        "service": "Logistics Control Tower & Supplier Risk Scorecard",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "control_tower": "/api/v1/control-tower",
            "scorecard": "/api/v1/scorecard",
            "health": "/health",
        },
    }
