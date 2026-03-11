import logging
import logging.handlers
import os

from apps.api.app.core.config import settings

# Noisy third-party loggers that flood the console
_QUIET_LOGGERS = [
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "uvicorn.lifespan",
    "fastapi",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
    "passlib",
    "multipart",
    "httpx",
]


def configure_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.WARNING)

    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "workforce.log")

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Replace any existing handlers (avoids duplicate console output)
    root.handlers.clear()
    root.addHandler(file_handler)

    # Silence noisy libraries — ERROR only
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.ERROR)


configure_logging()
logger = logging.getLogger("workforce")
