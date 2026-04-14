from dataclasses import dataclass
from typing import Protocol

from transportation_monitoring.display_backends import DisplayUpdatePlan, build_update_plan
from transportation_monitoring.display_models import TransitDisplayState, compact_line_rows


class CircuitPythonView(Protocol):
    def apply_state(self, state: TransitDisplayState, plan: DisplayUpdatePlan) -> None:
        """Apply the current display state to the underlying UI toolkit."""


@dataclass
class TextCell:
    text: str = ""


class InMemoryCircuitPythonView:
    """
    Lightweight stand-in for a displayio-based view.

    It mirrors the text cells a real CircuitPython backend would manage, which
    makes it useful in tests and during backend development on desktop Python.
    """

    def __init__(self, max_sections: int = 4, max_rows_per_section: int = 3) -> None:
        self.title = TextCell()
        self.clock = TextCell()
        self.footer = TextCell()
        self.section_titles = [TextCell() for _ in range(max_sections)]
        self.section_lines = [[TextCell() for _ in range(max_rows_per_section)] for _ in range(max_sections)]
        self.last_plan: DisplayUpdatePlan | None = None

    def apply_state(self, state: TransitDisplayState, plan: DisplayUpdatePlan) -> None:
        self.title.text = state.title
        self.clock.text = "" if state.generated_at is None else f"Maj {state.generated_at.strftime('%H:%M')}"
        self.footer.text = state.footer or ""

        for section_index, section in enumerate(state.sections):
            if section_index >= len(self.section_titles):
                break
            self.section_titles[section_index].text = section.title
            row_texts = compact_line_rows(section.line_rows)
            for row_index, cell in enumerate(self.section_lines[section_index]):
                cell.text = row_texts[row_index] if row_index < len(row_texts) else ""

        self.last_plan = plan


class CircuitPythonMagTagBackend:
    def __init__(self, view: CircuitPythonView, full_refresh_every: int = 30) -> None:
        self.view = view
        self.previous_state: TransitDisplayState | None = None
        self.full_refresh_every = full_refresh_every
        self.partial_update_count = 0

    def apply_state(self, state: TransitDisplayState) -> DisplayUpdatePlan:
        plan = build_update_plan(self.previous_state, state)
        if plan.full_refresh:
            self.partial_update_count = 0
        else:
            self.partial_update_count += 1
            if self.partial_update_count >= self.full_refresh_every:
                plan = DisplayUpdatePlan(
                    full_refresh=True,
                    regions=plan.regions,
                    reason="periodic e-ink cleanup refresh",
                )
                self.partial_update_count = 0

        self.view.apply_state(state, plan)
        self.previous_state = state
        return plan


class DisplayioMagTagView:
    def __init__(self, display, max_sections: int = 2, max_rows_per_section: int = 3) -> None:
        import displayio
        import terminalio
        from adafruit_display_text import label

        self.display = display
        self.max_sections = max_sections
        self.max_rows_per_section = max_rows_per_section
        self.root_group = displayio.Group()
        self.display.root_group = self.root_group

        self._label_module = label
        self._font = terminalio.FONT

        self.title_label = label.Label(self._font, text="", color=0x111111, x=10, y=8)
        self.clock_label = label.Label(self._font, text="", color=0x222222, x=220, y=8)

        self.root_group.append(self.title_label)
        self.root_group.append(self.clock_label)

        self.section_titles = []
        self.section_line_labels = []

        body_top = 28
        section_height = 44
        for section_index in range(max_sections):
            top = body_top + section_index * section_height
            title = label.Label(self._font, text="", color=0x111111, x=14, y=top)
            self.section_titles.append(title)
            self.root_group.append(title)

            section_rows = []
            for row_index in range(max_rows_per_section):
                section_line = label.Label(self._font, text="", color=0x222222, x=14, y=top + 12 + row_index * 10)
                section_rows.append(section_line)
                self.root_group.append(section_line)
            self.section_line_labels.append(section_rows)

    def apply_state(self, state: TransitDisplayState, plan: DisplayUpdatePlan) -> None:
        self.title_label.text = state.title
        self.clock_label.text = "" if state.generated_at is None else f"Maj {state.generated_at.strftime('%H:%M')}"

        for section_index in range(self.max_sections):
            if section_index < len(state.sections):
                section = state.sections[section_index]
                self.section_titles[section_index].text = section.title
                row_texts = compact_line_rows(section.line_rows)
                for row_index, label_row in enumerate(self.section_line_labels[section_index]):
                    label_row.text = row_texts[row_index][:42] if row_index < len(row_texts) else ""
            else:
                self.section_titles[section_index].text = ""
                for label_row in self.section_line_labels[section_index]:
                    label_row.text = ""

        if hasattr(self.display, "refresh"):
            try:
                self.display.refresh()
            except Exception:
                pass
