from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from transportation_monitoring.circuitpython_backend import (
    CircuitPythonMagTagBackend,
    InMemoryCircuitPythonView,
)
from transportation_monitoring.circuitpython_mqtt import CircuitPythonMQTTDisplayController
from transportation_monitoring.display_config import DisplayConfig
from transportation_monitoring.display_models import StopRouteSelection
from transportation_monitoring.mock_display import MockPngDisplay
from transportation_monitoring.mqtt_display import build_snapshot_payload, snapshot_topic


def test_circuitpython_backend_consumes_mqtt_snapshot_and_matches_mock_render():
    generated_at = datetime(2026, 4, 14, 8, 12, tzinfo=ZoneInfo("Europe/Paris"))
    passages = [
        {
            "monitoring_ref": "STOP_A",
            "stop_name": "Division Leclerc",
            "line": "189",
            "destination": "Clamart Centre",
            "waiting_time": timedelta(minutes=3),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_A",
            "stop_name": "Division Leclerc",
            "line": "190",
            "destination": "Mairie de Clamart",
            "waiting_time": timedelta(minutes=7),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_A",
            "stop_name": "Division Leclerc",
            "line": "190",
            "destination": "Mairie d'Issy",
            "waiting_time": timedelta(minutes=11),
            "status": "onTime",
        },
    ]
    config = DisplayConfig(
        selections=(StopRouteSelection("STOP_A", "Division Leclerc", ("189", "190")),),
        max_entries_per_stop=3,
    )
    view = InMemoryCircuitPythonView(max_sections=2, max_rows_per_section=3)
    backend = CircuitPythonMagTagBackend(view=view, full_refresh_every=5)
    controller = CircuitPythonMQTTDisplayController(
        config=config,
        backend=backend,
        base_topic="transport/home/bus",
    )

    topic = snapshot_topic("transport/home/bus")
    payload = build_snapshot_payload(passages, generated_at=generated_at)

    plan = controller.process_message(topic, payload)

    assert plan is not None
    assert plan.full_refresh is True
    assert view.title.text == ""
    assert view.clock.text == "Maj 08:12"
    assert view.section_titles[0].text == "Division Leclerc"
    assert view.section_lines[0][0].text == "189  3 min"
    assert view.section_lines[0][1].text == "190  7 min | 11 min"
    assert view.section_lines[0][2].text == ""
    assert view.footer.text == ""

    image = MockPngDisplay().render_image(controller.last_state)

    assert controller.last_state is not None
    assert controller.last_state.generated_at == generated_at
    assert image.size == (296, 128)


def test_circuitpython_controller_ignores_other_topics():
    config = DisplayConfig(
        selections=(StopRouteSelection("STOP_A", "Division Leclerc", ("189",)),),
    )
    view = InMemoryCircuitPythonView()
    backend = CircuitPythonMagTagBackend(view=view)
    controller = CircuitPythonMQTTDisplayController(
        config=config,
        backend=backend,
        base_topic="transport/home/bus",
    )

    result = controller.process_message("transport/home/bus/other", "{}")

    assert result is None
    assert controller.last_state is None
