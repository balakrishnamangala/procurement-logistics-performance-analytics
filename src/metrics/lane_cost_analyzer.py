"""Freight lane cost analysis and benchmarking."""
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils import get_logger

logger = get_logger("lane_cost")


class LaneCostAnalyzer:
    """Analyzes freight costs across shipping lanes for optimization.

    Identifies high-cost lanes, cost-per-unit trends, and carrier
    rate comparison to support procurement negotiations.
    """

    def analyze(self, shipments: pd.DataFrame) -> dict:
        if shipments.empty:
            return {"total_freight_cost": 0.0}

        df = self._prepare(shipments)

        return {
            "total_freight_cost": round(float(df["total_cost"].sum()), 2),
            "avg_cost_per_shipment": round(float(df["total_cost"].mean()), 2),
            "avg_cost_per_unit": self._avg_cost_per_unit(df),
            "by_lane": self._by_lane(df),
            "by_carrier": self._by_carrier(df),
            "by_mode": self._by_mode(df),
            "top_spend_lanes": self._top_lanes(df, n=10),
            "cost_trend": self._monthly_trend(df),
            "calculated_at": datetime.now().isoformat(),
        }

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["total_cost"] = (
            df.get("freight_cost", pd.Series(0, index=df.index)).fillna(0) +
            df.get("accessorial_cost", pd.Series(0, index=df.index)).fillna(0)
        )
        if "weight" in df.columns:
            df["cost_per_kg"] = np.where(df["weight"] > 0, df["total_cost"] / df["weight"], 0)
        if "units" in df.columns:
            df["cost_per_unit"] = np.where(df["units"] > 0, df["total_cost"] / df["units"], 0)
        return df

    def _avg_cost_per_unit(self, df: pd.DataFrame) -> float:
        if "units" in df.columns and df["units"].sum() > 0:
            return round(float(df["total_cost"].sum() / df["units"].sum()), 2)
        return 0.0

    def _by_lane(self, df: pd.DataFrame) -> dict:
        origin = "origin_id" if "origin_id" in df.columns else None
        dest = "destination_id" if "destination_id" in df.columns else None
        if not origin or not dest:
            return {}
        g = df.groupby([origin, dest]).agg(
            shipment_count=("total_cost", "count"),
            total_cost=("total_cost", "sum"),
            avg_cost=("total_cost", "mean"),
        )
        g = g.round(2)
        return g.to_dict(orient="index")

    def _by_carrier(self, df: pd.DataFrame) -> dict:
        if "carrier_id" not in df.columns:
            return {}
        g = df.groupby("carrier_id").agg(
            shipment_count=("total_cost", "count"),
            total_cost=("total_cost", "sum"),
            avg_cost=("total_cost", "mean"),
        ).round(2)
        return g.to_dict(orient="index")

    def _by_mode(self, df: pd.DataFrame) -> dict:
        if "transport_mode" not in df.columns:
            return {}
        g = df.groupby("transport_mode").agg(
            shipment_count=("total_cost", "count"),
            total_cost=("total_cost", "sum"),
            avg_cost=("total_cost", "mean"),
        ).round(2)
        return g.to_dict(orient="index")

    def _top_lanes(self, df: pd.DataFrame, n: int = 10) -> list:
        origin = "origin_id" if "origin_id" in df.columns else None
        dest = "destination_id" if "destination_id" in df.columns else None
        if not origin or not dest:
            return []
        g = df.groupby([origin, dest]).agg(
            total_cost=("total_cost", "sum"),
            shipments=("total_cost", "count"),
        ).reset_index()
        g["avg_cost"] = g["total_cost"] / g["shipments"]
        top = g.nlargest(n, "total_cost")
        return top.round(2).to_dict(orient="records")

    def _monthly_trend(self, df: pd.DataFrame) -> list:
        date_col = None
        for c in ["actual_delivery", "planned_delivery", "ship_date"]:
            if c in df.columns:
                date_col = c
                break
        if not date_col:
            return []
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["month"] = df[date_col].dt.to_period("M").astype(str)
        g = df.groupby("month").agg(
            total_cost=("total_cost", "sum"),
            shipments=("total_cost", "count"),
        ).reset_index()
        g["avg_cost"] = g["total_cost"] / g["shipments"]
        return g.round(2).to_dict(orient="records")
