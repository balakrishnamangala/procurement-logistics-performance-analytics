"""Shared test fixtures."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import sys

# Mock heavy dependencies for faster test startup
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['pyodbc'] = MagicMock()


@pytest.fixture
def sample_po_data():
    np.random.seed(42)
    n = 200
    base = datetime(2024, 6, 1)
    suppliers = [f"SUP-{i:04d}" for i in range(1, 11)]
    data = {
        "po_number": [f"PO-{i:06d}" for i in range(n)],
        "po_item": ["10"] * n,
        "supplier_id": np.random.choice(suppliers, n),
        "material_group": np.random.choice(["RAW", "PKG", "MRO"], n),
        "po_date": [base + timedelta(days=int(d)) for d in np.random.randint(0, 180, n)],
        "requested_date": [base + timedelta(days=int(d)) for d in np.random.randint(20, 200, n)],
        "order_quantity": np.random.randint(100, 2000, n),
        "receipt_quantity": np.random.randint(90, 2000, n),
        "defect_quantity": np.random.choice([0, 0, 0, 5, 10, 20], n),
        "unit_price": np.random.uniform(10, 200, n).round(2),
    }
    df = pd.DataFrame(data)
    df["actual_receipt_date"] = df["requested_date"] + pd.to_timedelta(
        np.random.choice([-1, 0, 0, 1, 2, 3], n), unit="D"
    )
    df["net_value"] = df["order_quantity"] * df["unit_price"]
    df["lead_time_days"] = (df["actual_receipt_date"] - df["po_date"]).dt.days
    df["is_on_time"] = (df["actual_receipt_date"] <= df["requested_date"]).astype(int)
    df["is_in_full"] = (df["receipt_quantity"] >= df["order_quantity"] * 0.98).astype(int)
    df["is_otif"] = (df["is_on_time"] & df["is_in_full"]).astype(int)
    return df


@pytest.fixture
def sample_shipment_data():
    np.random.seed(42)
    n = 150
    base = datetime(2024, 6, 1)
    carriers = [f"CAR-{i:03d}" for i in range(1, 6)]
    data = {
        "shipment_id": [f"SHP-{i:06d}" for i in range(n)],
        "carrier_id": np.random.choice(carriers, n),
        "origin_id": np.random.choice(["WH-E", "WH-W"], n),
        "destination_id": np.random.choice(["DC-N", "DC-S", "CUST"], n),
        "transport_mode": np.random.choice(["FTL", "LTL", "AIR"], n),
        "planned_delivery": [base + timedelta(days=int(d)) for d in np.random.randint(5, 180, n)],
        "freight_cost": np.random.uniform(200, 3000, n).round(2),
        "accessorial_cost": np.random.uniform(0, 300, n).round(2),
        "weight": np.random.uniform(500, 15000, n).round(1),
        "units": np.random.randint(10, 300, n),
        "dwell_time_hours": np.random.uniform(1, 10, n).round(1),
        "exception_flag": np.random.choice([0, 0, 0, 0, 1], n),
        "exception_type": np.random.choice(["LATE_DELIVERY", "DAMAGED", None, None, None], n),
    }
    df = pd.DataFrame(data)
    delays = np.random.choice([0, 0, 0, 2, 6, 12], n)
    df["actual_delivery"] = df["planned_delivery"] + pd.to_timedelta(delays, unit="h")
    df["delay_hours"] = delays
    return df
