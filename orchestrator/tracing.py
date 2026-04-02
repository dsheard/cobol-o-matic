"""Optional OpenTelemetry tracing for the COBOL reverse-engineering tool.

Creates distributed traces with spans for each phase, program batch,
subagent, and tool call.  Gracefully degrades to a no-op when OTEL
dependencies are not installed or no endpoint is configured.

Configuration (config.yaml):
    settings:
      otel_endpoint: http://localhost:4318   # OTLP HTTP endpoint
      otel_service_name: cobol-reverse-engineer

Or via environment:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

_tracer = None
_log_dir: Path | None = None


# ---------------------------------------------------------------------------
# JSONL event log (always available, even without OTEL)
# ---------------------------------------------------------------------------

_jsonl_file = None


def _ensure_jsonl(workspace: Path) -> None:
    global _jsonl_file, _log_dir
    _log_dir = workspace / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    if _jsonl_file is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = _log_dir / f"run-{ts}.jsonl"
        _jsonl_file = open(path, "a", encoding="utf-8")
        logger.info("Agent event log: %s", path)


def log_event(event_type: str, **attrs: Any) -> None:
    """Write a structured event to the JSONL log."""
    if _jsonl_file is None:
        return
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **{k: v for k, v in attrs.items() if v is not None},
    }
    _jsonl_file.write(json.dumps(record) + "\n")
    _jsonl_file.flush()


def close_event_log() -> None:
    global _jsonl_file
    if _jsonl_file is not None:
        _jsonl_file.close()
        _jsonl_file = None


# ---------------------------------------------------------------------------
# Transcript capture (copies SDK transcript paths to workspace/logs/)
# ---------------------------------------------------------------------------

def capture_transcript(transcript_path: str, label: str) -> None:
    """Copy an agent transcript file into workspace/logs/ for debugging."""
    if _log_dir is None or not transcript_path:
        return
    src = Path(transcript_path)
    if not src.is_file():
        return
    dest = _log_dir / f"transcript-{label}-{src.name}"
    try:
        import shutil
        shutil.copy2(src, dest)
        logger.debug("Captured transcript: %s -> %s", src, dest)
        log_event("transcript_captured", label=label, source=str(src), dest=str(dest))
    except OSError as e:
        logger.warning("Failed to capture transcript %s: %s", src, e)


# ---------------------------------------------------------------------------
# Session-based transcript capture
# ---------------------------------------------------------------------------

_sdk_transcript_dir: Path | None = None


def _normalise_project_name(path: str) -> str:
    """Normalise a path the same way the Claude SDK does for project dirs."""
    import re
    return re.sub(r"[^a-zA-Z0-9]", "-", path).strip("-").lower()


def _find_sdk_transcript_dir(cwd: str) -> Path | None:
    """Locate the SDK transcript directory for the given workspace."""
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.is_dir():
        return None
    norm = _normalise_project_name(cwd)
    for d in sorted(claude_dir.iterdir(), key=lambda p: len(p.name), reverse=True):
        if d.is_dir() and _normalise_project_name(d.name) == norm:
            return d
    for d in claude_dir.iterdir():
        if d.is_dir() and norm in _normalise_project_name(d.name):
            return d
    return None


def init_transcript_dir(cwd: str) -> None:
    """Find and cache the SDK transcript directory for this workspace."""
    global _sdk_transcript_dir
    _sdk_transcript_dir = _find_sdk_transcript_dir(cwd)
    if _sdk_transcript_dir:
        logger.debug("SDK transcript dir: %s", _sdk_transcript_dir)
    else:
        logger.debug("SDK transcript dir not found for cwd=%s", cwd)


def capture_session_transcript(session_id: str, label: str) -> None:
    """Copy the SDK transcript for a given session_id into workspace/logs/."""
    if not session_id or not _sdk_transcript_dir or _log_dir is None:
        return
    src = _sdk_transcript_dir / f"{session_id}.jsonl"
    if not src.is_file():
        logger.debug("Transcript not found: %s", src)
        return
    capture_transcript(str(src), label)


# ---------------------------------------------------------------------------
# OTEL initialisation
# ---------------------------------------------------------------------------

def init_tracing(workspace: Path, config: dict) -> None:
    """Initialise OTEL tracing and the JSONL event log.

    Falls back to JSONL-only if OTEL dependencies are not installed.
    """
    global _tracer

    _ensure_jsonl(workspace)

    settings = config.get("settings", {})
    endpoint = (
        settings.get("otel_endpoint")
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    )
    service_name = (
        settings.get("otel_service_name")
        or os.environ.get("OTEL_SERVICE_NAME")
        or "cobol-reverse-engineer"
    )

    if not endpoint:
        logger.debug("No OTEL endpoint configured — JSONL-only logging")
        log_event("tracing_init", mode="jsonl_only")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except ImportError:
        logger.warning(
            "OTEL endpoint configured (%s) but opentelemetry packages not installed. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-http",
            endpoint,
        )
        log_event("tracing_init", mode="jsonl_only", reason="otel_not_installed")
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("cobol-reverse-engineer")

    logger.info("OTEL tracing enabled: endpoint=%s, service=%s", endpoint, service_name)
    log_event("tracing_init", mode="otel", endpoint=endpoint, service_name=service_name)


def shutdown_tracing() -> None:
    """Flush pending spans and close the event log."""
    global _tracer
    if _tracer is not None:
        try:
            from opentelemetry import trace
            provider = trace.get_tracer_provider()
            if hasattr(provider, "shutdown"):
                provider.shutdown()
        except Exception as e:
            logger.warning("OTEL shutdown error: %s", e)
        _tracer = None
    close_event_log()


# ---------------------------------------------------------------------------
# Span helpers (no-op when OTEL is not initialised)
# ---------------------------------------------------------------------------

@contextmanager
def span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    """Create a traced span.  Yields the span (or None if OTEL is off)."""
    log_event("span_start", span=name, **(attributes or {}))
    start = time.monotonic()

    if _tracer is not None:
        with _tracer.start_as_current_span(name, attributes=attributes or {}) as s:
            try:
                yield s
            except Exception as e:
                s.set_status(trace_status_error(str(e)))
                s.record_exception(e)
                log_event("span_error", span=name, error=str(e))
                raise
            finally:
                elapsed = time.monotonic() - start
                log_event("span_end", span=name, elapsed_s=round(elapsed, 2))
    else:
        try:
            yield None
        except Exception:
            log_event("span_error", span=name, error="exception")
            raise
        finally:
            elapsed = time.monotonic() - start
            log_event("span_end", span=name, elapsed_s=round(elapsed, 2))


def set_span_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span (no-op without OTEL)."""
    if _tracer is not None:
        try:
            from opentelemetry import trace
            current = trace.get_current_span()
            if current:
                current.set_attribute(key, value)
        except Exception:
            pass


def trace_status_error(description: str) -> Any:
    """Create an OTEL error status."""
    try:
        from opentelemetry.trace import StatusCode, Status
        return Status(StatusCode.ERROR, description)
    except ImportError:
        return None
