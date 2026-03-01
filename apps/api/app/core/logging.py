"""
Logging profesional — stdlib only, cero dependencias externas.

Uso:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Mission created", extra={"mission_id": str(mid)})
"""

import logging
import sys


_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """
    Configura el logging global una sola vez.
    Llamado desde el lifespan de FastAPI al arrancar.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    # Evita handlers duplicados si se llama más de una vez
    root.handlers.clear()
    root.addHandler(handler)

    # Silencia logs ruidosos de terceros
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if numeric_level <= logging.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Retorna un logger con el nombre del módulo."""
    return logging.getLogger(name)
