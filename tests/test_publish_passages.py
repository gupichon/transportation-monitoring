import json

from transportation_monitoring import publish_passages


def test_snapshot_uses_authentication_qos_zero_and_retain(monkeypatch):
    calls = []
    monkeypatch.setattr(
        publish_passages,
        "secrets",
        {
            "mqtt": {
                "host": "192.168.1.30",
                "port": 1883,
                "topic": "transportation_monitoring",
                "username": "user",
                "password": "secret",
            }
        },
    )
    monkeypatch.setattr(
        publish_passages.publish,
        "single",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    publish_passages.publish_display_snapshot([{"line": "T6"}])

    args, kwargs = calls[0]
    assert args[0] == "transportation_monitoring/snapshot"
    assert json.loads(args[1])["passages"][0]["line"] == "T6"
    assert kwargs["hostname"] == "192.168.1.30"
    assert kwargs["port"] == 1883
    assert kwargs["auth"] == {"username": "user", "password": "secret"}
    assert kwargs["qos"] == 0
    assert kwargs["retain"] is True


def test_missing_mqtt_credentials_fail_without_values(monkeypatch):
    monkeypatch.setattr(publish_passages, "secrets", {"mqtt": {"host": "broker"}})

    try:
        publish_passages._mqtt_settings()
    except ValueError as exc:
        assert str(exc) == "Missing MQTT settings: username, password"
    else:
        raise AssertionError("missing credentials must fail")


def test_empty_snapshot_is_still_published(monkeypatch):
    calls = []
    monkeypatch.setattr(
        publish_passages,
        "secrets",
        {
            "mqtt": {
                "host": "broker",
                "username": "user",
                "password": "password",
            }
        },
    )
    monkeypatch.setattr(
        publish_passages.publish,
        "single",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    publish_passages.publish_display_snapshot([])

    assert json.loads(calls[0][0][1])["passages"] == []
