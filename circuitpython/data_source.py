import socketpool
import time
import wifi

import adafruit_minimqtt.adafruit_minimqtt as MQTT


class MQTTDataSource:
    def __init__(
        self,
        state,
        ssid,
        wifi_password,
        broker,
        port,
        username,
        password,
        transport_topic,
        temperature_topic,
        error_after_failures=5,
    ):
        self.state = state
        self.ssid = ssid
        self.wifi_password = wifi_password
        self.transport_topic = transport_topic
        self.temperature_topic = temperature_topic
        self.error_after_failures = error_after_failures
        self.wifi_failures = 0
        self.mqtt_failures = 0
        self.pool = None
        self.client = None
        self.mqtt_settings = (broker, port, username, password)

    def _record_failure(self, kind, exc):
        print("%s connection error: %s" % (kind, exc))
        if kind == "WIFI":
            self.wifi_failures += 1
            if self.wifi_failures >= self.error_after_failures:
                self.state.network_error = "ERR WIFI"
        else:
            self.mqtt_failures += 1
            if self.mqtt_failures >= self.error_after_failures:
                self.state.network_error = "ERR MQTT"

    def _on_message(self, client, topic, message):
        try:
            if topic == self.transport_topic:
                self.state.update_transport(message)
            elif topic == self.temperature_topic:
                self.state.update_temperature(message)
        except (KeyError, TypeError, ValueError) as exc:
            print("Invalid MQTT payload on %s: %s" % (topic, exc))

    def connect(self):
        if not wifi.radio.connected:
            try:
                wifi.radio.connect(self.ssid, self.wifi_password)
                self.wifi_failures = 0
            except Exception as exc:
                self._record_failure("WIFI", exc)
                return False

        broker, port, username, password = self.mqtt_settings
        try:
            if self.client is None:
                self.pool = socketpool.SocketPool(wifi.radio)
                self.client = MQTT.MQTT(
                    broker=broker,
                    port=port,
                    username=username,
                    password=password,
                    socket_pool=self.pool,
                    is_ssl=False,
                    keep_alive=60,
                )
                self.client.on_message = self._on_message
            self.client.connect()
            self.client.subscribe(self.transport_topic, qos=0)
            self.client.subscribe(self.temperature_topic, qos=0)
            self.mqtt_failures = 0
            self.state.network_error = None
            return True
        except Exception as exc:
            self._record_failure("MQTT", exc)
            return False

    def loop(self):
        if self.client is None or not self.client.is_connected():
            return False
        try:
            self.client.loop(timeout=1)
            return True
        except Exception as exc:
            self._record_failure("MQTT", exc)
            try:
                self.client.disconnect()
            except Exception:
                pass
            return False
