import json

import paho.mqtt.publish as publish

from transportation_monitoring import secrets
from transportation_monitoring.extract_next_passages import waiting_time_formatter
from transportation_monitoring.mqtt_display import build_snapshot_payload, snapshot_topic


def _mqtt_settings() -> tuple[str, int, str]:
    mqtt = secrets.get("mqtt", {})
    host = mqtt.get("host", "localhost")
    port = int(mqtt.get("port", 1883))
    topic = mqtt.get("topic", "transportation_monitoring")
    return host, port, topic

def publish_passages(passages: list[dict]):
    if not passages:
        return

    mqtt_host, mqtt_port, mqtt_topic = _mqtt_settings()
    for passage in passages:
        payload = json.dumps(passage, default=waiting_time_formatter)
        full_topic = mqtt_topic + "/" + str(passage["stop_name"]) + "/" + str(passage["line"])
        publish.single(full_topic, payload, hostname=mqtt_host, port=mqtt_port)


def publish_display_snapshot(passages: list[dict]):
    if not passages:
        return

    mqtt_host, mqtt_port, mqtt_topic = _mqtt_settings()
    payload = build_snapshot_payload(passages)
    publish.single(snapshot_topic(mqtt_topic), payload, hostname=mqtt_host, port=mqtt_port)
