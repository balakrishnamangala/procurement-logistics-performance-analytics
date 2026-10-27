"""Composite supplier risk scorecard combining all risk dimensions."""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

from src.scoring.lead_time_scorer import LeadTimeScorer
from src.scoring.otif_trend_scorer import OTIFTrendScorer
from src.scoring.defect_rate_scorer import DefectRateScorer
from src.scoring.spend_concentration_scorer import SpendConcentrationScorer
from src.utils import get_logger, load_config

logger = get_logger("composite_scorer")


class CompositeScorer:
    """Weighted composite supplier risk scorecard.

    Combines four risk dimensions:
    - Lead time variability (30%)
    - OTIF trend (25%)
    - Defect rate (25%)
    - Spend concentration (20%)

    Risk tiers: High (< 40), Medium (40-70), Low (> 70)
    """

    def __init__(self, config_path: str = "config/scoring_config.yaml"):
        config = load_config(config_path)
        weights = config.get("risk_weights", {})

        self.lead_time = LeadTimeScorer(weight=weights.get("lead_time", 0.30))
        self.otif_trend = OTIFTrendScorer(weight=weights.get("otif", 0.25))
        self.defect = DefectRateScorer(weight=weights.get("defect", 0.25))
        self.spend = SpendConcentrationScorer(weight=weights.get("spend", 0.20))

        thresholds = config.get("risk_thresholds", {})
        self.high_threshold = thresholds.get("high", 70)
        self.medium_threshold = thresholds.get("medium", 40)

    def score_all(self, po_data: pd.DataFrame) -> pd.DataFrame:
        """Generate composite risk scores for all suppliers."""
        if po_data.empty:
            return pd.DataFrame()

        lt_scores = self.lead_time.score(po_data)
        otif_scores = self.otif_trend.score(po_data)
        defect_scores = self.defect.score(po_data)
        spend_scores = self.spend.score(po_data)

        suppliers = po_data["supplier_id"].unique()
        results = []

        for supplier_id in suppliers:
            lt_row = lt_scores[lt_scores["supplier_id"] == supplier_id]
            otif_row = otif_scores[otif_scores["supplier_id"] == supplier_id]
            defect_row = defect_scores[defect_scores["supplier_id"] == supplier_id]

            lt_weighted = float(lt_row["weighted_score"].iloc[0]) if not lt_row.empty else 0
            otif_weighted = float(otif_row["weighted_score"].iloc[0]) if not otif_row.empty else 0
            defect_weighted = float(defect_row["weighted_score"].iloc[0]) if not defect_row.empty else 0
            spend_weighted = float(spend_scores["weighted_score"].mean()) if not spend_scores.empty else 0

            composite = lt_weighted + otif_weighted + defect_weighted + spend_weighted

            results.append({
                "supplier_id": supplier_id,
                "lead_time_score": float(lt_row["raw_score"].iloc[0]) if not lt_row.empty else 0,
                "otif_trend_score": float(otif_row["raw_score"].iloc[0]) if not otif_row.empty else 0,
                "defect_score": float(defect_row["raw_score"].iloc[0]) if not defect_row.empty else 0,
                "spend_score": float(spend_scores["raw_score"].mean()) if not spend_scores.empty else 0,
                "composite_score": round(composite, 2),
                "risk_tier": self._classify(composite),
                "trend_direction": str(otif_row["trend_direction"].iloc[0]) if not otif_row.empty else "unknown",
            })

        result_df = pd.DataFrame(results).sort_values("composite_score", ascending=True)

        high_risk = result_df[result_df["risk_tier"] == "HIGH"]
        logger.info(
            f"Scored {len(result_df)} suppliers: "
            f"{len(high_risk)} high-risk, "
            f"{len(result_df[result_df['risk_tier'] == 'MEDIUM'])} medium-risk"
        )
        return result_df

    def _classify(self, score: float) -> str:
        if score >= self.high_threshold:
            return "LOW"
        elif score >= self.medium_threshold:
            return "MEDIUM"
        return "HIGH"

    def get_high_risk_suppliers(self, po_data: pd.DataFrame) -> pd.DataFrame:
        scores = self.score_all(po_data)
        return scores[scores["risk_tier"] == "HIGH"]

    def generate_report(self, po_data: pd.DataFrame) -> dict:
        scores = self.score_all(po_data)
        return {
            "total_suppliers": len(scores),
            "high_risk_count": len(scores[scores["risk_tier"] == "HIGH"]),
            "medium_risk_count": len(scores[scores["risk_tier"] == "MEDIUM"]),
            "low_risk_count": len(scores[scores["risk_tier"] == "LOW"]),
            "avg_composite_score": round(float(scores["composite_score"].mean()), 2),
            "high_risk_suppliers": scores[scores["risk_tier"] == "HIGH"].to_dict(orient="records"),
            "generated_at": datetime.now().isoformat(),
        }
