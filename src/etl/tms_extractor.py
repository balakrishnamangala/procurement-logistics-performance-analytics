"""TMS carrier and shipment data extractor via REST API."""
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

from src.utils import get_logger

logger = get_logger("tms_extractor")


class TMSExtractor:
    """Extracts shipment and carrier data from TMS via REST API.

    Pulls shipment records, tracking events, carrier performance
    data, and freight cost details for control tower analytics.
    """

    def __init__(self, config: dict):
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.endpoints = config.get("endpoints", {})

    def extract_shipments(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> pd.DataFrame:
        """Extract shipment records with cost and timing data.

        Includes planned vs actual dates, freight costs, weight/volume,
        and exception flags for OTIF and cost analysis.
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=90)
        if to_date is None:
            to_date = datetime.now()

        logger.info(f"Extracting shipments from {from_date:%Y-%m-%d} to {to_date:%Y-%m-%d}")

        params = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "page_size": 5000,
        }
        if status:
            params["status"] = status

        records = self._fetch_paginated(
            self.endpoints.get("shipments", "/api/v1/shipments"),
            params,
        )

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df = self._transform_shipment_dates(df)

        logger.info(f"Extracted {len(df):,} shipment records")
        return df

    def extract_carriers(self) -> pd.DataFrame:
        """Extract carrier master data with service attributes."""
        logger.info("Extracting carrier master data")

        records = self._fetch_paginated(
            self.endpoints.get("carriers", "/api/v1/carriers"),
            {"active": True},
        )

        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    def extract_tracking_events(
        self, shipment_ids: list[str]
    ) -> pd.DataFrame:
        """Extract tracking milestone events for given shipments."""
        logger.info(f"Extracting tracking events for {len(shipment_ids)} shipments")

        all_events = []
        for batch_start in range(0, len(shipment_ids), 100):
            batch = shipment_ids[batch_start:batch_start + 100]
            params = {"shipment_ids": ",".join(batch)}
            events = self._fetch_paginated(
                self.endpoints.get("tracking", "/api/v1/tracking"),
                params,
            )
            all_events.extend(events)

        if not all_events:
            return pd.DataFrame()

        return pd.DataFrame(all_events)

    def _fetch_paginated(self, endpoint: str, params: dict) -> list[dict]:
        """Fetch paginated results from TMS API with local fallback."""
        import os
        data_dir = os.path.join("data", "raw")

        # Map endpoint to filename
        endpoint_name = endpoint.rstrip("/").split("/")[-1]
        for ext in [".parquet", ".csv"]:
            filepath = os.path.join(data_dir, f"tms_{endpoint_name}{ext}")
            if os.path.exists(filepath):
                df = pd.read_parquet(filepath) if ext == ".parquet" else pd.read_csv(filepath)
                logger.info(f"Loaded {len(df):,} records from {filepath}")
                return df.to_dict("records")

        # Production: call TMS REST API
        # import requests
        # headers = {"Authorization": f"Bearer {self.api_key}"}
        # all_records = []
        # page = 1
        # while True:
        #     params["page"] = page
        #     resp = requests.get(f"{self.api_url}{endpoint}", headers=headers, params=params)
        #     resp.raise_for_status()
        #     data = resp.json()
        #     all_records.extend(data.get("results", []))
        #     if not data.get("has_more", False):
        #         break
        #     page += 1
        # return all_records

        logger.warning(f"No data available for {endpoint}")
        return []

    def _transform_shipment_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse and standardize date columns in shipment data."""
        date_cols = [
            "planned_ship_date", "actual_ship_date",
            "planned_delivery", "actual_delivery",
        ]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
