# 🏭 Real-Time Logistics Control Tower & Supplier Risk Scorecard

[![CI](https://github.com/balakrishnamangala/procurement-logistics-performance-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/balakrishnamangala/procurement-logistics-performance-analytics/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

An end-to-end analytics platform integrating **SAP S/4HANA**, **SAP EWM**, and **TMS** data into a unified logistics monitoring system with real-time KPIs and weighted supplier risk scoring.

## 📊 Key Results

| Metric | Impact |
|--------|--------|
| Late shipment reduction | **19% decrease** in late deliveries through carrier performance visibility |
| Expedite freight savings | **12% reduction** in expedited shipping costs via exception trend detection |
| Supplier risk identification | **7 high-risk suppliers** flagged for procurement action |
| Dashboard refresh | **15-minute** automated ETL cycle from source systems |

## 🏗️ Architecture

```
SAP S/4HANA ──┐
  (EKKO/EKPO) │
  (MKPF/MSEG) ├──► ETL Orchestrator ──► Star Schema DW ──► Metrics Engine
  (LFA1)      │         │                                        │
SAP EWM ──────┤    15-min refresh                          ┌─────┴─────┐
  (Deliveries)│                                            │           │
  (Tasks)     │                                       Control      Supplier
TMS API ──────┘                                       Tower        Risk
  (Shipments)                                         KPIs         Scorecard
  (Tracking)                                            │           │
                                                        └─────┬─────┘
                                                              │
                                                         FastAPI REST
                                                              │
                                                     ┌────────┴────────┐
                                                  Power BI          Alerting
```

## 🛠️ Tech Stack

- **Languages**: Python 3.10+, SQL, DAX
- **ETL**: pandas, SQLAlchemy, SAP RFC/REST connectors
- **Database**: PostgreSQL 15 (star schema)
- **API**: FastAPI, Pydantic, uvicorn
- **Visualization**: Power BI (DirectQuery to REST API)
- **Infrastructure**: Docker, GitHub Actions CI
- **Source Systems**: SAP S/4HANA, SAP EWM, TMS REST API

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/balakrishnamangala/procurement-logistics-performance-analytics.git
cd procurement-logistics-performance-analytics
cp .env.example .env
pip install -r requirements.txt

# Generate sample data
python data/sample/generate_sample_data.py

# Run API server
make run
# → http://localhost:8000/docs

# Run with Docker
docker-compose up -d
```

## 📁 Project Structure

```
├── src/
│   ├── etl/                    # Data extraction & loading
│   │   ├── sap_extractor.py    # SAP S/4HANA (EKKO, EKPO, MKPF, LFA1)
│   │   ├── ewm_extractor.py    # SAP EWM (deliveries, warehouse tasks)
│   │   ├── tms_extractor.py    # TMS REST API (shipments, carriers)
│   │   └── orchestrator.py     # ETL coordination & scheduling
│   ├── metrics/                # KPI calculators
│   │   ├── otif_calculator.py  # On-Time In-Full rate
│   │   ├── otd_calculator.py   # On-Time Delivery rate
│   │   ├── dwell_time_analyzer.py
│   │   ├── lane_cost_analyzer.py
│   │   └── exception_tracker.py
│   ├── scoring/                # Supplier risk assessment
│   │   ├── lead_time_scorer.py # CV-based lead time variability
│   │   ├── otif_trend_scorer.py# Slope-adjusted OTIF trend
│   │   ├── defect_rate_scorer.py
│   │   ├── spend_concentration_scorer.py  # Herfindahl index
│   │   └── composite_scorer.py # Weighted risk scorecard
│   ├── api/                    # FastAPI REST endpoints
│   │   ├── app.py              # Application factory
│   │   ├── routes.py           # Control tower & scorecard routes
│   │   └── schemas.py          # Pydantic request/response models
│   ├── dashboard/              # Dashboard data aggregation
│   │   ├── data_service.py     # Cached metrics service
│   │   └── powerbi_connector.py# Power Query M & DAX measures
│   └── utils/                  # Shared utilities
├── sql/                        # Database DDL
│   └── star_schema.sql         # Fact & dimension table definitions
├── tests/                      # pytest test suite
├── config/                     # YAML configuration
├── data/sample/                # Sample data generator & CSVs
├── docs/                       # Architecture & API documentation
├── notebooks/                  # Exploratory analysis
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .github/workflows/ci.yml
```

## 📈 Supplier Risk Scoring Model

| Dimension | Weight | Method |
|-----------|--------|--------|
| Lead Time Variability | 30% | `100 × (1 − CV)` where CV = σ/μ of lead times |
| OTIF Trend | 25% | Current OTIF rate + linear regression slope adjustment |
| Defect Rate | 25% | `100 × (1 − defect_qty / received_qty)` |
| Spend Concentration | 20% | `100 × (1 − HHI)` Herfindahl-Hirschman Index |

**Risk Tiers**: HIGH (< 40) · MEDIUM (40–70) · LOW (> 70)

## 🧪 Testing

```bash
make test        # Run full test suite
make lint        # Flake8 linting
make all         # Install + lint + test
```

## 📄 License

MIT
