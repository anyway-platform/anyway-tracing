import os


def is_tracing_enabled() -> bool:
    return (os.getenv("ANYWAY_TRACING_ENABLED") or "true").lower() == "true"


def is_content_tracing_enabled() -> bool:
    return (os.getenv("ANYWAY_TRACE_CONTENT") or "true").lower() == "true"


def is_metrics_enabled() -> bool:
    return (os.getenv("ANYWAY_METRICS_ENABLED") or "true").lower() == "true"


def is_logging_enabled() -> bool:
    return (os.getenv("ANYWAY_LOGGING_ENABLED") or "false").lower() == "true"
