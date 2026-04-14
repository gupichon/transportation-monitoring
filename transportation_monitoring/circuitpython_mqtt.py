from __future__ import annotations

from dataclasses import dataclass

from transportation_monitoring.circuitpython_backend import CircuitPythonMagTagBackend
from transportation_monitoring.display_config import DisplayConfig
from transportation_monitoring.display_models import TransitDisplayState, build_display_state
from transportation_monitoring.mqtt_display import parse_snapshot_payload, snapshot_topic


@dataclass(frozen=True)
class MQTTDisplayMessage:
    topic: str
    payload: str | bytes


class CircuitPythonMQTTDisplayController:
    def __init__(
        self,
        config: DisplayConfig,
        backend: CircuitPythonMagTagBackend,
        base_topic: str,
    ) -> None:
        self.config = config
        self.backend = backend
        self.base_topic = base_topic.rstrip("/")
        self.expected_topic = snapshot_topic(self.base_topic)
        self.last_state: TransitDisplayState | None = None

    def accepts_topic(self, topic: str) -> bool:
        return topic == self.expected_topic

    def process_message(self, topic: str, payload: str | bytes):
        if not self.accepts_topic(topic):
            return None

        snapshot = parse_snapshot_payload(payload)
        state = build_display_state(
            passages=snapshot["passages"],
            selections=self.config.selections,
            title=self.config.title,
            generated_at=snapshot["generated_at"],
            max_entries_per_stop=self.config.max_entries_per_stop,
            footer=self.config.footer,
        )
        self.last_state = state
        return self.backend.apply_state(state)

    def process(self, message: MQTTDisplayMessage):
        return self.process_message(message.topic, message.payload)
