from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from transportation_monitoring.circuitpython_backend import (
    CircuitPythonMagTagBackend,
    InMemoryCircuitPythonView,
)
from transportation_monitoring.circuitpython_mqtt import CircuitPythonMQTTDisplayController
from transportation_monitoring.display_config import DisplayConfig
from transportation_monitoring.display_models import StopRouteSelection, build_display_state
from transportation_monitoring.mock_display import MockPngDisplay
from transportation_monitoring.mqtt_display import build_snapshot_payload, snapshot_topic


ARTIFACTS_DIR = Path("artifacts")


def build_example_state():
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
        {
            "monitoring_ref": "STOP_B",
            "stop_name": "Cimetière",
            "line": "189",
            "destination": "Porte de Saint-Cloud",
            "waiting_time": timedelta(minutes=9),
            "status": "delayed",
        },
        {
            "monitoring_ref": "STOP_B",
            "stop_name": "Cimetière",
            "line": "190",
            "destination": "Mairie de Clamart",
            "waiting_time": timedelta(minutes=12),
            "status": "onTime",
        },
        {
            "monitoring_ref": "STOP_B",
            "stop_name": "Cimetière",
            "line": "190",
            "destination": "Petit Clamart",
            "waiting_time": timedelta(minutes=18),
            "status": "onTime",
        },
    ]
    selections = (
        StopRouteSelection("STOP_A", "Division Leclerc", ("189", "190")),
        StopRouteSelection("STOP_B", "Cimetière", ("189", "190")),
    )
    state = build_display_state(
        passages=passages,
        selections=selections,
        generated_at=generated_at,
        max_entries_per_stop=3,
    )
    return generated_at, passages, selections, state


def generate_artifacts(output_dir: Path = ARTIFACTS_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at, passages, selections, state = build_example_state()
    mock_path = MockPngDisplay().save_png(state, output_dir / "mock_display_example.png")

    config = DisplayConfig(
        selections=selections,
        max_entries_per_stop=3,
    )
    controller = CircuitPythonMQTTDisplayController(
        config=config,
        backend=CircuitPythonMagTagBackend(view=InMemoryCircuitPythonView(max_sections=2, max_rows_per_section=3)),
        base_topic="transport/home/bus",
    )
    payload = build_snapshot_payload(passages, generated_at=generated_at)
    controller.process_message(snapshot_topic("transport/home/bus"), payload)
    mqtt_path = MockPngDisplay().save_png(controller.last_state, output_dir / "mqtt_display_example.png")

    return mock_path, mqtt_path


def main() -> None:
    mock_path, mqtt_path = generate_artifacts()
    print(mock_path)
    print(mqtt_path)


if __name__ == "__main__":
    main()
