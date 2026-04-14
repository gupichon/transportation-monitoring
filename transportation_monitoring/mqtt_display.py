from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any


SNAPSHOT_TOPIC_SUFFIX = "snapshot"


def snapshot_topic(base_topic: str) -> str:
    return f"{base_topic.rstrip('/')}/{SNAPSHOT_TOPIC_SUFFIX}"


def _waiting_seconds(waiting_time: Any) -> int | None:
    if waiting_time is None:
        return None
    if isinstance(waiting_time, timedelta):
        return int(waiting_time.total_seconds())
    if isinstance(waiting_time, (int, float)):
        return int(waiting_time)
    raise TypeError(f"Unsupported waiting_time type: {type(waiting_time)}")


def build_snapshot_payload(
    passages: list[dict],
    generated_at: datetime | None = None,
) -> str:
    if generated_at is None:
        generated_at = datetime.now().astimezone()

    payload = {
        "generated_at": generated_at.isoformat(),
        "passages": [
            {
                "monitoring_ref": passage.get("monitoring_ref"),
                "stop_name": passage.get("stop_name"),
                "line": passage.get("line"),
                "destination": passage.get("destination"),
                "direction": passage.get("direction"),
                "status": passage.get("status"),
                "waiting_seconds": _waiting_seconds(passage.get("waiting_time")),
            }
            for passage in passages
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_snapshot_payload(payload: str | bytes) -> dict[str, Any]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    raw = json.loads(payload)
    generated_at = datetime.fromisoformat(raw["generated_at"])
    passages: list[dict[str, Any]] = []
    for passage in raw.get("passages", []):
        waiting_seconds = passage.get("waiting_seconds")
        waiting_time = None if waiting_seconds is None else timedelta(seconds=int(waiting_seconds))
        passages.append(
            {
                "monitoring_ref": passage.get("monitoring_ref"),
                "stop_name": passage.get("stop_name"),
                "line": passage.get("line"),
                "destination": passage.get("destination"),
                "direction": passage.get("direction"),
                "status": passage.get("status"),
                "waiting_time": waiting_time,
            }
        )

    return {
        "generated_at": generated_at,
        "passages": passages,
    }
