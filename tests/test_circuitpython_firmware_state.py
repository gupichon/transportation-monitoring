import importlib.util
from pathlib import Path


def _load_firmware_state_module():
    path = Path(__file__).parents[1] / "circuitpython" / "display_state.py"
    spec = importlib.util.spec_from_file_location("firmware_display_state", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_firmware_state_combines_topics_and_marks_stale_temperature():
    module = _load_firmware_state_module()
    state = module.DisplayState(
        stops=(
            {
                "monitoring_ref": "STOP_A",
                "label": "Division Leclerc",
                "lines": ("T6",),
            },
        ),
        stale_after_seconds=5400,
    )
    state.update_temperature('{"temperature": 22.9}', now=100)
    state.update_transport(
        '{"generated_at":"2026-07-30T09:00:00+02:00",'
        '"passages":[{"monitoring_ref":"STOP_A","line":"T6","waiting_seconds":180}]}'
    )

    assert state.temperature_label(now=100) == "22,9 °C"
    assert state.temperature_label(now=5500) == "22,9 °C !"
    assert state.clock_label() == "Maj 09:00"
    assert state.sections() == (("Division Leclerc", ("T6  3 min",)),)


def test_firmware_network_error_replaces_clock():
    module = _load_firmware_state_module()
    state = module.DisplayState(stops=())
    state.generated_at = "2026-07-30T09:00:00+02:00"
    state.network_error = "ERR WIFI"

    assert state.clock_label() == "ERR WIFI"
