# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # Logistics Data Exploration
# Exploratory analysis of procurement and shipment data for control tower KPIs.

# %%
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, "..")

# %%
# Load sample data
pos = pd.read_csv("../data/sample/sample_purchase_orders.csv")
ships = pd.read_csv("../data/sample/sample_shipments.csv")

print(f"Purchase Orders: {len(pos):,} rows")
print(f"Shipments: {len(ships):,} rows")

# %%
# OTIF Analysis
from src.metrics import OTIFCalculator
calc = OTIFCalculator()

pos["requested_date"] = pd.to_datetime(pos["requested_date"])
pos["actual_receipt_date"] = pd.to_datetime(pos["actual_receipt_date"])
pos["is_on_time"] = (pos["actual_receipt_date"] <= pos["requested_date"]).astype(int)
pos["is_in_full"] = (pos["receipt_quantity"] >= pos["order_quantity"] * 0.98).astype(int)
pos["is_otif"] = (pos["is_on_time"] & pos["is_in_full"]).astype(int)

result = calc.calculate(pos)
print(f"Overall OTIF: {result['overall']:.1%}")
print(f"Suppliers analyzed: {len(result['by_supplier'])}")

# %%
# OTD Analysis
from src.metrics import OTDCalculator
otd_calc = OTDCalculator()

ships["planned_delivery"] = pd.to_datetime(ships["planned_delivery"])
ships["actual_delivery"] = pd.to_datetime(ships["actual_delivery"])

otd_result = otd_calc.calculate(ships)
print(f"Overall OTD: {otd_result['overall_otd']:.1%}")
print(f"Late shipments: {otd_result['late_shipment_analysis']['count']}")

# %%
# Supplier Risk Scorecard
from src.scoring import CompositeScorer
scorer = CompositeScorer()
scores = scorer.score_all(pos)

print(f"\nSupplier Risk Distribution:")
print(scores["risk_tier"].value_counts())
print(f"\nTop 5 High-Risk Suppliers:")
print(scores.nsmallest(5, "composite_score")[["supplier_id", "composite_score", "risk_tier"]])
