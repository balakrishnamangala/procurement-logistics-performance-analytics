"""Centralized logging configuration."""
import sys
from loguru import logger


def get_logger(name: str, level: str = "INFO"):
    """Return a named logger with file and stderr sinks."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level=level,
        filter=lambda record: record["extra"].get("name", "") == name,
    )
    logger.add(
        f"logs/{name}.log",
        rotation="10 MB",
        retention="30 days",
        level=level,
        filter=lambda record: record["extra"].get("name", "") == name,
    )
    return logger.bind(name=name)
