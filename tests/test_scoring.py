"""Unit tests for supplier risk scoring modules."""
import pytest
import pandas as pd
from src.scoring import LeadTimeScorer, OTIFTrendScorer, DefectRateScorer, SpendConcentrationScorer, CompositeScorer


class TestLeadTimeScorer:
    def test_score(self, sample_po_data):
        scorer = LeadTimeScorer()
        result = scorer.score(sample_po_data)
        assert not result.empty
        assert "raw_score" in result.columns
        assert all(0 <= s <= 100 for s in result["raw_score"])

    def test_empty(self):
        scorer = LeadTimeScorer()
        result = scorer.score(pd.DataFrame())
        assert result.empty


class TestOTIFTrendScorer:
    def test_score(self, sample_po_data):
        scorer = OTIFTrendScorer()
        result = scorer.score(sample_po_data)
        assert not result.empty
        assert "trend_direction" in result.columns

    def test_trend_directions(self, sample_po_data):
        scorer = OTIFTrendScorer()
        result = scorer.score(sample_po_data)
        valid = {"improving", "stable", "declining"}
        assert all(d in valid for d in result["trend_direction"])


class TestDefectRateScorer:
    def test_score(self, sample_po_data):
        scorer = DefectRateScorer()
        result = scorer.score(sample_po_data)
        assert not result.empty
        assert all(0 <= s <= 100 for s in result["raw_score"])


class TestSpendConcentrationScorer:
    def test_score(self, sample_po_data):
        scorer = SpendConcentrationScorer()
        result = scorer.score(sample_po_data)
        assert not result.empty
        assert "hhi" in result.columns
        assert all(0 <= h <= 1 for h in result["hhi"])

    def test_classification(self):
        scorer = SpendConcentrationScorer()
        assert scorer._classify(0.30) == "highly_concentrated"
        assert scorer._classify(0.20) == "moderately_concentrated"
        assert scorer._classify(0.10) == "diversified"


class TestCompositeScorer:
    def test_score_all(self, sample_po_data):
        scorer = CompositeScorer()
        result = scorer.score_all(sample_po_data)
        assert not result.empty
        assert "risk_tier" in result.columns
        assert all(t in ["HIGH", "MEDIUM", "LOW"] for t in result["risk_tier"])

    def test_high_risk_suppliers(self, sample_po_data):
        scorer = CompositeScorer()
        high_risk = scorer.get_high_risk_suppliers(sample_po_data)
        if not high_risk.empty:
            assert all(high_risk["risk_tier"] == "HIGH")

    def test_report(self, sample_po_data):
        scorer = CompositeScorer()
        report = scorer.generate_report(sample_po_data)
        assert report["total_suppliers"] > 0
        total = report["high_risk_count"] + report["medium_risk_count"] + report["low_risk_count"]
        assert total == report["total_suppliers"]
