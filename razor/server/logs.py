from logging import Logger, getLogger
from typing import Final

from uvicorn.config import LOGGING_CONFIG

LOGGING_CONFIG["loggers"]["uvicorn.access"]["level"] = "INFO"
LOGGING_CONFIG["loggers"]["uvicorn.error"]["level"] = "WARNING"

logger: Final[Logger] = getLogger("uvicorn")
