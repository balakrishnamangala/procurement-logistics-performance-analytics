"""Power BI REST API data connector configuration.

Provides M (Power Query) snippets and OData-compatible endpoints
for connecting Power BI dashboards to the control tower API.
"""
from typing import Optional


def get_powerbi_query(base_url: str = "http://localhost:8000") -> dict:
    """Generate Power Query M code for Power BI DirectQuery connection."""
    return {
        "dashboard_kpis": f'''
let
    Source = Json.Document(Web.Contents("{base_url}/api/v1/control-tower/dashboard")),
    kpi_tiles = Source[kpi_tiles],
    #"Converted to Table" = Table.FromList(kpi_tiles, Splitter.SplitByNothing()),
    #"Expanded" = Table.ExpandRecordColumn(#"Converted to Table", "Column1",
        {{"name", "value", "unit", "target"}})
in
    #"Expanded"
'''.strip(),
        "supplier_scorecard": f'''
let
    Source = Json.Document(Web.Contents("{base_url}/api/v1/scorecard/suppliers")),
    suppliers = Source[suppliers],
    #"Converted to Table" = Table.FromList(suppliers, Splitter.SplitByNothing()),
    #"Expanded" = Table.ExpandRecordColumn(#"Converted to Table", "Column1",
        {{"supplier_id", "composite_score", "risk_tier", "lead_time_score",
          "otif_trend_score", "defect_score", "spend_score", "trend_direction"}})
in
    #"Expanded"
'''.strip(),
        "shipment_metrics": f'''
let
    Source = Json.Document(Web.Contents("{base_url}/api/v1/control-tower/shipment-metrics")),
    #"Converted to Record" = Record.FromTable(Table.FromRecords({{Source}}))
in
    #"Converted to Record"
'''.strip(),
        "otd_trend": f'''
let
    Source = Json.Document(Web.Contents("{base_url}/api/v1/control-tower/otd-trend?period=daily&days=30")),
    data = Source[data],
    #"Converted to Table" = Table.FromList(data, Splitter.SplitByNothing()),
    #"Expanded" = Table.ExpandRecordColumn(#"Converted to Table", "Column1",
        {{"period", "value", "count"}})
in
    #"Expanded"
'''.strip(),
    }


# DAX measures for Power BI calculated columns
DAX_MEASURES = {
    "OTIF_Rate_Formatted": '''
OTIF Rate =
FORMAT(
    DIVIDE(
        CALCULATE(COUNTROWS('PurchaseOrders'), 'PurchaseOrders'[is_otif] = 1),
        COUNTROWS('PurchaseOrders')
    ),
    "0.0%"
)
''',
    "Risk_Color": '''
Risk Color =
SWITCH(
    'Suppliers'[risk_tier],
    "HIGH", "#FF4444",
    "MEDIUM", "#FFB347",
    "LOW", "#77DD77",
    "#CCCCCC"
)
''',
    "YoY_OTIF_Change": '''
YoY OTIF Change =
VAR CurrentOTIF = [OTIF Rate]
VAR PriorOTIF =
    CALCULATE(
        [OTIF Rate],
        DATEADD('Calendar'[Date], -1, YEAR)
    )
RETURN
    CurrentOTIF - PriorOTIF
''',
}
