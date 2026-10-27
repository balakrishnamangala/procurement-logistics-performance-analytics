"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


class TestHealthEndpoints:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "endpoints" in data


class TestControlTowerEndpoints:
    def test_dashboard(self):
        resp = client.get("/api/v1/control-tower/dashboard")
        assert resp.status_code in [200, 422]

    def test_shipment_metrics(self):
        resp = client.get("/api/v1/control-tower/shipment-metrics")
        assert resp.status_code in [200, 422]

    def test_exceptions(self):
        resp = client.get("/api/v1/control-tower/exceptions")
        assert resp.status_code in [200, 422]

    def test_dwell_time(self):
        resp = client.get("/api/v1/control-tower/dwell-time")
        assert resp.status_code in [200, 422]

    def test_lane_costs(self):
        resp = client.get("/api/v1/control-tower/lane-costs")
        assert resp.status_code in [200, 422]


class TestScorecardEndpoints:
    def test_supplier_scorecard(self):
        resp = client.get("/api/v1/scorecard/suppliers")
        assert resp.status_code in [200, 422]

    def test_high_risk(self):
        resp = client.get("/api/v1/scorecard/high-risk")
        assert resp.status_code in [200, 422]

    def test_supplier_not_found(self):
        resp = client.get("/api/v1/scorecard/suppliers/NONEXISTENT")
        assert resp.status_code in [404, 422]
