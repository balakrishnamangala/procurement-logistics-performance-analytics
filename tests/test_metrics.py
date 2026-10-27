"""Unit tests for metric calculators."""
import pytest
from src.metrics import OTIFCalculator, OTDCalculator, DwellTimeAnalyzer, LaneCostAnalyzer, ExceptionTracker


class TestOTIFCalculator:
    def test_overall_otif(self, sample_po_data):
        calc = OTIFCalculator()
        result = calc.calculate(sample_po_data)
        assert 0 <= result["overall"] <= 1.0
        assert "by_supplier" in result
        assert "trend" in result

    def test_by_supplier(self, sample_po_data):
        calc = OTIFCalculator()
        result = calc.calculate(sample_po_data)
        assert len(result["by_supplier"]) > 0
        for _, v in result["by_supplier"].items():
            assert 0 <= v["otif_rate"] <= 1.0

    def test_empty_data(self):
        import pandas as pd
        calc = OTIFCalculator()
        result = calc.calculate(pd.DataFrame())
        assert result["overall"] == 0.0


class TestOTDCalculator:
    def test_overall_otd(self, sample_shipment_data):
        calc = OTDCalculator()
        result = calc.calculate(sample_shipment_data)
        assert 0 <= result["overall_otd"] <= 1.0

    def test_by_carrier(self, sample_shipment_data):
        calc = OTDCalculator()
        result = calc.calculate(sample_shipment_data)
        assert len(result["by_carrier"]) > 0

    def test_late_analysis(self, sample_shipment_data):
        calc = OTDCalculator()
        result = calc.calculate(sample_shipment_data)
        assert "late_shipment_analysis" in result


class TestDwellTimeAnalyzer:
    def test_analyze(self, sample_shipment_data):
        analyzer = DwellTimeAnalyzer()
        result = analyzer.analyze(sample_shipment_data)
        assert result["avg_dwell_hours"] >= 0


class TestLaneCostAnalyzer:
    def test_analyze(self, sample_shipment_data):
        analyzer = LaneCostAnalyzer()
        result = analyzer.analyze(sample_shipment_data)
        assert result["total_freight_cost"] > 0
        assert "by_carrier" in result


class TestExceptionTracker:
    def test_analyze(self, sample_shipment_data):
        tracker = ExceptionTracker()
        result = tracker.analyze(sample_shipment_data)
        assert result["total_shipments"] == len(sample_shipment_data)
        assert 0 <= result["exception_rate"] <= 1.0
