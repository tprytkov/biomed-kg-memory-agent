import logging

from src.app.utils.config import get_settings


def build_logger(name: str = "biomed_kg_memory_agent") -> logging.Logger:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


logger = build_logger()
