"""Defect rate scoring for supplier quality risk."""
import pandas as pd
import numpy as np
from src.utils import get_logger

logger = get_logger("defect_scorer")


class DefectRateScorer:
    """Scores suppliers based on quality defect rates.

    Score = 100 * (1 - defect_rate) where defect_rate = defect_qty / total_qty.
    Penalizes suppliers with high rejection or quality hold rates.
    """

    def __init__(self, weight: float = 0.25):
        self.weight = weight

    def score(self, po_data: pd.DataFrame) -> pd.DataFrame:
        if po_data.empty or "supplier_id" not in po_data.columns:
            return pd.DataFrame()

        df = po_data.copy()
        if "defect_quantity" not in df.columns:
            df["defect_quantity"] = 0
        if "receipt_quantity" not in df.columns and "order_quantity" in df.columns:
            df["receipt_quantity"] = df["order_quantity"]

        df["defect_quantity"] = df["defect_quantity"].fillna(0)
        df["receipt_quantity"] = df["receipt_quantity"].fillna(0)

        grouped = df.groupby("supplier_id").agg(
            total_received=("receipt_quantity", "sum"),
            total_defects=("defect_quantity", "sum"),
            order_count=("supplier_id", "count"),
            orders_with_defects=("defect_quantity", lambda x: (x > 0).sum()),
        ).reset_index()

        grouped["defect_rate"] = np.where(
            grouped["total_received"] > 0,
            grouped["total_defects"] / grouped["total_received"],
            0,
        )
        grouped["defect_frequency"] = np.where(
            grouped["order_count"] > 0,
            grouped["orders_with_defects"] / grouped["order_count"],
            0,
        )

        grouped["raw_score"] = (100 * (1 - grouped["defect_rate"])).clip(0, 100)
        grouped["weighted_score"] = grouped["raw_score"] * self.weight

        logger.info(f"Scored {len(grouped)} suppliers on defect rate")
        return grouped.round(4)
