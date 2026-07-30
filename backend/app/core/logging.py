import logging
import sys
from pathlib import Path
from backend.app.core.config import settings


def setup_logger() -> logging.Logger:
    """Configure application logging for file and console output."""
    log_dir = settings.get_log_dir()
    log_file = log_dir / "app.log"

    logger = logging.getLogger("smart_classroom")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
