"""Generate realistic sample data for development and testing."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

SUPPLIERS = [f"SUP-{i:04d}" for i in range(1, 26)]
CARRIERS = [f"CAR-{i:03d}" for i in range(1, 11)]
WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"]
MATERIAL_GROUPS = ["RAW_MATERIAL", "PACKAGING", "MRO", "COMPONENTS", "CHEMICALS"]
MODES = ["FTL", "LTL", "INTERMODAL", "AIR", "OCEAN"]


def generate_purchase_orders(n=2000):
    start = datetime(2024, 1, 1)
    records = []
    for i in range(n):
        po_date = start + timedelta(days=np.random.randint(0, 365))
        lead = np.random.randint(5, 45)
        requested = po_date + timedelta(days=lead)
        delay = np.random.choice([0, 0, 0, 1, 2, 3, 5, 8], p=[0.4, 0.15, 0.1, 0.1, 0.08, 0.07, 0.05, 0.05])
        actual = requested + timedelta(days=int(delay))
        qty = np.random.randint(100, 5000)
        recv_pct = np.random.choice([1.0, 1.0, 0.98, 0.95, 0.90, 0.85], p=[0.5, 0.2, 0.1, 0.1, 0.05, 0.05])
        defect_rate = np.random.choice([0, 0, 0, 0.01, 0.02, 0.05], p=[0.6, 0.15, 0.1, 0.08, 0.04, 0.03])

        records.append({
            "po_number": f"PO-{i+1:06d}",
            "po_item": "10",
            "supplier_id": np.random.choice(SUPPLIERS),
            "material_group": np.random.choice(MATERIAL_GROUPS),
            "po_date": po_date.strftime("%Y-%m-%d"),
            "requested_date": requested.strftime("%Y-%m-%d"),
            "actual_receipt_date": actual.strftime("%Y-%m-%d"),
            "order_quantity": qty,
            "receipt_quantity": int(qty * recv_pct),
            "defect_quantity": int(qty * defect_rate),
            "unit_price": round(np.random.uniform(5, 500), 2),
            "net_value": round(qty * np.random.uniform(5, 500), 2),
            "plant": np.random.choice(WAREHOUSES),
            "currency": "USD",
        })
    return pd.DataFrame(records)


def generate_shipments(n=1500):
    start = datetime(2024, 1, 1)
    records = []
    origins = WAREHOUSES + ["VENDOR-A", "VENDOR-B", "PORT-LA", "PORT-NY"]
    dests = WAREHOUSES + ["DC-NORTH", "DC-SOUTH", "CUSTOMER-HUB"]

    for i in range(n):
        ship_date = start + timedelta(days=np.random.randint(0, 365))
        transit = np.random.randint(1, 14)
        planned = ship_date + timedelta(days=transit)
        delay_hrs = np.random.choice([0, 0, 0, 2, 6, 12, 24, 48], p=[0.45, 0.15, 0.1, 0.1, 0.08, 0.05, 0.04, 0.03])
        actual = planned + timedelta(hours=int(delay_hrs))
        has_exception = 1 if np.random.random() < 0.08 else 0
        exc_types = ["LATE_DELIVERY", "DAMAGED", "SHORT_SHIP", "DOCUMENTATION", "CARRIER_ISSUE", "OTHER"]

        records.append({
            "shipment_id": f"SHP-{i+1:06d}",
            "carrier_id": np.random.choice(CARRIERS),
            "origin_id": np.random.choice(origins),
            "destination_id": np.random.choice(dests),
            "transport_mode": np.random.choice(MODES, p=[0.35, 0.25, 0.15, 0.15, 0.10]),
            "planned_ship_date": ship_date.strftime("%Y-%m-%d"),
            "actual_ship_date": ship_date.strftime("%Y-%m-%d"),
            "planned_delivery": planned.strftime("%Y-%m-%d %H:%M"),
            "actual_delivery": actual.strftime("%Y-%m-%d %H:%M"),
            "weight": round(np.random.uniform(500, 20000), 1),
            "units": np.random.randint(10, 500),
            "freight_cost": round(np.random.uniform(200, 5000), 2),
            "accessorial_cost": round(np.random.uniform(0, 500), 2),
            "dwell_time_hours": round(np.random.uniform(1, 12), 1),
            "exception_flag": has_exception,
            "exception_type": np.random.choice(exc_types) if has_exception else None,
            "delay_hours": delay_hrs,
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))

    pos = generate_purchase_orders(2000)
    pos.to_csv(os.path.join(out, "sample_purchase_orders.csv"), index=False)

    ships = generate_shipments(1500)
    ships.to_csv(os.path.join(out, "sample_shipments.csv"), index=False)

    print(f"Generated {len(pos)} POs and {len(ships)} shipments in {out}/")
