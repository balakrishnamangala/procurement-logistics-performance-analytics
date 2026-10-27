"""SAP S/4HANA data extractor for purchase order and vendor data."""
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

from src.utils import get_logger, load_config

logger = get_logger("sap_extractor")


class SAPExtractor:
    """Extracts purchase order and vendor master data from SAP S/4HANA.

    Connects to SAP tables (EKKO, EKPO, MKPF, LFA1) to pull
    PO headers, line items, goods receipts, and vendor information.
    """

    def __init__(self, config: dict):
        self.config = config
        self.host = config.get("host", "")
        self.client = config.get("client", "100")
        self.tables = config.get("tables", {})

    def extract_purchase_orders(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Extract purchase order headers and items.

        Joins EKKO (PO header) with EKPO (PO items) to create
        a denormalized PO dataset with quantities and values.
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=180)
        if to_date is None:
            to_date = datetime.now()

        logger.info(f"Extracting POs from {from_date:%Y-%m-%d} to {to_date:%Y-%m-%d}")

        query = f"""
        SELECT
            h.EBELN AS po_number,
            i.EBELP AS po_item,
            h.AEDAT AS po_date,
            h.LIFNR AS supplier_id,
            i.WERKS AS plant,
            i.MATNR AS material_number,
            i.TXZ01 AS material_desc,
            i.MENGE AS order_quantity,
            i.MEINS AS unit_of_measure,
            i.NETPR AS unit_price,
            i.NETWR AS total_value,
            h.WAERS AS currency,
            i.EINDT AS requested_date,
            i.BEDAT AS confirmed_date,
            h.STATU AS po_status
        FROM {self.tables['purchase_orders']} h
        INNER JOIN {self.tables['po_items']} i
            ON h.EBELN = i.EBELN
        WHERE h.AEDAT BETWEEN :from_date AND :to_date
            AND h.BSTYP = 'F'
            AND h.LOEKZ = ''
        ORDER BY h.AEDAT DESC
        """

        logger.info(f"SAP PO query prepared for tables {self.tables['purchase_orders']}, {self.tables['po_items']}")
        return self._execute_query(query, {"from_date": from_date, "to_date": to_date})

    def extract_goods_receipts(
        self,
        from_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Extract goods receipt data from MKPF/MSEG.

        Captures actual receipt dates, quantities, and quality
        inspection results for OTIF calculation.
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=180)

        logger.info(f"Extracting goods receipts from {from_date:%Y-%m-%d}")

        query = f"""
        SELECT
            m.EBELN AS po_number,
            m.EBELP AS po_item,
            h.BUDAT AS receipt_date,
            m.MENGE AS receipt_quantity,
            m.MEINS AS unit_of_measure,
            m.WERKS AS plant,
            m.LGORT AS storage_location,
            h.BWART AS movement_type,
            CASE WHEN q.STAT = 'A' THEN 'Accepted'
                 WHEN q.STAT = 'R' THEN 'Rejected'
                 ELSE 'Pending' END AS quality_status,
            COALESCE(q.DEFECT_QTY, 0) AS defect_quantity
        FROM {self.tables['goods_receipt']} h
        INNER JOIN MSEG m ON h.MBLNR = m.MBLNR AND h.MJAHR = m.MJAHR
        LEFT JOIN QALS q ON m.EBELN = q.EBELN AND m.EBELP = q.EBELP
        WHERE h.BUDAT >= :from_date
            AND m.BWART IN ('101', '103')
        """

        return self._execute_query(query, {"from_date": from_date})

    def extract_vendor_master(self) -> pd.DataFrame:
        """Extract vendor master data from LFA1."""
        logger.info("Extracting vendor master data")

        query = f"""
        SELECT
            LIFNR AS supplier_id,
            NAME1 AS supplier_name,
            LAND1 AS country,
            REGIO AS region,
            KTOKK AS account_group,
            ZTERM AS payment_terms,
            ERDAT AS created_date
        FROM {self.tables['vendor_master']}
        WHERE LOEVM = ''
        """

        return self._execute_query(query, {})

    def _execute_query(self, query: str, params: dict) -> pd.DataFrame:
        """Execute query against SAP connection.

        In production, this connects via PyRFC or ODBC to SAP.
        For development, reads from local parquet/CSV files.
        """
        try:
            # Production: use SAP RFC or database connection
            # from pyrfc import Connection
            # conn = Connection(ashost=self.host, sysnr='00', client=self.client, ...)
            # result = conn.call('RFC_READ_TABLE', ...)

            # Development fallback: read from local files
            import os
            data_dir = os.path.join("data", "raw")
            table_name = query.split("FROM")[1].split()[0].strip() if "FROM" in query else "unknown"

            local_file = os.path.join(data_dir, f"sap_{table_name.lower()}.parquet")
            if os.path.exists(local_file):
                df = pd.read_parquet(local_file)
                logger.info(f"Loaded {len(df):,} records from {local_file}")
                return df

            csv_file = os.path.join(data_dir, f"sap_{table_name.lower()}.csv")
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                logger.info(f"Loaded {len(df):,} records from {csv_file}")
                return df

            logger.warning(f"No local data found for {table_name}, returning empty DataFrame")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"SAP extraction failed: {e}")
            raise
