"""Spend concentration scoring using Herfindahl-Hirschman Index (HHI)."""
import pandas as pd
import numpy as np
from src.utils import get_logger

logger = get_logger("spend_concentration")


class SpendConcentrationScorer:
    """Scores supply base diversification using HHI.

    HHI = sum of squared market shares across suppliers.
    HHI > 0.25 = highly concentrated (single-source risk)
    HHI 0.15-0.25 = moderately concentrated
    HHI < 0.15 = diversified
    """

    def __init__(self, weight: float = 0.20,
                 hhi_high: float = 0.25, hhi_moderate: float = 0.15):
        self.weight = weight
        self.hhi_high = hhi_high
        self.hhi_moderate = hhi_moderate

    def score(self, po_data: pd.DataFrame, category_col: str = "material_group") -> pd.DataFrame:
        if po_data.empty:
            return pd.DataFrame()

        df = po_data.copy()
        if "total_value" not in df.columns:
            if "order_quantity" in df.columns and "unit_price" in df.columns:
                df["total_value"] = df["order_quantity"] * df["unit_price"]
            elif "net_value" in df.columns:
                df["total_value"] = df["net_value"]
            else:
                df["total_value"] = 1

        if category_col in df.columns:
            return self._score_by_category(df, category_col)
        else:
            return self._score_overall(df)

    def _score_by_category(self, df: pd.DataFrame, category_col: str) -> pd.DataFrame:
        results = []
        for category, group in df.groupby(category_col):
            hhi, supplier_shares = self._compute_hhi(group)
            raw_score = self._hhi_to_score(hhi)
            results.append({
                "category": category,
                "hhi": round(hhi, 4),
                "concentration_level": self._classify(hhi),
                "supplier_count": len(supplier_shares),
                "top_supplier_share": round(supplier_shares.iloc[0], 4) if len(supplier_shares) > 0 else 0,
                "raw_score": round(raw_score, 2),
                "weighted_score": round(raw_score * self.weight, 2),
            })
        return pd.DataFrame(results)

    def _score_overall(self, df: pd.DataFrame) -> pd.DataFrame:
        hhi, supplier_shares = self._compute_hhi(df)
        raw_score = self._hhi_to_score(hhi)
        return pd.DataFrame([{
            "category": "ALL",
            "hhi": round(hhi, 4),
            "concentration_level": self._classify(hhi),
            "supplier_count": len(supplier_shares),
            "top_supplier_share": round(supplier_shares.iloc[0], 4) if len(supplier_shares) > 0 else 0,
            "raw_score": round(raw_score, 2),
            "weighted_score": round(raw_score * self.weight, 2),
        }])

    def _compute_hhi(self, df: pd.DataFrame) -> tuple:
        if "supplier_id" not in df.columns:
            return 1.0, pd.Series()
        spend = df.groupby("supplier_id")["total_value"].sum()
        total = spend.sum()
        if total == 0:
            return 1.0, pd.Series()
        shares = (spend / total).sort_values(ascending=False)
        hhi = float((shares ** 2).sum())
        return hhi, shares

    def _hhi_to_score(self, hhi: float) -> float:
        """Convert HHI to 0-100 score (lower HHI = higher score = lower risk)."""
        return float(np.clip(100 * (1 - hhi), 0, 100))

    def _classify(self, hhi: float) -> str:
        if hhi >= self.hhi_high:
            return "highly_concentrated"
        elif hhi >= self.hhi_moderate:
            return "moderately_concentrated"
        return "diversified"
