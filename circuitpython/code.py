import board
import time

import config
import secret
from data_source import MQTTDataSource
from display_state import DisplayState
from display_view import MagTagDisplayView


state = DisplayState(
    stops=config.DISPLAY_STOPS,
    max_passages=config.MAX_PASSAGES_PER_STOP,
    stale_after_seconds=config.TEMPERATURE_STALE_AFTER_SECONDS,
)
view = MagTagDisplayView(board.DISPLAY, max_sections=len(config.DISPLAY_STOPS))
source = MQTTDataSource(
    state=state,
    ssid=secret.WIFI_SSID,
    wifi_password=secret.WIFI_PASSWORD,
    broker=config.MQTT_BROKER,
    port=config.MQTT_PORT,
    username=secret.MQTT_USERNAME,
    password=secret.MQTT_PASSWORD,
    transport_topic=config.TRANSPORT_TOPIC,
    temperature_topic=config.TEMPERATURE_TOPIC,
    error_after_failures=config.NETWORK_ERROR_AFTER_FAILURES,
)

view.update(state)
next_connection_attempt = 0
while True:
    now = time.monotonic()
    if source.client is None or not source.client.is_connected():
        if now >= next_connection_attempt:
            source.connect()
            view.update(state, now)
            next_connection_attempt = now + config.RECONNECT_DELAY_SECONDS
    else:
        if not source.loop():
            next_connection_attempt = now + config.RECONNECT_DELAY_SECONDS
        view.update(state, now)
    time.sleep(0.1)
