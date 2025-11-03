import json

import paho.mqtt.publish as publish

from transportation_monitoring import secrets
from transportation_monitoring.extract_next_passages import waiting_time_formatter

MQTT_HOST = secrets["mqtt"]["host"]
MQTT_PORT = secrets["mqtt"]["port"]
MQTT_TOPIC = secrets["mqtt"]["topic"]

def publish_passages(passages: list[dict]):
    if not passages:
        return

    for passage in passages:
        payload = json.dumps(passage, default=waiting_time_formatter)
        full_topic = MQTT_TOPIC + "/" + passage["stop_name"] + "/" + passage["line"]
        publish.single(full_topic, payload, hostname=MQTT_HOST)
