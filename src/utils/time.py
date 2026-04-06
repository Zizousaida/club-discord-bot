from __future__ import annotations

from datetime import UTC, datetime


def utcnow_iso() -> str:
    """
    Return the current UTC time in ISO 8601 format.

    Stored timestamps are always in UTC to avoid timezone issues.
    """
    return datetime.now(tz=UTC).isoformat()


def format_timestamp_for_display(iso_str: str) -> str:
    """
    Format an ISO 8601 timestamp string into a human-friendly form.

    Example output: 2025-01-01 12:34 UTC
    """
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
