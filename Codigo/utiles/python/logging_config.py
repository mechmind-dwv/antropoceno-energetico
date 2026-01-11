"""
Configuración centralizada de logging
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_dir: Path = Path("logs"), level: str = "INFO", experiment: str = "general"
):
    """Configurar logging para el proyecto"""

    log_dir.mkdir(exist_ok=True)

    # Formato de log
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Logger root
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    # Handler para archivo
    log_file = log_dir / f"{experiment}_{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Añadir handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
