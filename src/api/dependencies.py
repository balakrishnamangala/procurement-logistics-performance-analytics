"""FastAPI dependency injection for data services."""
from functools import lru_cache
from src.dashboard.data_service import DashboardDataService


@lru_cache()
def get_data_service() -> DashboardDataService:
    """Singleton data service instance for API endpoints."""
    return DashboardDataService()
