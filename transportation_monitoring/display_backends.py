from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from transportation_monitoring.display_models import TransitDisplayState


@dataclass(frozen=True)
class DisplayRegion:
    name: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class DisplayUpdatePlan:
    full_refresh: bool
    regions: tuple[DisplayRegion, ...]
    reason: str


class DisplayBackend(Protocol):
    def update(self, state: TransitDisplayState) -> DisplayUpdatePlan:
        """Apply a new state to the display backend."""


def _section_signature(section) -> tuple:
    return (
        section.title,
        tuple((entry.line, entry.destination, entry.wait_label, entry.status) for entry in section.entries),
        section.empty_message,
    )


def build_update_plan(
    previous: TransitDisplayState | None,
    current: TransitDisplayState,
) -> DisplayUpdatePlan:
    if previous is None:
        return DisplayUpdatePlan(
            full_refresh=True,
            regions=(DisplayRegion("screen", 0, 0, current.width, current.height),),
            reason="initial render",
        )

    if (previous.width, previous.height) != (current.width, current.height):
        return DisplayUpdatePlan(
            full_refresh=True,
            regions=(DisplayRegion("screen", 0, 0, current.width, current.height),),
            reason="display geometry changed",
        )

    if len(previous.sections) != len(current.sections):
        return DisplayUpdatePlan(
            full_refresh=True,
            regions=(DisplayRegion("screen", 0, 0, current.width, current.height),),
            reason="section count changed",
        )

    regions: list[DisplayRegion] = []
    header_changed = (
        previous.title != current.title
        or previous.generated_at != current.generated_at
        or previous.footer != current.footer
    )
    if header_changed:
        regions.append(DisplayRegion("header", 0, 0, current.width, 24))

    footer_height = 14 if current.footer else 0
    header_height = 24
    body_top = header_height + 4
    body_height = current.height - body_top - footer_height - 4
    section_height = body_height // max(1, len(current.sections))

    for index, section in enumerate(current.sections):
        previous_section = previous.sections[index]
        if _section_signature(previous_section) == _section_signature(section):
            continue

        top = body_top + index * section_height
        regions.append(
            DisplayRegion(
                name=f"section_{index}",
                x=6,
                y=top,
                width=current.width - 12,
                height=section_height - 2,
            )
        )

    if previous.footer != current.footer and current.footer:
        regions.append(DisplayRegion("footer", 0, current.height - 14, current.width, 14))

    return DisplayUpdatePlan(
        full_refresh=False,
        regions=tuple(regions),
        reason="diff update" if regions else "no visual changes",
    )


class CircuitPythonMagTagDisplay:
    """
    Backend placeholder for the real MagTag implementation.

    The intended strategy is:
    - keep static widgets mounted once
    - update only changed text/areas on each state transition
    - schedule a periodic full refresh to reduce e-ink ghosting
    """

    def __init__(self, full_refresh_every: int = 30) -> None:
        self.previous_state: TransitDisplayState | None = None
        self.full_refresh_every = full_refresh_every
        self.update_count = 0

    def update(self, state: TransitDisplayState) -> DisplayUpdatePlan:
        plan = build_update_plan(self.previous_state, state)
        self.update_count += 1

        if not plan.full_refresh and self.update_count >= self.full_refresh_every:
            plan = DisplayUpdatePlan(
                full_refresh=True,
                regions=(DisplayRegion("screen", 0, 0, state.width, state.height),),
                reason="periodic e-ink cleanup refresh",
            )
            self.update_count = 0

        self.previous_state = state
        return plan
