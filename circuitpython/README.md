# MagTag CircuitPython

Target: Adafruit MagTag 2.9" grayscale running CircuitPython 10.2.1.

1. Copy `secret.example.py` to `secret.py` and fill the Wi-Fi and EMQX credentials.
2. Copy `code.py`, `config.py`, `data_source.py`, `display_state.py`,
   `display_view.py`, and the local `secret.py` to the root of `CIRCUITPY`.
3. From the CircuitPython 10.x library bundle, copy the
   `adafruit_minimqtt` folder to `CIRCUITPY/lib`.
4. Reset the board and use the serial console for connection and payload errors.

`secret.py` is ignored by Git and must never be committed.
