"""Dashboard data aggregation service powering API and Power BI."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List

from src.etl import ETLOrchestrator
from src.metrics import OTIFCalculator, OTDCalculator, DwellTimeAnalyzer, LaneCostAnalyzer, ExceptionTracker
from src.scoring import CompositeScorer
from src.utils import get_logger

logger = get_logger("data_service")


class DashboardDataService:
    """Aggregates metrics and scores for dashboard consumption."""

    def __init__(self):
        self.otif_calc = OTIFCalculator()
        self.otd_calc = OTDCalculator()
        self.dwell_analyzer = DwellTimeAnalyzer()
        self.lane_analyzer = LaneCostAnalyzer()
        self.exception_tracker = ExceptionTracker()
        self.scorer = CompositeScorer()
        self._po_cache: Optional[pd.DataFrame] = None
        self._shipment_cache: Optional[pd.DataFrame] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=15)

    def _get_data(self):
        now = datetime.now()
        if self._cache_time and (now - self._cache_time) < self._cache_ttl:
            return self._po_cache, self._shipment_cache

        try:
            orchestrator = ETLOrchestrator()
            self._po_cache = orchestrator._extract_and_transform_pos()
            self._shipment_cache = orchestrator._extract_and_transform_shipments()
            self._cache_time = now
        except Exception as e:
            logger.warning(f"Data refresh failed, using cache: {e}")
            if self._po_cache is None:
                self._po_cache = pd.DataFrame(columns=[
                    "po_number", "po_item", "supplier_id", "material_group",
                    "po_date", "requested_date", "order_quantity", "receipt_quantity",
                    "defect_quantity", "unit_price", "actual_receipt_date", "net_value",
                    "lead_time_days", "is_on_time", "is_in_full", "is_otif",
                ])
            if self._shipment_cache is None:
                self._shipment_cache = pd.DataFrame(columns=[
                    "shipment_id", "carrier_id", "origin_id", "destination_id",
                    "transport_mode", "planned_delivery", "freight_cost",
                    "accessorial_cost", "weight", "units", "dwell_time_hours",
                    "exception_flag", "exception_type", "actual_delivery", "delay_hours",
                ])

        return self._po_cache, self._shipment_cache

    def get_dashboard_kpis(self, from_date=None, to_date=None, warehouse_id=None) -> list:
        po_data, ship_data = self._get_data()

        otif_result = self.otif_calc.calculate(po_data)
        otd_result = self.otd_calc.calculate(ship_data)
        dwell_result = self.dwell_analyzer.analyze(ship_data)
        lane_result = self.lane_analyzer.analyze(ship_data)
        exception_result = self.exception_tracker.analyze(ship_data)
        scorecard = self.scorer.generate_report(po_data)

        return [
            {"name": "OTIF Rate", "value": round(otif_result.get("overall", 0) * 100, 1), "unit": "%", "target": 95.0},
            {"name": "OTD Rate", "value": round(otd_result.get("overall_otd", 0) * 100, 1), "unit": "%", "target": 97.0},
            {"name": "Avg Dwell Time", "value": dwell_result.get("avg_dwell_hours", 0), "unit": "hrs", "target": 4.0},
            {"name": "Freight Cost/Unit", "value": lane_result.get("avg_cost_per_unit", 0), "unit": "$"},
            {"name": "Exception Rate", "value": round(exception_result.get("exception_rate", 0) * 100, 1), "unit": "%", "target": 2.0},
            {"name": "High Risk Suppliers", "value": scorecard.get("high_risk_count", 0), "unit": ""},
        ]

    def get_shipment_metrics(self, carrier_id=None, days=30):
        _, ship_data = self._get_data()
        otd = self.otd_calc.calculate(ship_data)
        exc = self.exception_tracker.analyze(ship_data)
        dwell = self.dwell_analyzer.analyze(ship_data)
        return {
            "overall_otd": otd.get("overall_otd", 0),
            "total_shipments": exc.get("total_shipments", 0),
            "total_exceptions": exc.get("total_exceptions", 0),
            "exception_rate": exc.get("exception_rate", 0),
            "avg_dwell_hours": dwell.get("avg_dwell_hours", 0),
        }

    def get_otd_trend(self, period="daily", days=30):
        _, ship_data = self._get_data()
        otd = self.otd_calc.calculate(ship_data)
        trend = otd.get("trend", [])
        return [{"period": t.get("date", ""), "value": t.get("otd_rate", 0), "count": t.get("total", 0)} for t in trend]

    def get_exception_analysis(self, carrier_id=None, exception_type=None, days=30):
        _, ship_data = self._get_data()
        return self.exception_tracker.analyze(ship_data)

    def get_dwell_analysis(self, warehouse_id=None):
        _, ship_data = self._get_data()
        return self.dwell_analyzer.analyze(ship_data)

    def get_lane_cost_analysis(self, top_n=10):
        _, ship_data = self._get_data()
        return self.lane_analyzer.analyze(ship_data)

    def get_supplier_scorecard(self, risk_tier=None):
        po_data, _ = self._get_data()
        scores = self.scorer.score_all(po_data)
        if risk_tier:
            scores = scores[scores["risk_tier"] == risk_tier.value]
        return {
            "total_suppliers": len(scores),
            "high_risk_count": len(scores[scores["risk_tier"] == "HIGH"]),
            "medium_risk_count": len(scores[scores["risk_tier"] == "MEDIUM"]),
            "low_risk_count": len(scores[scores["risk_tier"] == "LOW"]),
            "suppliers": scores.to_dict(orient="records"),
        }

    def get_supplier_detail(self, supplier_id: str):
        po_data, _ = self._get_data()
        supplier_pos = po_data[po_data["supplier_id"] == supplier_id]
        if supplier_pos.empty:
            return None
        scores = self.scorer.score_all(supplier_pos)
        if scores.empty:
            return None
        return scores.iloc[0].to_dict()

    def get_high_risk_suppliers(self):
        po_data, _ = self._get_data()
        return self.scorer.get_high_risk_suppliers(po_data).to_dict(orient="records")

    def get_supplier_otif_trend(self, supplier_id=None, months=6):
        po_data, _ = self._get_data()
        if supplier_id:
            po_data = po_data[po_data["supplier_id"] == supplier_id]
        otif = self.otif_calc.calculate(po_data)
        return otif.get("trend", [])
