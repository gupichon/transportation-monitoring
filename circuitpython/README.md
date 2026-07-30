# MagTag CircuitPython

Target: Adafruit MagTag 2.9" grayscale running CircuitPython 10.2.1.

1. Copy `secret.example.py` to `secret.py` and fill the Wi-Fi and EMQX credentials.
2. Copy `code.py`, `config.py`, `data_source.py`, `display_state.py`,
   `display_view.py`, and the local `secret.py` to the root of `CIRCUITPY`.
3. Copy the contents of the local `lib/` directory to `CIRCUITPY/lib/`.
4. Reset the board and use the serial console for connection and payload errors.

`secret.py` is ignored by Git and must never be committed.

The local `lib/` directory is also ignored by Git. It is currently populated
from the official Adafruit CircuitPython 10.x MPY bundle dated 2026-07-18 and
contains:

- `adafruit_minimqtt/`;
- `adafruit_ticks.mpy`, required by MiniMQTT and Display Text;
- `adafruit_bitmap_font/`, a declared dependency of Display Text.

CircuitPython 10.2.1 for the MagTag already includes
`adafruit_connection_manager` and `adafruit_display_text` as frozen modules.
