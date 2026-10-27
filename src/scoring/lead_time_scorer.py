"""Lead time variability scoring for supplier risk assessment."""
import pandas as pd
import numpy as np
from src.utils import get_logger

logger = get_logger("lead_time_scorer")


class LeadTimeScorer:
    """Scores suppliers on lead time reliability.

    Score = 100 * (1 - CV) where CV = std_dev / mean of lead times.
    Lower variability = higher score = lower risk.
    """

    def __init__(self, weight: float = 0.30):
        self.weight = weight

    def score(self, po_data: pd.DataFrame) -> pd.DataFrame:
        if po_data.empty or "supplier_id" not in po_data.columns:
            return pd.DataFrame()

        df = po_data.copy()
        if "lead_time_days" not in df.columns:
            df["actual_receipt_date"] = pd.to_datetime(df.get("actual_receipt_date"), errors="coerce")
            df["po_date"] = pd.to_datetime(df.get("po_date"), errors="coerce")
            df["lead_time_days"] = (df["actual_receipt_date"] - df["po_date"]).dt.days

        df = df.dropna(subset=["lead_time_days"])
        df = df[df["lead_time_days"] > 0]

        grouped = df.groupby("supplier_id")["lead_time_days"].agg(
            ["mean", "std", "count", "min", "max"]
        ).reset_index()
        grouped.columns = [
            "supplier_id", "avg_lead_time", "std_lead_time",
            "order_count", "min_lead_time", "max_lead_time",
        ]

        grouped["cv"] = np.where(
            grouped["avg_lead_time"] > 0,
            grouped["std_lead_time"].fillna(0) / grouped["avg_lead_time"],
            0,
        )
        grouped["raw_score"] = (100 * (1 - grouped["cv"])).clip(0, 100)
        grouped["weighted_score"] = grouped["raw_score"] * self.weight
        grouped["lead_time_range"] = grouped["max_lead_time"] - grouped["min_lead_time"]

        logger.info(f"Scored {len(grouped)} suppliers on lead time variability")
        return grouped
