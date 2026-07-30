from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
from threading import Event
from uuid import uuid4
from zoneinfo import ZoneInfo

import paho.mqtt.client as mqtt
import pytest
import yaml

from transportation_monitoring.data_explorer import yload


pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_TAG = "transportation-monitoring:integration-test"


def _require_live_test() -> None:
    if os.environ.get("RUN_LIVE_INTEGRATION") != "1":
        pytest.skip("set RUN_LIVE_INTEGRATION=1 to run the live Docker integration")


def _docker(*args: str, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_docker_queries_idfm_and_publishes_authenticated_snapshot(tmp_path):
    _require_live_test()
    source_secrets = yload("secrets.yaml")
    mqtt_settings = source_secrets.get("mqtt", {})
    required = ("host", "username", "password")
    missing = [key for key in required if not mqtt_settings.get(key)]
    assert not missing, f"missing MQTT settings: {', '.join(missing)}"
    assert source_secrets.get("API_KEY"), "missing API_KEY"

    unique_base_topic = f"transportation_monitoring/integration/{uuid4().hex}"
    expected_topic = f"{unique_base_topic}/snapshot"
    test_secrets = copy.deepcopy(source_secrets)
    test_secrets["mqtt"]["topic"] = unique_base_topic
    secrets_path = tmp_path / "secrets.yaml"
    secrets_path.write_text(
        yaml.safe_dump(test_secrets, allow_unicode=True),
        encoding="utf-8",
    )

    build = _docker("build", "-f", "docker/Dockerfile", "-t", IMAGE_TAG, ".")
    assert build.returncode == 0, f"Docker build failed:\n{build.stdout}\n{build.stderr}"

    connected = Event()
    received = Event()
    payloads: list[bytes] = []
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"transportation-monitoring-test-{uuid4().hex}",
    )
    client.username_pw_set(mqtt_settings["username"], mqtt_settings["password"])

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(expected_topic, qos=0)
            connected.set()

    def on_message(client, userdata, message):
        if message.topic == expected_topic:
            payloads.append(message.payload)
            received.set()

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_settings["host"], int(mqtt_settings.get("port", 1883)), 30)
    client.loop_start()

    try:
        assert connected.wait(10), "MQTT test client could not connect to EMQX"
        container_name = f"transportation-monitoring-integration-{uuid4().hex[:12]}"
        run = _docker(
            "run",
            "--rm",
            "--name",
            container_name,
            "--mount",
            f"type=bind,source={secrets_path.resolve()},target=/app/secrets.yaml,readonly",
            "--mount",
            (
                "type=bind,"
                f"source={(PROJECT_ROOT / 'stops_monitoring.yaml').resolve()},"
                "target=/app/stops_monitoring.yaml,readonly"
            ),
            IMAGE_TAG,
            "python",
            "-m",
            "transportation_monitoring.stops_query_loop",
            "--once",
            timeout=90,
        )
        assert run.returncode == 0, f"Producer container failed:\n{run.stdout}\n{run.stderr}"
        assert received.wait(10), "no MQTT snapshot received from the producer container"

        payload = json.loads(payloads[-1].decode("utf-8"))
        generated_at = datetime.fromisoformat(payload["generated_at"])
        assert generated_at.tzinfo is not None
        assert generated_at.utcoffset() == generated_at.astimezone(
            ZoneInfo("Europe/Paris")
        ).utcoffset()
        assert isinstance(payload["passages"], list)
        for passage in payload["passages"]:
            assert {
                "monitoring_ref",
                "stop_name",
                "line",
                "destination",
                "direction",
                "status",
                "waiting_seconds",
            } <= passage.keys()
    finally:
        if connected.is_set():
            cleanup = client.publish(expected_topic, payload=b"", qos=0, retain=True)
            cleanup.wait_for_publish(timeout=5)
        client.loop_stop()
        client.disconnect()
