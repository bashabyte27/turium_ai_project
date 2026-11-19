import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Prints each log line as one JSON object so it is easy to search and parse."""

    def format(self, record):
        line = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        line.update(getattr(record, "fields", {}))
        if record.exc_info:
            line["exception"] = self.formatException(record.exc_info)
        return json.dumps(line)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def log(event, level=logging.INFO, **fields):
    """log("ingest_done", item_id="abc", chunks=3)"""
    logging.getLogger("inbox").log(level, event, extra={"fields": fields})
