"""Observability: Prometheus metrics + structured JSON logs + request IDs."""
import json
import logging
import sys
import time
import uuid

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency (s)", ["method", "path"],
                    buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5))
ERRORS = Counter("app_unhandled_errors_total", "Unhandled exceptions")
TOP_SCORE = Histogram("retrieval_top_score", "Top-1 cosine score per search",
                      buckets=(.0, .05, .1, .2, .3, .4, .5, .75, 1.0))
LOW_CONF = Counter("retrieval_low_confidence_total",
                   "Searches whose top-1 score fell below the confidence threshold")
LOW_CONF_THRESHOLD = 0.10


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"), "level": record.levelname,
                   "msg": record.getMessage()}
        payload.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger() -> logging.Logger:
    log = logging.getLogger("finrisk")
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        log.addHandler(h)
        log.setLevel(logging.INFO)
        log.propagate = False
    return log


log = get_logger()


async def observe(request, call_next):
    start = time.perf_counter()
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        ERRORS.inc()
        log.exception("unhandled error", extra={"extra_fields": {"request_id": rid}})
        raise
    finally:
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        path = route.path if route else "unmatched"
        REQUESTS.labels(request.method, path, str(status)).inc()
        LATENCY.labels(request.method, path).observe(elapsed)
        log.info("request", extra={"extra_fields": {
            "request_id": rid, "method": request.method, "path": path,
            "status": status, "latency_ms": round(elapsed * 1000, 2)}})
    response.headers["x-request-id"] = rid
    return response


def record_search(top_score: float | None) -> None:
    s = top_score or 0.0
    TOP_SCORE.observe(s)
    if s < LOW_CONF_THRESHOLD:
        LOW_CONF.inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
