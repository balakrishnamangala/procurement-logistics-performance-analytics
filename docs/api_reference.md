# API Reference

Base URL: `http://localhost:8000`

## Control Tower

### GET /api/v1/control-tower/dashboard
Returns KPI tiles for the logistics control tower.

Query params: `from_date`, `to_date`, `warehouse_id`

### GET /api/v1/control-tower/shipment-metrics
Aggregate shipment performance metrics.

Query params: `carrier_id`, `days` (default: 30)

### GET /api/v1/control-tower/otd-trend
OTD rate trend over time.

Query params: `period` (daily|weekly|monthly), `days`

### GET /api/v1/control-tower/exceptions
Exception analysis with type breakdown.

Query params: `carrier_id`, `exception_type`, `days`

### GET /api/v1/control-tower/dwell-time
Warehouse dwell time analysis.

Query params: `warehouse_id`

### GET /api/v1/control-tower/lane-costs
Lane cost analysis with top spend identification.

Query params: `top_n` (default: 10)

## Supplier Scorecard

### GET /api/v1/scorecard/suppliers
Full supplier risk scorecard.

Query params: `risk_tier` (HIGH|MEDIUM|LOW)

### GET /api/v1/scorecard/suppliers/{supplier_id}
Detailed risk breakdown for one supplier.

### GET /api/v1/scorecard/high-risk
List of high-risk suppliers requiring action.

### GET /api/v1/scorecard/otif-trend
Supplier OTIF trend over time.

Query params: `supplier_id`, `months` (default: 6)
