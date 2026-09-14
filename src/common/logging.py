# Structured Observability Logger

import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "props") and isinstance(record.props, dict):
            payload.update(record.props)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logger(name: str = "docintel", level: str = "INFO", as_json: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if as_json:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        logger.addHandler(handler)
    return logger


logger = setup_logger()


@contextmanager
def log_stage(stage_name: str, document_id: Optional[str] = None, **kwargs: Any) -> Generator[Dict[str, Any], None, None]:
    start = time.perf_counter()
    ctx: Dict[str, Any] = {"stage": stage_name, "document_id": document_id, **kwargs}
    logger.info(f"Starting stage: {stage_name}", extra={"props": ctx})
    try:
        yield ctx
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        ctx["duration_ms"] = duration_ms
        ctx["status"] = "SUCCESS"
        logger.info(f"Completed stage: {stage_name} in {duration_ms}ms", extra={"props": ctx})
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        ctx["duration_ms"] = duration_ms
        ctx["status"] = "ERROR"
        ctx["error"] = str(exc)
        logger.error(f"Failed stage: {stage_name} after {duration_ms}ms: {exc}", extra={"props": ctx})
        raise
