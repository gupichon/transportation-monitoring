from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from transportation_monitoring.display_backends import CircuitPythonMagTagDisplay
from transportation_monitoring.display_config import parse_display_config
from transportation_monitoring.display_models import (
    StopRouteSelection,
    build_display_state,
)
from transportation_monitoring.mock_display import MockMagTagDisplay


def test_build_display_state_filters_lines_and_formats_wait_time():
    passages = [
        {
            "monitoring_ref": "STOP_A",
            "line": "189",
            "destination": "Clamart",
            "waiting_time": timedelta(minutes=2, seconds=20),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_A",
            "line": "190",
            "destination": "Mairie",
            "waiting_time": timedelta(seconds=20),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_A",
            "line": "191",
            "destination": "Ignore",
            "waiting_time": timedelta(minutes=5),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_A",
            "line": "190",
            "destination": "Petit Clamart",
            "waiting_time": timedelta(minutes=6),
            "status": "onTime",
        },
    ]

    state = build_display_state(
        passages=passages,
        selections=[StopRouteSelection("STOP_A", "Division Leclerc", ("189", "190"))],
        generated_at=datetime(2026, 4, 14, 15, 0, tzinfo=ZoneInfo("Europe/Paris")),
        max_entries_per_stop=3,
    )

    section = state.sections[0]
    assert section.title == "Division Leclerc"
    assert [entry.line for entry in section.entries] == ["190", "189", "190"]
    assert [entry.wait_label for entry in section.entries] == ["1 min", "2 min", "6 min"]
    assert [row.line for row in section.line_rows] == ["190", "189"]
    assert [row.wait_labels for row in section.line_rows] == [("1 min", "6 min"), ("2 min",)]


def test_mock_magtag_display_renders_png_image():
    state = build_display_state(
        passages=[
            {
                "monitoring_ref": "STOP_A",
                "line": "189",
                "destination": "Clamart Centre",
                "waiting_time": timedelta(minutes=3),
                "status": "onTime",
            }
        ],
        selections=[StopRouteSelection("STOP_A", "Division Leclerc", ("189",))],
        generated_at=datetime(2026, 4, 14, 15, 5, tzinfo=ZoneInfo("Europe/Paris")),
    )

    renderer = MockMagTagDisplay()
    image = renderer.render_image(state)

    assert image.size == (296, 128)
    assert image.mode == "L"


def test_circuitpython_backend_prefers_partial_updates_after_first_render():
    backend = CircuitPythonMagTagDisplay(full_refresh_every=10)

    state_a = build_display_state(
        passages=[
            {
                "monitoring_ref": "STOP_A",
                "line": "189",
                "destination": "Clamart Centre",
                "waiting_time": timedelta(minutes=3),
                "status": "onTime",
            }
        ],
        selections=[StopRouteSelection("STOP_A", "Division Leclerc", ("189",))],
        generated_at=datetime(2026, 4, 14, 15, 5, tzinfo=ZoneInfo("Europe/Paris")),
    )
    state_b = build_display_state(
        passages=[
            {
                "monitoring_ref": "STOP_A",
                "line": "189",
                "destination": "Clamart Centre",
                "waiting_time": timedelta(minutes=2),
                "status": "onTime",
            }
        ],
        selections=[StopRouteSelection("STOP_A", "Division Leclerc", ("189",))],
        generated_at=datetime(2026, 4, 14, 15, 6, tzinfo=ZoneInfo("Europe/Paris")),
    )

    first_plan = backend.update(state_a)
    second_plan = backend.update(state_b)

    assert first_plan.full_refresh is True
    assert second_plan.full_refresh is False
    assert any(region.name == "header" for region in second_plan.regions)
    assert any(region.name == "section_0" for region in second_plan.regions)


def test_parse_display_config():
    config = parse_display_config(
        {
            "max_entries_per_stop": 3,
            "stops": [
                {
                    "monitoring_ref": "STIF:StopPoint:Q:41855:",
                    "label": "Division Leclerc",
                    "lines": ["189", "190"],
                }
            ],
        }
    )

    assert config.title == ""
    assert config.max_entries_per_stop == 3
    assert config.footer is None
    assert len(config.selections) == 1
    assert config.selections[0].lines == ("189", "190")
