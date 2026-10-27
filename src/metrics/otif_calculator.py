"""On-Time In-Full (OTIF) metric calculator for purchase orders."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from src.utils import get_logger

logger = get_logger("otif_calculator")


class OTIFCalculator:
    """Calculates OTIF metrics at supplier, category, and plant level.

    OTIF = (Orders delivered on-time AND in-full) / Total orders
    On-time: actual_receipt_date <= requested_date
    In-full: receipt_quantity >= 98% of order_quantity
    """

    def __init__(self, tolerance_pct: float = 0.98):
        self.tolerance_pct = tolerance_pct

    def calculate(self, po_data: pd.DataFrame) -> dict:
        """Calculate overall and segmented OTIF metrics."""
        if po_data.empty:
            return {"overall": 0.0, "by_supplier": {}, "by_period": {}}

        df = self._prepare_data(po_data)

        result = {
            "overall": self._overall_otif(df),
            "by_supplier": self._by_supplier(df),
            "by_period": self._by_period(df),
            "by_category": self._by_category(df),
            "trend": self._weekly_trend(df),
            "calculated_at": datetime.now().isoformat(),
        }

        logger.info(f"OTIF overall: {result['overall']:.1%}")
        return result

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure OTIF flags are computed."""
        df = df.copy()
        for col in ["requested_date", "actual_receipt_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        if "is_on_time" not in df.columns:
            df["is_on_time"] = (
                df["actual_receipt_date"] <= df["requested_date"]
            ).astype(int).fillna(0).astype(int)

        if "is_in_full" not in df.columns:
            df["is_in_full"] = np.where(
                df["order_quantity"] > 0,
                (df["receipt_quantity"] >= df["order_quantity"] * self.tolerance_pct).astype(int),
                0,
            )

        if "is_otif" not in df.columns:
            df["is_otif"] = (df["is_on_time"] & df["is_in_full"]).astype(int)

        return df

    def _overall_otif(self, df: pd.DataFrame) -> float:
        total = len(df)
        if total == 0:
            return 0.0
        return float(df["is_otif"].sum() / total)

    def _by_supplier(self, df: pd.DataFrame) -> dict:
        if "supplier_id" not in df.columns:
            return {}
        grouped = df.groupby("supplier_id").agg(
            total_orders=("is_otif", "count"),
            otif_orders=("is_otif", "sum"),
            on_time_orders=("is_on_time", "sum"),
            in_full_orders=("is_in_full", "sum"),
        )
        grouped["otif_rate"] = grouped["otif_orders"] / grouped["total_orders"]
        grouped["on_time_rate"] = grouped["on_time_orders"] / grouped["total_orders"]
        grouped["in_full_rate"] = grouped["in_full_orders"] / grouped["total_orders"]
        return grouped.to_dict(orient="index")

    def _by_period(self, df: pd.DataFrame, freq: str = "M") -> dict:
        if "requested_date" not in df.columns:
            return {}
        df["period"] = df["requested_date"].dt.to_period(freq).astype(str)
        grouped = df.groupby("period").agg(
            total=("is_otif", "count"),
            otif=("is_otif", "sum"),
        )
        grouped["otif_rate"] = grouped["otif"] / grouped["total"]
        return grouped.to_dict(orient="index")

    def _by_category(self, df: pd.DataFrame) -> dict:
        if "material_group" not in df.columns:
            return {}
        grouped = df.groupby("material_group").agg(
            total=("is_otif", "count"),
            otif=("is_otif", "sum"),
        )
        grouped["otif_rate"] = grouped["otif"] / grouped["total"]
        return grouped.to_dict(orient="index")

    def _weekly_trend(self, df: pd.DataFrame, weeks: int = 12) -> list:
        if "requested_date" not in df.columns:
            return []
        cutoff = df["requested_date"].max() - timedelta(weeks=weeks)
        recent = df[df["requested_date"] >= cutoff].copy()
        recent["week"] = recent["requested_date"].dt.isocalendar().week.astype(int)
        recent["year"] = recent["requested_date"].dt.year
        grouped = recent.groupby(["year", "week"]).agg(
            total=("is_otif", "count"),
            otif=("is_otif", "sum"),
        ).reset_index()
        grouped["otif_rate"] = grouped["otif"] / grouped["total"]
        return grouped[["year", "week", "total", "otif", "otif_rate"]].to_dict(orient="records")
