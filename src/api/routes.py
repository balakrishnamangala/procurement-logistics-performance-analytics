"""API route handlers for control tower and scorecard endpoints."""
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Optional

from src.api.schemas import (
    DashboardResponse, ScorecardResponse, SupplierScore,
    ShipmentMetrics, TrendResponse, TrendPoint, KPITile,
    ExceptionSummary, RiskTier,
)
from src.api.dependencies import get_data_service

control_tower_router = APIRouter()
scorecard_router = APIRouter()


@control_tower_router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    warehouse_id: Optional[str] = Query(None),
    data_service=Depends(get_data_service),
):
    """Get control tower dashboard with KPI tiles."""
    try:
        kpis = data_service.get_dashboard_kpis(
            from_date=from_date, to_date=to_date,
            warehouse_id=warehouse_id,
        )
        return DashboardResponse(
            kpi_tiles=kpis,
            generated_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@control_tower_router.get("/shipment-metrics", response_model=ShipmentMetrics)
async def get_shipment_metrics(
    carrier_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    data_service=Depends(get_data_service),
):
    """Get aggregate shipment performance metrics."""
    return data_service.get_shipment_metrics(carrier_id=carrier_id, days=days)


@control_tower_router.get("/otd-trend", response_model=TrendResponse)
async def get_otd_trend(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=7, le=365),
    data_service=Depends(get_data_service),
):
    """Get OTD rate trend over time."""
    data = data_service.get_otd_trend(period=period, days=days)
    return TrendResponse(metric="otd_rate", data=data, generated_at=datetime.now())


@control_tower_router.get("/exceptions")
async def get_exceptions(
    carrier_id: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    days: int = Query(30),
    data_service=Depends(get_data_service),
):
    """Get shipment exception analysis."""
    return data_service.get_exception_analysis(
        carrier_id=carrier_id, exception_type=exception_type, days=days
    )


@control_tower_router.get("/dwell-time")
async def get_dwell_time(
    warehouse_id: Optional[str] = Query(None),
    data_service=Depends(get_data_service),
):
    """Get warehouse dwell time analysis."""
    return data_service.get_dwell_analysis(warehouse_id=warehouse_id)


@control_tower_router.get("/lane-costs")
async def get_lane_costs(
    top_n: int = Query(10, ge=1, le=50),
    data_service=Depends(get_data_service),
):
    """Get lane cost analysis with top spend lanes."""
    return data_service.get_lane_cost_analysis(top_n=top_n)


@scorecard_router.get("/suppliers", response_model=ScorecardResponse)
async def get_scorecard(
    risk_tier: Optional[RiskTier] = Query(None),
    data_service=Depends(get_data_service),
):
    """Get supplier risk scorecard with composite scores."""
    try:
        result = data_service.get_supplier_scorecard(risk_tier=risk_tier)
        return ScorecardResponse(
            total_suppliers=result["total_suppliers"],
            high_risk_count=result["high_risk_count"],
            medium_risk_count=result["medium_risk_count"],
            low_risk_count=result["low_risk_count"],
            suppliers=[SupplierScore(**s) for s in result["suppliers"]],
            generated_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@scorecard_router.get("/suppliers/{supplier_id}")
async def get_supplier_detail(
    supplier_id: str,
    data_service=Depends(get_data_service),
):
    """Get detailed risk breakdown for a specific supplier."""
    result = data_service.get_supplier_detail(supplier_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return result


@scorecard_router.get("/high-risk")
async def get_high_risk_suppliers(
    data_service=Depends(get_data_service),
):
    """Get list of high-risk suppliers requiring attention."""
    return data_service.get_high_risk_suppliers()


@scorecard_router.get("/otif-trend")
async def get_supplier_otif_trend(
    supplier_id: Optional[str] = Query(None),
    months: int = Query(6, ge=1, le=24),
    data_service=Depends(get_data_service),
):
    """Get OTIF trend for supplier(s)."""
    return data_service.get_supplier_otif_trend(supplier_id=supplier_id, months=months)
