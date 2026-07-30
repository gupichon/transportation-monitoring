from __future__ import annotations

from dataclasses import dataclass

from transportation_monitoring.data_explorer import yload
from transportation_monitoring.display_models import StopRouteSelection


@dataclass(frozen=True)
class DisplayConfig:
    selections: tuple[StopRouteSelection, ...]
    title: str = ""
    max_entries_per_stop: int = 3
    footer: str | None = None
    temperature_stale_after_seconds: int | None = None


def parse_display_config(raw_config: dict | None) -> DisplayConfig:
    raw_config = raw_config or {}
    raw_stops = raw_config.get("stops", [])
    selections = tuple(
        StopRouteSelection(
            monitoring_ref=stop["monitoring_ref"],
            stop_label=stop.get("label") or stop["monitoring_ref"],
            lines=tuple(str(line) for line in stop.get("lines", ())),
        )
        for stop in raw_stops
    )

    stale_after = raw_config.get("temperature_stale_after_seconds")
    return DisplayConfig(
        title=raw_config.get("title", ""),
        selections=selections,
        max_entries_per_stop=int(raw_config.get("max_entries_per_stop", 3)),
        footer=raw_config.get("footer"),
        temperature_stale_after_seconds=None if stale_after is None else int(stale_after),
    )


def load_display_config(filename: str) -> DisplayConfig:
    return parse_display_config(yload(filename))
