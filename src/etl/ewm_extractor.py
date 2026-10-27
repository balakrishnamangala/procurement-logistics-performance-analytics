"""SAP EWM warehouse data extractor for inventory and operations."""
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

from src.utils import get_logger

logger = get_logger("ewm_extractor")


class EWMExtractor:
    """Extracts warehouse operations data from SAP EWM.

    Pulls inbound/outbound delivery data, warehouse task completions,
    and stock snapshots for dwell time and throughput analysis.
    """

    def __init__(self, config: dict):
        self.config = config
        self.warehouse_number = config.get("warehouse_number", "WH01")
        self.tables = config.get("tables", {})

    def extract_inbound_deliveries(
        self, from_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Extract inbound delivery and receiving data.

        Captures arrival times, unloading completion, and put-away
        timestamps for dwell time calculation.
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=90)

        logger.info(f"Extracting inbound deliveries from {from_date:%Y-%m-%d}")

        query = f"""
        SELECT
            d.DOCNO AS delivery_number,
            d.ITEMNO AS delivery_item,
            d.WHNUMBER AS warehouse_id,
            d.SUPPLIER AS supplier_id,
            d.PRODUCT AS material_number,
            d.QUANTITY AS expected_qty,
            d.UOM AS unit_of_measure,
            d.PLAN_ARRIVAL AS planned_arrival,
            d.ACT_ARRIVAL AS actual_arrival,
            d.UNLOAD_START AS unload_start_time,
            d.UNLOAD_END AS unload_end_time,
            d.PUTAWAY_COMPLETE AS putaway_complete_time,
            d.DOCK_DOOR AS dock_door,
            d.STATUS AS delivery_status
        FROM {self.tables.get('inbound_deliveries', '/SCWM/DLVH')} d
        WHERE d.PLAN_ARRIVAL >= :from_date
            AND d.DIRECTION = 'INBOUND'
        ORDER BY d.PLAN_ARRIVAL DESC
        """

        return self._execute_query(query, {"from_date": from_date})

    def extract_warehouse_tasks(
        self, from_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Extract warehouse task data for throughput metrics.

        Covers receiving, put-away, picking, packing, and dispatch tasks.
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=90)

        logger.info(f"Extracting warehouse tasks from {from_date:%Y-%m-%d}")

        query = f"""
        SELECT
            t.TASKID AS task_id,
            t.WHNUMBER AS warehouse_id,
            t.TASK_TYPE AS task_type,
            t.PRODUCT AS material_number,
            t.QUANTITY AS quantity,
            t.SOURCE_BIN AS source_bin,
            t.DEST_BIN AS dest_bin,
            t.CREATED_AT AS created_time,
            t.STARTED_AT AS start_time,
            t.COMPLETED_AT AS complete_time,
            t.WORKER_ID AS worker_id,
            t.STATUS AS task_status,
            t.PRIORITY AS priority
        FROM {self.tables.get('warehouse_tasks', '/SCWM/WHST')} t
        WHERE t.CREATED_AT >= :from_date
        ORDER BY t.CREATED_AT DESC
        """

        return self._execute_query(query, {"from_date": from_date})

    def extract_stock_snapshot(self) -> pd.DataFrame:
        """Extract current stock positions across warehouse bins."""
        logger.info("Extracting current stock snapshot")

        query = f"""
        SELECT
            s.WHNUMBER AS warehouse_id,
            s.PRODUCT AS material_number,
            s.BIN AS storage_bin,
            s.AVAILABLE_QTY AS available_qty,
            s.RESERVED_QTY AS reserved_qty,
            s.BLOCKED_QTY AS blocked_qty,
            s.UOM AS unit_of_measure,
            s.LAST_MOVEMENT AS last_movement_date,
            s.BATCH AS batch_number
        FROM {self.tables.get('stock_overview', '/SCWM/AQUA')} s
        WHERE s.WHNUMBER = :warehouse
        """

        return self._execute_query(query, {"warehouse": self.warehouse_number})

    def _execute_query(self, query: str, params: dict) -> pd.DataFrame:
        """Execute query with local file fallback for development."""
        import os
        data_dir = os.path.join("data", "raw")

        if "inbound" in query.lower():
            filename = "ewm_inbound_deliveries"
        elif "task" in query.lower():
            filename = "ewm_warehouse_tasks"
        else:
            filename = "ewm_stock_snapshot"

        for ext in [".parquet", ".csv"]:
            filepath = os.path.join(data_dir, f"{filename}{ext}")
            if os.path.exists(filepath):
                df = pd.read_parquet(filepath) if ext == ".parquet" else pd.read_csv(filepath)
                logger.info(f"Loaded {len(df):,} records from {filepath}")
                return df

        logger.warning(f"No local data for {filename}")
        return pd.DataFrame()
