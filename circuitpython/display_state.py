import json
import time


class DisplayState:
    def __init__(self, stops, max_passages=3, stale_after_seconds=None):
        self.stops = stops
        self.max_passages = max_passages
        self.stale_after_seconds = stale_after_seconds
        self.generated_at = None
        self.passages = []
        self.temperature = None
        self.temperature_received_at = None
        self.network_error = None

    def update_transport(self, payload):
        raw = json.loads(payload)
        generated_at = raw["generated_at"]
        passages = raw.get("passages", [])
        if not isinstance(generated_at, str) or not isinstance(passages, list):
            raise ValueError("invalid transport snapshot")
        self.generated_at = generated_at
        self.passages = passages

    def update_temperature(self, payload, now=None):
        raw = json.loads(payload)
        value = raw["temperature"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("temperature must be numeric")
        self.temperature = float(value)
        self.temperature_received_at = time.monotonic() if now is None else now

    def temperature_is_stale(self, now=None):
        if self.stale_after_seconds is None or self.temperature_received_at is None:
            return False
        now = time.monotonic() if now is None else now
        return now - self.temperature_received_at >= self.stale_after_seconds

    def temperature_label(self, now=None):
        if self.temperature is None:
            return "--,- °C"
        label = ("%.1f" % self.temperature).replace(".", ",") + " °C"
        return label + (" !" if self.temperature_is_stale(now) else "")

    def clock_label(self):
        if self.network_error:
            return self.network_error
        if not self.generated_at or "T" not in self.generated_at:
            return ""
        return "Maj " + self.generated_at.split("T", 1)[1][:5]

    @staticmethod
    def _wait_label(seconds):
        if seconds is None:
            return "--"
        seconds = int(seconds)
        if seconds <= 0:
            return "Approche"
        if seconds < 60:
            return "1 min"
        return "%d min" % (seconds // 60)

    def sections(self):
        result = []
        for stop in self.stops:
            allowed = stop["lines"]
            matching = [
                passage
                for passage in self.passages
                if passage.get("monitoring_ref") == stop["monitoring_ref"]
                and (not allowed or str(passage.get("line")) in allowed)
            ]
            matching.sort(
                key=lambda passage: (
                    passage.get("waiting_seconds") is None,
                    passage.get("waiting_seconds") or 0,
                )
            )
            grouped = {}
            order = []
            for passage in matching[: self.max_passages]:
                line = str(passage.get("line", "?"))
                if line not in grouped:
                    grouped[line] = []
                    order.append(line)
                grouped[line].append(self._wait_label(passage.get("waiting_seconds")))
            rows = [
                line + "  " + " | ".join(grouped[line][:3])
                for line in order
            ] or ["Aucun passage"]
            result.append((stop["label"], tuple(rows)))
        return tuple(result)

    def visible_signature(self, now=None):
        return (
            self.temperature_label(now),
            self.clock_label(),
            self.sections(),
        )
