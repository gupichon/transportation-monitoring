from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def interval_for(now: datetime, schedule: list[dict]) -> int | None:
    current = now.timetz().replace(tzinfo=None)
    for period in schedule:
        if _parse_time(period["start"]) <= current < _parse_time(period["end"]):
            return int(period["interval_seconds"])
    return None


def next_run_after(now: datetime, schedule: list[dict], timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz)
    interval = interval_for(local_now, schedule)
    if interval is not None:
        timestamp = local_now.timestamp()
        next_timestamp = (int(timestamp) // interval + 1) * interval
        return datetime.fromtimestamp(next_timestamp, tz)

    candidates: list[datetime] = []
    for day_offset in (0, 1):
        day = local_now.date() + timedelta(days=day_offset)
        for period in schedule:
            candidate = datetime.combine(day, _parse_time(period["start"]), tz)
            if candidate > local_now:
                candidates.append(candidate)
    if not candidates:
        raise ValueError("schedule must contain at least one period")
    return min(candidates)


def daily_call_count(schedule: list[dict], stop_count: int) -> int:
    cycles = 0
    for period in schedule:
        start = datetime.combine(datetime.min.date(), _parse_time(period["start"]))
        end = datetime.combine(datetime.min.date(), _parse_time(period["end"]))
        seconds = int((end - start).total_seconds())
        interval = int(period["interval_seconds"])
        if seconds <= 0 or interval <= 0 or seconds % interval:
            raise ValueError("schedule periods must be positive multiples of their interval")
        cycles += seconds // interval
    return cycles * stop_count
