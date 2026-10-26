import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "event": record.getMessage(),
                "request_id": getattr(record, "request_id", None),
                "status": getattr(record, "status", None),
                "duration_ms": getattr(record, "duration_ms", None),
            }
        )


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("quickbuddy")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
