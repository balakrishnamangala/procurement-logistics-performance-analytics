"""OTIF trend scoring for supplier risk assessment."""
import pandas as pd
import numpy as np
from src.utils import get_logger

logger = get_logger("otif_trend_scorer")


class OTIFTrendScorer:
    """Scores suppliers on OTIF performance trend over rolling windows.

    Combines current OTIF rate with directional trend (improving/declining).
    A declining trend from a high OTIF is riskier than a stable moderate one.
    """

    def __init__(self, weight: float = 0.25, lookback_periods: int = 6):
        self.weight = weight
        self.lookback_periods = lookback_periods

    def score(self, po_data: pd.DataFrame) -> pd.DataFrame:
        if po_data.empty or "supplier_id" not in po_data.columns:
            return pd.DataFrame()

        df = po_data.copy()
        df["requested_date"] = pd.to_datetime(df.get("requested_date"), errors="coerce")

        if "is_otif" not in df.columns:
            df["is_otif"] = 0

        results = []
        for supplier_id, group in df.groupby("supplier_id"):
            group = group.sort_values("requested_date")
            current_otif = group["is_otif"].mean()

            group["period"] = group["requested_date"].dt.to_period("M")
            monthly = group.groupby("period")["is_otif"].mean().reset_index()
            monthly.columns = ["period", "otif_rate"]

            recent = monthly.tail(self.lookback_periods)
            if len(recent) >= 2:
                x = np.arange(len(recent))
                slope = np.polyfit(x, recent["otif_rate"].values, 1)[0]
            else:
                slope = 0.0

            base_score = current_otif * 100
            trend_adjustment = slope * 50
            raw_score = np.clip(base_score + trend_adjustment, 0, 100)

            results.append({
                "supplier_id": supplier_id,
                "current_otif": round(current_otif, 4),
                "otif_trend_slope": round(slope, 6),
                "trend_direction": "improving" if slope > 0.005 else ("declining" if slope < -0.005 else "stable"),
                "periods_analyzed": len(recent),
                "raw_score": round(raw_score, 2),
                "weighted_score": round(raw_score * self.weight, 2),
            })

        result_df = pd.DataFrame(results)
        logger.info(f"Scored {len(result_df)} suppliers on OTIF trend")
        return result_df
