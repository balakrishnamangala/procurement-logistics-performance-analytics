"""Warehouse dwell time analysis for inbound shipments."""
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils import get_logger

logger = get_logger("dwell_time")


class DwellTimeAnalyzer:
    """Analyzes dwell time between dock arrival and putaway completion.

    Dwell = putaway_complete - dock_arrival (hours)
    Excessive dwell ties up dock capacity, delays inventory availability.
    """

    def __init__(self, target_hours: float = 4.0, critical_hours: float = 8.0):
        self.target_hours = target_hours
        self.critical_hours = critical_hours

    def analyze(self, data: pd.DataFrame) -> dict:
        if data.empty:
            return {"avg_dwell_hours": 0.0}

        df = self._prepare(data)

        return {
            "avg_dwell_hours": round(float(df["dwell_time_hours"].mean()), 2),
            "median_dwell_hours": round(float(df["dwell_time_hours"].median()), 2),
            "p90_dwell_hours": round(float(df["dwell_time_hours"].quantile(0.90)), 2),
            "pct_within_target": round(float((df["dwell_time_hours"] <= self.target_hours).mean()), 4),
            "pct_critical": round(float((df["dwell_time_hours"] > self.critical_hours).mean()), 4),
            "by_warehouse": self._by_warehouse(df),
            "by_carrier": self._by_carrier(df),
            "trend": self._weekly_trend(df),
            "calculated_at": datetime.now().isoformat(),
        }

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "dwell_time_hours" not in df.columns:
            for col in ["dock_arrival", "putaway_complete_time"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            if "dock_arrival" in df.columns and "putaway_complete_time" in df.columns:
                df["dwell_time_hours"] = (
                    (df["putaway_complete_time"] - df["dock_arrival"]).dt.total_seconds() / 3600
                )
        df["dwell_time_hours"] = df["dwell_time_hours"].fillna(0).clip(lower=0)
        return df

    def _by_warehouse(self, df: pd.DataFrame) -> dict:
        if "warehouse_id" not in df.columns:
            return {}
        g = df.groupby("warehouse_id")["dwell_time_hours"].agg(["mean", "median", "count"])
        g.columns = ["avg_hours", "median_hours", "shipment_count"]
        return g.round(2).to_dict(orient="index")

    def _by_carrier(self, df: pd.DataFrame) -> dict:
        if "carrier_id" not in df.columns:
            return {}
        g = df.groupby("carrier_id")["dwell_time_hours"].agg(["mean", "median", "count"])
        g.columns = ["avg_hours", "median_hours", "shipment_count"]
        return g.round(2).to_dict(orient="index")

    def _weekly_trend(self, df: pd.DataFrame) -> list:
        date_col = None
        for c in ["dock_arrival", "actual_delivery", "actual_arrival"]:
            if c in df.columns:
                date_col = c
                break
        if not date_col:
            return []
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["week"] = df[date_col].dt.isocalendar().week.astype(int)
        df["year"] = df[date_col].dt.year
        g = df.groupby(["year", "week"])["dwell_time_hours"].agg(["mean", "median", "count"]).reset_index()
        g.columns = ["year", "week", "avg_hours", "median_hours", "count"]
        return g.round(2).to_dict(orient="records")
