"""Shipment exception tracking and trend detection."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from src.utils import get_logger

logger = get_logger("exceptions")

EXCEPTION_TYPES = [
    "LATE_PICKUP", "LATE_DELIVERY", "DAMAGED", "SHORT_SHIP",
    "WRONG_ITEM", "DOCUMENTATION", "CUSTOMS_HOLD", "WEATHER",
    "CARRIER_ISSUE", "REFUSED", "ADDRESS_ERROR", "OTHER",
]


class ExceptionTracker:
    """Tracks and categorizes shipment exceptions for root cause analysis."""

    def analyze(self, shipments: pd.DataFrame) -> dict:
        if shipments.empty:
            return {"exception_rate": 0.0, "total_exceptions": 0}

        df = self._prepare(shipments)
        exceptions = df[df["exception_flag"] == 1]

        return {
            "total_shipments": len(df),
            "total_exceptions": len(exceptions),
            "exception_rate": round(len(exceptions) / len(df), 4) if len(df) > 0 else 0.0,
            "by_type": self._by_type(exceptions),
            "by_carrier": self._by_carrier(df),
            "by_origin": self._by_origin(df),
            "trend": self._weekly_trend(df),
            "repeat_offenders": self._repeat_offenders(exceptions),
            "calculated_at": datetime.now().isoformat(),
        }

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "exception_flag" not in df.columns:
            df["exception_flag"] = 0
        df["exception_flag"] = df["exception_flag"].fillna(0).astype(int)
        if "exception_type" not in df.columns:
            df["exception_type"] = "OTHER"
        return df

    def _by_type(self, exceptions: pd.DataFrame) -> dict:
        if exceptions.empty or "exception_type" not in exceptions.columns:
            return {}
        counts = exceptions["exception_type"].value_counts()
        total = counts.sum()
        return {
            k: {"count": int(v), "pct": round(v / total, 4)}
            for k, v in counts.items()
        }

    def _by_carrier(self, df: pd.DataFrame) -> dict:
        if "carrier_id" not in df.columns:
            return {}
        g = df.groupby("carrier_id").agg(
            total=("exception_flag", "count"),
            exceptions=("exception_flag", "sum"),
        )
        g["exception_rate"] = (g["exceptions"] / g["total"]).round(4)
        return g.to_dict(orient="index")

    def _by_origin(self, df: pd.DataFrame) -> dict:
        if "origin_id" not in df.columns:
            return {}
        g = df.groupby("origin_id").agg(
            total=("exception_flag", "count"),
            exceptions=("exception_flag", "sum"),
        )
        g["exception_rate"] = (g["exceptions"] / g["total"]).round(4)
        return g.to_dict(orient="index")

    def _weekly_trend(self, df: pd.DataFrame) -> list:
        date_col = None
        for c in ["actual_delivery", "planned_delivery"]:
            if c in df.columns:
                date_col = c
                break
        if not date_col:
            return []
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["week"] = df[date_col].dt.isocalendar().week.astype(int)
        df["year"] = df[date_col].dt.year
        g = df.groupby(["year", "week"]).agg(
            total=("exception_flag", "count"),
            exceptions=("exception_flag", "sum"),
        ).reset_index()
        g["rate"] = (g["exceptions"] / g["total"]).round(4)
        return g.to_dict(orient="records")

    def _repeat_offenders(self, exceptions: pd.DataFrame, threshold: int = 3) -> list:
        if exceptions.empty or "carrier_id" not in exceptions.columns:
            return []
        counts = exceptions["carrier_id"].value_counts()
        repeat = counts[counts >= threshold]
        return [
            {"carrier_id": k, "exception_count": int(v)}
            for k, v in repeat.items()
        ]
