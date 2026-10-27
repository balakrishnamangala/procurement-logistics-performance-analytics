# System Architecture

## Overview

The Logistics Control Tower & Supplier Risk Scorecard is a real-time analytics platform
that integrates SAP S/4HANA procurement data, SAP EWM warehouse operations, and TMS
shipment tracking into a unified star schema data warehouse.

## Data Flow

```
SAP S/4HANA ──┐
  (EKKO/EKPO) │
  (MKPF/MSEG) ├──► ETL Orchestrator ──► Star Schema DW ──► Metrics Engine
  (LFA1)      │         │                                        │
SAP EWM ──────┤    Incremental &                           ┌─────┴─────┐
  (Deliveries)│    Full Load (15min)                       │           │
  (Tasks)     │                                      Control      Supplier
TMS API ──────┘                                      Tower        Risk
  (Shipments)                                        KPIs         Scorecard
  (Tracking)                                           │           │
                                                       └─────┬─────┘
                                                             │
                                                        FastAPI REST
                                                             │
                                                    ┌────────┴────────┐
                                                    │                 │
                                                Power BI          Alerting
                                                Dashboard         System
```

## Star Schema

### Fact Tables
- **fact_purchase_orders**: PO line items with OTIF flags, lead times, defect quantities
- **fact_shipments**: Shipment records with delay hours, dwell time, exception flags

### Dimension Tables
- **dim_supplier**: Vendor master from SAP LFA1
- **dim_carrier**: Carrier master from TMS
- **dim_warehouse**: Warehouse/plant locations
- **dim_lane**: Origin-destination shipping lanes
- **dim_date**: Calendar dimension with fiscal periods

## Risk Scoring Model

| Dimension | Weight | Method |
|-----------|--------|--------|
| Lead Time Variability | 30% | 100 × (1 − CV) |
| OTIF Trend | 25% | Current rate + slope adjustment |
| Defect Rate | 25% | 100 × (1 − defect_rate) |
| Spend Concentration | 20% | 100 × (1 − HHI) |

Risk Tiers: **HIGH** (< 40) · **MEDIUM** (40–70) · **LOW** (> 70)

## Technology Stack
- **ETL**: Python, pandas, SQLAlchemy
- **Database**: PostgreSQL 15
- **API**: FastAPI, Pydantic
- **Visualization**: Power BI (DirectQuery to API)
- **Infrastructure**: Docker, GitHub Actions CI
- **Source Systems**: SAP S/4HANA, SAP EWM, TMS REST API
