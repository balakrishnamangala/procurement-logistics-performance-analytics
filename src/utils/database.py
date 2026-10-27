"""Database connection manager for the logistics data warehouse."""
from contextlib import contextmanager
from typing import Optional, Generator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.utils.logger import get_logger

logger = get_logger("database")


class DatabaseManager:
    """Manages connections to the logistics star schema database."""

    def __init__(self, connection_string: str, schema: str = "logistics_dw"):
        self.connection_string = connection_string
        self.schema = schema
        self._engine: Optional[Engine] = None
        self._session_factory = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False,
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info("Database engine created")
        return self._engine

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional session scope."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame."""
        with self.engine.connect() as conn:
            result = pd.read_sql(text(query), conn, params=params)
        return result

    def bulk_insert(self, df: pd.DataFrame, table_name: str, if_exists: str = "append") -> int:
        """Bulk insert DataFrame into target table."""
        rows = df.to_sql(
            table_name,
            self.engine,
            schema=self.schema,
            if_exists=if_exists,
            index=False,
            chunksize=5000,
            method="multi",
        )
        logger.info(f"Inserted {len(df):,} rows into {self.schema}.{table_name}")
        return len(df)

    def truncate_table(self, table_name: str) -> None:
        """Truncate a target table before full reload."""
        with self.engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {self.schema}.{table_name}"))
            conn.commit()
        logger.info(f"Truncated {self.schema}.{table_name}")

    def close(self) -> None:
        """Dispose of the engine connection pool."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connection closed")
