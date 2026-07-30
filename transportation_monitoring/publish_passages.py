import json

import paho.mqtt.publish as publish

from transportation_monitoring import secrets
from transportation_monitoring.extract_next_passages import waiting_time_formatter
from transportation_monitoring.mqtt_display import build_snapshot_payload, snapshot_topic


def _mqtt_settings() -> tuple[str, int, str, dict[str, str]]:
    mqtt = secrets.get("mqtt", {})
    required = ("host", "username", "password")
    missing = [key for key in required if not mqtt.get(key)]
    if missing:
        raise ValueError(f"Missing MQTT settings: {', '.join(missing)}")
    host = mqtt["host"]
    port = int(mqtt.get("port", 1883))
    topic = mqtt.get("topic", "transportation_monitoring")
    auth = {"username": mqtt["username"], "password": mqtt["password"]}
    return host, port, topic, auth

def publish_passages(passages: list[dict]):
    if not passages:
        return

    mqtt_host, mqtt_port, mqtt_topic, mqtt_auth = _mqtt_settings()
    for passage in passages:
        payload = json.dumps(passage, default=waiting_time_formatter)
        full_topic = mqtt_topic + "/" + str(passage["stop_name"]) + "/" + str(passage["line"])
        publish.single(full_topic, payload, hostname=mqtt_host, port=mqtt_port, auth=mqtt_auth)


def publish_display_snapshot(passages: list[dict]):
    mqtt_host, mqtt_port, mqtt_topic, mqtt_auth = _mqtt_settings()
    payload = build_snapshot_payload(passages)
    publish.single(
        snapshot_topic(mqtt_topic),
        payload,
        hostname=mqtt_host,
        port=mqtt_port,
        auth=mqtt_auth,
        qos=0,
        retain=True,
    )
