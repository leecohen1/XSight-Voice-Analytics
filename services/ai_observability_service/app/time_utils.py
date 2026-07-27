"""UTC period-boundary helpers.

All aggregation periods are computed in UTC, using half-open intervals
[start, end) — a boundary timestamp belongs to the period it starts, never
to the one it ends. "Today" and "month" are always UTC-calendar days/months,
never the server's local timezone, so a deployment in any timezone produces
identical bucketing.

Every timestamp this module produces uses the same fixed-precision format
`validation.py` normalizes stored events to (whole seconds, `+00:00`
suffix) — required for safe lexicographic comparison against stored
`occurred_at` strings in SQL (see validation.py's comment on this).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

_FMT_NOTE = "whole-second precision, +00:00 suffix, matching stored occurred_at format"


def format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def today_bounds(now: Optional[datetime] = None) -> tuple[str, str]:
    """[start of today UTC, start of tomorrow UTC)."""
    now = now or datetime.now(timezone.utc)
    start = now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return format_utc(start), format_utc(end)


def month_bounds(now: Optional[datetime] = None) -> tuple[str, str]:
    """[start of this UTC month, start of next UTC month)."""
    now = now or datetime.now(timezone.utc)
    start = now.astimezone(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return format_utc(start), format_utc(end)


def resolve_period(
    range_: Optional[str], from_: Optional[str], to_: Optional[str]
) -> tuple[str, str]:
    """Resolves the query params of any `/usage/*` endpoint into a concrete
    [period_start, period_end) pair. Explicit `from`/`to` always win over
    `range` when both are given. Defaults to the current UTC month."""
    if from_ and to_:
        return format_utc(parse_utc(from_)), format_utc(parse_utc(to_))
    if range_ == "today":
        return today_bounds()
    if range_ == "month":
        return month_bounds()
    return month_bounds()


def days_in_month(period_start: str) -> int:
    start = parse_utc(period_start)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return (next_month - start).days
