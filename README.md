# Real-Time Logistics Control Tower & Supplier Risk Scorecard

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A real-time logistics control tower that consolidates SAP S/4HANA purchase order, EWM warehouse, and TMS carrier data into a unified star schema. Exposes OTIF, OTD, dwell time, lane cost, and exception trends through a drill-down Power BI dashboard refreshed every 15 minutes. Includes a weighted supplier risk scorecard that flagged 7 high-risk suppliers for mitigation.

## Key Results

- **19% reduction in late shipments** through proactive supplier risk identification
- **12% reduction in expedite freight spend** in the pilot quarter
- **7 high-risk suppliers flagged** via composite weighted scorecard
- **15-minute refresh cycle** for near real-time logistics visibility

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SAP S/4HANA │  │  SAP EWM     │  │  TMS Carrier  │
│  (PO Data)   │  │  (Warehouse) │  │  (Shipments)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│              ETL Orchestrator                    │
│         (Extract, Transform, Load)               │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Star Schema (SQL)                   │
│  fact_shipments │ fact_purchase_orders           │
│  dim_supplier │ dim_carrier │ dim_warehouse      │
│  dim_lane │ dim_date                             │
└──────────┬──────────────────┬───────────────────┘
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│ Logistics Metrics │  │ Supplier Risk    │
│ OTIF, OTD, Dwell  │  │ Scorecard Engine │
│ Lane Cost, Trends  │  │ (Weighted Model) │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────────────────┐
│         FastAPI REST Endpoints                   │
│    /api/v1/control-tower  │  /api/v1/scorecard  │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         Power BI Control Tower Dashboard         │
│    KPI Tiles │ Trend Charts │ Drill-Down Views   │
└─────────────────────────────────────────────────┘
```

## Tech Stack

- **Data Integration**: SAP S/4HANA, SAP EWM, TMS APIs
- **Data Processing**: Python, Pandas, SQLAlchemy
- **Database**: SQL Server / Azure SQL (Star Schema)
- **API**: FastAPI, Pydantic
- **Visualization**: Power BI, DAX, Microsoft Fabric
- **Infrastructure**: Docker, GitHub Actions CI/CD

## Quick Start

```bash
git clone https://github.com/balakrishnamangala/procurement-logistics-performance-analytics.git
cd procurement-logistics-performance-analytics

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Generate sample data
python scripts/generate_sample_data.py

# Run ETL pipeline
python -m src.etl.orchestrator --config config/etl_config.yaml

# Launch API
uvicorn src.api.main:app --reload

# Run tests
pytest tests/ -v
```

## Project Structure

```
├── config/                  # YAML configuration files
├── data/
│   ├── raw/                # Raw extracts from source systems
│   ├── processed/          # Transformed star schema data
│   └── sample/             # Generated sample datasets
├── docs/                   # Documentation and diagrams
├── notebooks/              # Jupyter notebooks for analysis
├── scripts/                # Utility scripts
├── src/
│   ├── api/               # FastAPI endpoints
│   ├── dashboard/         # Dashboard data aggregation
│   ├── etl/               # Extract-Transform-Load pipeline
│   ├── metrics/           # Logistics KPI calculators
│   ├── scoring/           # Supplier risk scoring engine
│   └── utils/             # Shared utilities
└── tests/                 # Unit and integration tests
```

## License

MIT License
