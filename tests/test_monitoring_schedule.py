from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from transportation_monitoring.data_explorer import yload
from transportation_monitoring.monitoring_schedule import (
    daily_call_count,
    interval_for,
    next_run_after,
)
from transportation_monitoring import stops_query_loop


TZ = ZoneInfo("Europe/Paris")


@pytest.fixture
def monitoring_config():
    return yload("stops_monitoring.yaml")


@pytest.mark.parametrize(
    ("clock", "expected"),
    [
        ((6, 29), None),
        ((6, 30), 180),
        ((7, 29), 180),
        ((7, 30), 60),
        ((10, 29), 60),
        ((10, 30), 180),
        ((22, 29), 180),
        ((22, 30), None),
    ],
)
def test_dynamic_interval_boundaries(monitoring_config, clock, expected):
    now = datetime(2026, 7, 30, *clock, tzinfo=TZ)
    assert interval_for(now, monitoring_config["schedule"]) == expected


def test_schedule_uses_880_calls_per_day(monitoring_config):
    assert len(monitoring_config["stops"]) == 2
    assert daily_call_count(monitoring_config["schedule"], 2) == 880


def test_night_schedule_resumes_at_0630(monitoring_config):
    now = datetime(2026, 7, 30, 22, 30, tzinfo=TZ)
    assert next_run_after(now, monitoring_config["schedule"], "Europe/Paris") == datetime(
        2026, 7, 31, 6, 30, tzinfo=TZ
    )


def test_partial_idfm_failure_returns_no_snapshot(monkeypatch):
    calls = []

    def fake_query(api_key, monitoring_ref):
        calls.append(monitoring_ref)
        if monitoring_ref == "STOP_B":
            raise RuntimeError("temporary failure")
        return {"response": monitoring_ref}

    monkeypatch.setattr(stops_query_loop, "idfm_next_passages", fake_query)
    monkeypatch.setattr(
        stops_query_loop,
        "extract_next_passages",
        lambda response: [{"monitoring_ref": response["response"]}],
    )

    assert stops_query_loop.query_stops("key", ["STOP_A", "STOP_B"]) is None
    assert calls == ["STOP_A", "STOP_B"]
