from __future__ import annotations

from dataclasses import dataclass
import json
from time import monotonic

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
        temperature_topic: str = "zigbee2mqtt/Temp/hum balcon",
        monotonic_fn=monotonic,
    ) -> None:
        self.config = config
        self.backend = backend
        self.base_topic = base_topic.rstrip("/")
        self.expected_topic = snapshot_topic(self.base_topic)
        self.temperature_topic = temperature_topic
        self.monotonic_fn = monotonic_fn
        self.last_state: TransitDisplayState | None = None
        self._passages: list[dict] = []
        self._generated_at = None
        self._temperature_c: float | None = None
        self._temperature_received_at: float | None = None
        self._network_error: str | None = None

    def accepts_topic(self, topic: str) -> bool:
        return topic in (self.expected_topic, self.temperature_topic)

    def _temperature_is_stale(self, now: float | None = None) -> bool:
        stale_after = self.config.temperature_stale_after_seconds
        if stale_after is None or self._temperature_received_at is None:
            return False
        now = self.monotonic_fn() if now is None else now
        return now - self._temperature_received_at >= stale_after

    def _render(self):
        state = build_display_state(
            passages=self._passages,
            selections=self.config.selections,
            title=self.config.title,
            generated_at=self._generated_at,
            max_entries_per_stop=self.config.max_entries_per_stop,
            footer=self.config.footer,
            temperature_c=self._temperature_c,
            temperature_stale=self._temperature_is_stale(),
            network_error=self._network_error,
        )
        if state == self.last_state:
            return None
        self.last_state = state
        return self.backend.apply_state(state)

    def process_message(self, topic: str, payload: str | bytes):
        if not self.accepts_topic(topic):
            return None

        try:
            if topic == self.expected_topic:
                snapshot = parse_snapshot_payload(payload)
                self._passages = snapshot["passages"]
                self._generated_at = snapshot["generated_at"]
            else:
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                raw = json.loads(payload)
                value = raw["temperature"]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("temperature must be numeric")
                self._temperature_c = float(value)
                self._temperature_received_at = self.monotonic_fn()
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"Invalid MQTT payload on {topic}: {exc}")
            return None
        return self._render()

    def set_network_error(self, error: str | None):
        if error not in (None, "ERR WIFI", "ERR MQTT"):
            raise ValueError("unsupported network error")
        self._network_error = error
        return self._render()

    def tick(self):
        return self._render()

    def process(self, message: MQTTDisplayMessage):
        return self.process_message(message.topic, message.payload)
