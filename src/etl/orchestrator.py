"""ETL orchestrator coordinating all data source extractions and loads."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from src.utils import get_logger, load_config, DatabaseManager
from src.etl.sap_extractor import SAPExtractor
from src.etl.ewm_extractor import EWMExtractor
from src.etl.tms_extractor import TMSExtractor

logger = get_logger("etl_orchestrator")


class ETLOrchestrator:
    """Coordinates extraction from SAP, EWM, and TMS into the star schema.

    Manages incremental and full-load strategies, data transformation,
    and loading into the logistics data warehouse.
    """

    def __init__(self, config_path: str = "config/etl_config.yaml"):
        self.config = load_config(config_path)
        self.sap = SAPExtractor(self.config["sources"]["sap_s4hana"])
        self.ewm = EWMExtractor(self.config["sources"]["sap_ewm"])
        self.tms = TMSExtractor(self.config["sources"]["tms"])
        self.db = DatabaseManager(
            self.config["database"]["connection_string"],
            self.config["database"]["schema"],
        )

    def run_full_load(self) -> dict:
        """Execute a complete ETL cycle across all sources."""
        logger.info("Starting full ETL load")
        stats = {}

        po_data = self._extract_and_transform_pos()
        stats["purchase_orders"] = len(po_data)

        shipment_data = self._extract_and_transform_shipments()
        stats["shipments"] = len(shipment_data)

        warehouse_data = self._extract_and_transform_warehouse()
        stats["warehouse_tasks"] = len(warehouse_data)

        dimensions = self._build_dimensions(po_data, shipment_data)
        stats["dimensions"] = {k: len(v) for k, v in dimensions.items()}

        logger.info(f"ETL complete: {stats}")
        return stats

    def run_incremental(self, since: Optional[datetime] = None) -> dict:
        """Run incremental load for recent changes only."""
        if since is None:
            interval = self.config["schedule"]["refresh_interval_minutes"]
            since = datetime.now() - timedelta(minutes=interval)

        logger.info(f"Incremental load since {since:%Y-%m-%d %H:%M}")
        stats = {}

        po_data = self._extract_and_transform_pos(from_date=since)
        stats["purchase_orders"] = len(po_data)

        shipment_data = self._extract_and_transform_shipments(from_date=since)
        stats["shipments"] = len(shipment_data)

        logger.info(f"Incremental load complete: {stats}")
        return stats

    def _extract_and_transform_pos(
        self, from_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Extract PO and goods receipt data, compute OTIF flags."""
        pos = self.sap.extract_purchase_orders(from_date=from_date)
        receipts = self.sap.extract_goods_receipts(from_date=from_date)

        if pos.empty:
            return pos

        if not receipts.empty:
            merged = pos.merge(
                receipts[["po_number", "po_item", "receipt_date",
                          "receipt_quantity", "quality_status", "defect_quantity"]],
                on=["po_number", "po_item"],
                how="left",
            )
        else:
            merged = pos.copy()
            merged["receipt_date"] = pd.NaT
            merged["receipt_quantity"] = 0
            merged["quality_status"] = "Pending"
            merged["defect_quantity"] = 0

        merged["actual_receipt_date"] = pd.to_datetime(merged.get("receipt_date"), errors="coerce")
        merged["requested_date"] = pd.to_datetime(merged["requested_date"], errors="coerce")

        merged["lead_time_days"] = (
            merged["actual_receipt_date"] - pd.to_datetime(merged.get("po_date", merged["requested_date"]), errors="coerce")
        ).dt.days

        merged["is_on_time"] = (
            merged["actual_receipt_date"] <= merged["requested_date"]
        ).astype(int).fillna(0).astype(int)

        merged["is_in_full"] = np.where(
            merged["order_quantity"] > 0,
            (merged["receipt_quantity"] >= merged["order_quantity"] * 0.98).astype(int),
            0,
        )
        merged["is_otif"] = (merged["is_on_time"] & merged["is_in_full"]).astype(int)

        logger.info(f"Transformed {len(merged):,} PO records with OTIF flags")
        return merged

    def _extract_and_transform_shipments(
        self, from_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Extract and enrich shipment data with timing metrics."""
        shipments = self.tms.extract_shipments(from_date=from_date)

        if shipments.empty:
            return shipments

        for col in ["planned_delivery", "actual_delivery", "planned_ship_date", "actual_ship_date"]:
            if col in shipments.columns:
                shipments[col] = pd.to_datetime(shipments[col], errors="coerce")

        shipments["is_on_time"] = (
            shipments["actual_delivery"] <= shipments["planned_delivery"]
        ).astype(int).fillna(0).astype(int)

        shipments["delay_hours"] = np.maximum(
            (shipments["actual_delivery"] - shipments["planned_delivery"]).dt.total_seconds() / 3600,
            0,
        ).fillna(0)

        if "actual_arrival" in shipments.columns and "putaway_complete_time" in shipments.columns:
            shipments["dwell_time_hours"] = (
                pd.to_datetime(shipments["putaway_complete_time"]) -
                pd.to_datetime(shipments["actual_arrival"])
            ).dt.total_seconds() / 3600
        elif "actual_delivery" in shipments.columns and "actual_ship_date" in shipments.columns:
            shipments["dwell_time_hours"] = 0.0

        shipments["total_cost"] = (
            shipments.get("freight_cost", 0) + shipments.get("accessorial_cost", 0)
        )

        logger.info(f"Transformed {len(shipments):,} shipment records")
        return shipments

    def _extract_and_transform_warehouse(self) -> pd.DataFrame:
        """Extract warehouse task data for operational metrics."""
        tasks = self.ewm.extract_warehouse_tasks()
        if tasks.empty:
            return tasks

        for col in ["created_time", "start_time", "complete_time"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], errors="coerce")

        tasks["task_duration_minutes"] = (
            (tasks["complete_time"] - tasks["start_time"]).dt.total_seconds() / 60
        ).fillna(0)

        logger.info(f"Transformed {len(tasks):,} warehouse tasks")
        return tasks

    def _build_dimensions(self, pos: pd.DataFrame, shipments: pd.DataFrame) -> dict:
        """Build dimension tables from extracted data."""
        dimensions = {}

        if not pos.empty and "supplier_id" in pos.columns:
            vendors = self.sap.extract_vendor_master()
            if not vendors.empty:
                dimensions["dim_supplier"] = vendors

        if not shipments.empty:
            carriers = self.tms.extract_carriers()
            if not carriers.empty:
                dimensions["dim_carrier"] = carriers

        return dimensions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/etl_config.yaml")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()

    orchestrator = ETLOrchestrator(config_path=args.config)
    if args.mode == "full":
        stats = orchestrator.run_full_load()
    else:
        stats = orchestrator.run_incremental()
    print(f"ETL {args.mode} load complete: {stats}")
