-- Logistics Data Warehouse Star Schema
-- Designed for supply chain control tower and supplier risk analytics

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE dim_date (
    date_key        INT PRIMARY KEY,
    full_date       DATE NOT NULL,
    day_of_week     SMALLINT,
    day_name        VARCHAR(10),
    week_of_year    SMALLINT,
    month           SMALLINT,
    month_name      VARCHAR(10),
    quarter         SMALLINT,
    year            SMALLINT,
    is_weekend      BIT,
    is_holiday      BIT,
    fiscal_quarter  SMALLINT,
    fiscal_year     SMALLINT
);

CREATE TABLE dim_supplier (
    supplier_key    INT IDENTITY PRIMARY KEY,
    supplier_id     VARCHAR(20) NOT NULL,
    supplier_name   VARCHAR(200),
    country         VARCHAR(100),
    region          VARCHAR(50),
    category        VARCHAR(100),
    tier            SMALLINT,
    payment_terms   VARCHAR(50),
    contract_start  DATE,
    contract_end    DATE,
    is_active       BIT DEFAULT 1,
    created_at      DATETIME DEFAULT GETDATE(),
    updated_at      DATETIME DEFAULT GETDATE()
);

CREATE TABLE dim_carrier (
    carrier_key     INT IDENTITY PRIMARY KEY,
    carrier_id      VARCHAR(20) NOT NULL,
    carrier_name    VARCHAR(200),
    carrier_type    VARCHAR(50),  -- FTL, LTL, Parcel, Air, Ocean
    region          VARCHAR(50),
    service_level   VARCHAR(50),  -- Standard, Express, Economy
    is_active       BIT DEFAULT 1,
    created_at      DATETIME DEFAULT GETDATE()
);

CREATE TABLE dim_warehouse (
    warehouse_key   INT IDENTITY PRIMARY KEY,
    warehouse_id    VARCHAR(20) NOT NULL,
    warehouse_name  VARCHAR(200),
    warehouse_type  VARCHAR(50),  -- DC, Regional, Cross-Dock
    city            VARCHAR(100),
    state           VARCHAR(50),
    country         VARCHAR(100),
    capacity_sqft   INT,
    is_active       BIT DEFAULT 1
);

CREATE TABLE dim_lane (
    lane_key        INT IDENTITY PRIMARY KEY,
    lane_id         VARCHAR(50) NOT NULL,
    origin_city     VARCHAR(100),
    origin_state    VARCHAR(50),
    origin_country  VARCHAR(100),
    dest_city       VARCHAR(100),
    dest_state      VARCHAR(50),
    dest_country    VARCHAR(100),
    distance_miles  DECIMAL(10,2),
    transport_mode  VARCHAR(50),
    is_active       BIT DEFAULT 1
);

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE fact_purchase_orders (
    po_key              BIGINT IDENTITY PRIMARY KEY,
    po_number           VARCHAR(20) NOT NULL,
    po_item             VARCHAR(10),
    date_key            INT REFERENCES dim_date(date_key),
    supplier_key        INT REFERENCES dim_supplier(supplier_key),
    warehouse_key       INT REFERENCES dim_warehouse(warehouse_key),
    material_number     VARCHAR(40),
    material_desc       VARCHAR(200),
    order_quantity      DECIMAL(15,3),
    unit_of_measure     VARCHAR(10),
    unit_price          DECIMAL(15,4),
    total_value         DECIMAL(15,2),
    currency            VARCHAR(5),
    requested_date      DATE,
    confirmed_date      DATE,
    actual_receipt_date DATE,
    receipt_quantity     DECIMAL(15,3),
    quality_status      VARCHAR(20),
    defect_quantity      DECIMAL(15,3) DEFAULT 0,
    po_status           VARCHAR(20),
    lead_time_days      INT,
    is_on_time          BIT,
    is_in_full          BIT,
    is_otif             BIT,
    created_at          DATETIME DEFAULT GETDATE()
);

CREATE TABLE fact_shipments (
    shipment_key        BIGINT IDENTITY PRIMARY KEY,
    shipment_id         VARCHAR(30) NOT NULL,
    date_key            INT REFERENCES dim_date(date_key),
    carrier_key         INT REFERENCES dim_carrier(carrier_key),
    lane_key            INT REFERENCES dim_lane(lane_key),
    origin_warehouse_key INT REFERENCES dim_warehouse(warehouse_key),
    dest_warehouse_key  INT REFERENCES dim_warehouse(warehouse_key),
    supplier_key        INT REFERENCES dim_supplier(supplier_key),
    shipment_type       VARCHAR(20),  -- Inbound, Outbound, Transfer
    transport_mode      VARCHAR(20),  -- FTL, LTL, Parcel, Air
    weight_lbs          DECIMAL(12,2),
    volume_cuft         DECIMAL(12,2),
    pieces              INT,
    freight_cost        DECIMAL(12,2),
    accessorial_cost    DECIMAL(12,2) DEFAULT 0,
    total_cost          DECIMAL(12,2),
    planned_ship_date   DATE,
    actual_ship_date    DATE,
    planned_delivery    DATE,
    actual_delivery     DATE,
    is_on_time          BIT,
    delay_hours         DECIMAL(8,2) DEFAULT 0,
    dwell_time_hours    DECIMAL(8,2),
    exception_flag      BIT DEFAULT 0,
    exception_type      VARCHAR(50),
    exception_desc      VARCHAR(500),
    status              VARCHAR(30),
    created_at          DATETIME DEFAULT GETDATE()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_fact_po_date ON fact_purchase_orders(date_key);
CREATE INDEX idx_fact_po_supplier ON fact_purchase_orders(supplier_key);
CREATE INDEX idx_fact_po_warehouse ON fact_purchase_orders(warehouse_key);
CREATE INDEX idx_fact_ship_date ON fact_shipments(date_key);
CREATE INDEX idx_fact_ship_carrier ON fact_shipments(carrier_key);
CREATE INDEX idx_fact_ship_lane ON fact_shipments(lane_key);
CREATE INDEX idx_fact_ship_supplier ON fact_shipments(supplier_key);
CREATE INDEX idx_fact_ship_status ON fact_shipments(status);
