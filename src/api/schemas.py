"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime


class KPITile(BaseModel):
    name: str
    value: float
    unit: str = ""
    trend: Optional[str] = None
    target: Optional[float] = None


class DashboardResponse(BaseModel):
    kpi_tiles: List[KPITile]
    generated_at: datetime


class SupplierScore(BaseModel):
    supplier_id: str
    lead_time_score: float
    otif_trend_score: float
    defect_score: float
    spend_score: float
    composite_score: float
    risk_tier: RiskTier
    trend_direction: str = "unknown"


class ScorecardResponse(BaseModel):
    total_suppliers: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    suppliers: List[SupplierScore]
    generated_at: datetime


class ShipmentMetrics(BaseModel):
    overall_otd: float
    total_shipments: int
    total_exceptions: int
    exception_rate: float
    avg_dwell_hours: float


class TrendPoint(BaseModel):
    period: str
    value: float
    count: int = 0


class TrendResponse(BaseModel):
    metric: str
    data: List[TrendPoint]
    generated_at: datetime


class ExceptionSummary(BaseModel):
    exception_type: str
    count: int
    pct: float


class FilterParams(BaseModel):
    supplier_id: Optional[str] = None
    carrier_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    risk_tier: Optional[RiskTier] = None
