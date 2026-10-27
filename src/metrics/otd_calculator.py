"""On-Time Delivery (OTD) metric calculator for shipments."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils import get_logger

logger = get_logger("otd_calculator")


class OTDCalculator:
    """Calculates On-Time Delivery rate for outbound shipments.

    OTD = shipments delivered by planned_delivery / total shipments
    Supports grace period configuration and carrier-level drill-down.
    """

    def __init__(self, grace_period_hours: float = 0.0):
        self.grace_period = timedelta(hours=grace_period_hours)

    def calculate(self, shipment_data: pd.DataFrame) -> dict:
        if shipment_data.empty:
            return {"overall_otd": 0.0, "by_carrier": {}, "by_lane": {}}

        df = self._prepare(shipment_data)

        return {
            "overall_otd": self._overall(df),
            "by_carrier": self._by_carrier(df),
            "by_lane": self._by_lane(df),
            "by_mode": self._by_mode(df),
            "trend": self._daily_trend(df, days=30),
            "late_shipment_analysis": self._late_analysis(df),
            "calculated_at": datetime.now().isoformat(),
        }

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in ["planned_delivery", "actual_delivery"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        df["effective_deadline"] = df["planned_delivery"] + self.grace_period
        df["is_on_time"] = (df["actual_delivery"] <= df["effective_deadline"]).astype(int).fillna(0).astype(int)
        df["delay_hours"] = np.maximum(
            (df["actual_delivery"] - df["planned_delivery"]).dt.total_seconds() / 3600, 0
        ).fillna(0)
        return df

    def _overall(self, df: pd.DataFrame) -> float:
        if len(df) == 0:
            return 0.0
        return float(df["is_on_time"].sum() / len(df))

    def _by_carrier(self, df: pd.DataFrame) -> dict:
        if "carrier_id" not in df.columns:
            return {}
        g = df.groupby("carrier_id").agg(
            total=("is_on_time", "count"),
            on_time=("is_on_time", "sum"),
            avg_delay_hrs=("delay_hours", "mean"),
        )
        g["otd_rate"] = g["on_time"] / g["total"]
        return g.to_dict(orient="index")

    def _by_lane(self, df: pd.DataFrame) -> dict:
        origin = "origin_id" if "origin_id" in df.columns else None
        dest = "destination_id" if "destination_id" in df.columns else None
        if not origin or not dest:
            return {}
        g = df.groupby([origin, dest]).agg(
            total=("is_on_time", "count"),
            on_time=("is_on_time", "sum"),
            avg_delay_hrs=("delay_hours", "mean"),
        )
        g["otd_rate"] = g["on_time"] / g["total"]
        return g.to_dict(orient="index")

    def _by_mode(self, df: pd.DataFrame) -> dict:
        if "transport_mode" not in df.columns:
            return {}
        g = df.groupby("transport_mode").agg(
            total=("is_on_time", "count"),
            on_time=("is_on_time", "sum"),
        )
        g["otd_rate"] = g["on_time"] / g["total"]
        return g.to_dict(orient="index")

    def _daily_trend(self, df: pd.DataFrame, days: int = 30) -> list:
        if "actual_delivery" not in df.columns:
            return []
        cutoff = df["actual_delivery"].max() - timedelta(days=days)
        recent = df[df["actual_delivery"] >= cutoff].copy()
        recent["date"] = recent["actual_delivery"].dt.date
        g = recent.groupby("date").agg(total=("is_on_time", "count"), on_time=("is_on_time", "sum")).reset_index()
        g["otd_rate"] = g["on_time"] / g["total"]
        g["date"] = g["date"].astype(str)
        return g.to_dict(orient="records")

    def _late_analysis(self, df: pd.DataFrame) -> dict:
        late = df[df["is_on_time"] == 0]
        if late.empty:
            return {"count": 0}
        return {
            "count": len(late),
            "avg_delay_hours": round(float(late["delay_hours"].mean()), 1),
            "median_delay_hours": round(float(late["delay_hours"].median()), 1),
            "p95_delay_hours": round(float(late["delay_hours"].quantile(0.95)), 1),
            "worst_carrier": late.groupby("carrier_id")["delay_hours"].mean().idxmax() if "carrier_id" in late.columns else None,
        }
