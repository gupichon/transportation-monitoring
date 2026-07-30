MQTT_BROKER = "192.168.1.30"
MQTT_PORT = 1883
TRANSPORT_TOPIC = "transportation_monitoring/snapshot"
TEMPERATURE_TOPIC = "zigbee2mqtt/Temp/hum balcon"

TEMPERATURE_STALE_AFTER_SECONDS = 5400
NETWORK_ERROR_AFTER_FAILURES = 5
RECONNECT_DELAY_SECONDS = 10
MAX_PASSAGES_PER_STOP = 3

DISPLAY_STOPS = (
    {
        "monitoring_ref": "STIF:StopPoint:Q:41855:",
        "label": "Division Leclerc",
        "lines": ("T6",),
    },
    {
        "monitoring_ref": "STIF:StopPoint:Q:12406:",
        "label": "Cimetière",
        "lines": ("189", "190"),
    },
)
