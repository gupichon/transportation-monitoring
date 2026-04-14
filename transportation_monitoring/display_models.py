from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


MAGTAG_WIDTH = 296
MAGTAG_HEIGHT = 128


@dataclass(frozen=True)
class StopRouteSelection:
    monitoring_ref: str
    stop_label: str
    lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArrivalDisplayEntry:
    line: str
    destination: str
    wait_label: str
    status: str | None = None


@dataclass(frozen=True)
class LineDisplayRow:
    line: str
    wait_labels: tuple[str, ...]


@dataclass(frozen=True)
class StopDisplaySection:
    title: str
    monitoring_ref: str
    entries: tuple[ArrivalDisplayEntry, ...]
    line_rows: tuple[LineDisplayRow, ...] = ()
    empty_message: str = "Aucun passage"


@dataclass(frozen=True)
class TransitDisplayState:
    generated_at: datetime | None
    sections: tuple[StopDisplaySection, ...]
    title: str = ""
    footer: str | None = None
    width: int = MAGTAG_WIDTH
    height: int = MAGTAG_HEIGHT


def _wait_label(waiting_time: timedelta | None) -> str:
    if waiting_time is None:
        return "--"

    total_seconds = int(waiting_time.total_seconds())
    if total_seconds <= 0:
        return "Approche"
    if total_seconds < 60:
        return "1 min"

    minutes = total_seconds // 60
    return f"{minutes} min"


def build_display_state(
    passages: Iterable[dict],
    selections: Iterable[StopRouteSelection],
    title: str = "",
    generated_at: datetime | None = None,
    max_entries_per_stop: int = 3,
    footer: str | None = None,
) -> TransitDisplayState:
    sections: list[StopDisplaySection] = []
    passages_by_stop: dict[str, list[dict]] = {}

    for passage in passages:
        monitoring_ref = passage.get("monitoring_ref")
        if monitoring_ref is None:
            continue
        passages_by_stop.setdefault(monitoring_ref, []).append(passage)

    for selection in selections:
        matching = list(passages_by_stop.get(selection.monitoring_ref, ()))
        if selection.lines:
            allowed = set(selection.lines)
            matching = [passage for passage in matching if passage.get("line") in allowed]

        matching.sort(
            key=lambda passage: (
                passage.get("waiting_time") is None,
                passage.get("waiting_time"),
            )
        )

        entries = tuple(
            ArrivalDisplayEntry(
                line=str(passage.get("line", "?")),
                destination=str(passage.get("destination") or passage.get("direction") or "?"),
                wait_label=_wait_label(passage.get("waiting_time")),
                status=passage.get("status"),
            )
            for passage in matching[:max_entries_per_stop]
        )

        grouped_waits: dict[str, list[str]] = {}
        for entry in entries:
            grouped_waits.setdefault(entry.line, []).append(entry.wait_label)

        line_rows = tuple(
            LineDisplayRow(line=line, wait_labels=tuple(wait_labels[:3]))
            for line, wait_labels in grouped_waits.items()
        )

        sections.append(
            StopDisplaySection(
                title=selection.stop_label,
                monitoring_ref=selection.monitoring_ref,
                entries=entries,
                line_rows=line_rows,
            )
        )

    return TransitDisplayState(
        title=title,
        generated_at=generated_at,
        sections=tuple(sections),
        footer=footer,
    )


def compact_entries_label(entries: tuple[ArrivalDisplayEntry, ...]) -> str:
    if not entries:
        return "Aucun passage"

    return " | ".join(f"{entry.line} {entry.wait_label}" for entry in entries[:3])


def compact_line_rows(line_rows: tuple[LineDisplayRow, ...]) -> tuple[str, ...]:
    if not line_rows:
        return ("Aucun passage",)

    return tuple(
        f"{line_row.line}  {' | '.join(line_row.wait_labels)}"
        for line_row in line_rows
    )
