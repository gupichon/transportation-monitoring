# Transportation Monitoring

A Python project for monitoring Île-de-France (IDFM) public transportation in real-time and publishing updated information to MQTT.

## Overview

This project queries the IDFM (Île-de-France Mobilités) API to fetch real-time information about upcoming passages for specified transportation stops (bus, tram, RER, etc.). The data is then processed and published to an MQTT broker, making it ideal for integration with home automation systems like Home Assistant.

## Features

- Real-time monitoring of IDFM transportation stops
- Integration with IDFM PRIM API for live passage data
- MQTT publishing for home automation integration (e.g., Home Assistant)
- Mock display rendering for offline UI development targeting Adafruit MagTag
- Configurable monitoring intervals
- Docker support for easy deployment
- Support for multiple stops monitoring

## Requirements

- Python >= 3.12
- IDFM API key (from [IDFM Developer Portal](https://prim.iledefrance-mobilites.fr))
- MQTT broker (optional, for Home Assistant integration)

## Installation

### From Source

1. Clone the repository:
```bash
git clone <repository-url>
cd TransportationMonitoring
```

2. Install dependencies:
```bash
pip install -e .
```

For development with tests:
```bash
pip install -e ".[test]"
```

### Docker

Build the Docker image:
```bash
docker build -t transportation-monitoring -f docker/Dockerfile .
```

## Configuration

Create the following configuration files in the project root:

### `stops_monitoring.yaml`

Specify which stops to monitor and the query interval:

```yaml
stops:
  - "STIF:StopPoint:Q:41855:"  # Stop 1
  - "STIF:StopPoint:Q:12406:"  # Stop 2
sleeping_time: 120  # Interval in seconds between queries
# max_loop: 5  # Optional: limit number of loops for testing
```

### `secrets.yaml`

Store your API credentials:

```yaml
API_KEY: "your-idfm-api-key"
MQTT_HOST: "mqtt-broker-host"
MQTT_PORT: 1883
MQTT_USERNAME: "username"  # Optional
MQTT_PASSWORD: "password"  # Optional
```

## Usage

### Run Directly

```bash
python -m transportation_monitoring.stops_query_loop
```

### Run with Docker

```bash
docker compose -f docker/docker-compose.yml up
```

## Project Structure

```
transportation_monitoring/
├── transportation_monitoring.py      # Main IDFM API client
├── extract_next_passages.py         # Data parsing and extraction
├── publish_passages.py              # MQTT publishing logic
├── stops_query_loop.py              # Main monitoring loop
├── data_explorer.py                 # YAML configuration loader
├── arrets-lignes.json               # Stops reference data
└── referentiel-des-lignes.json      # Lines reference data
docker/
├── Dockerfile                       # Docker image definition
├── docker-compose.yml               # Docker Compose configuration
└── requirements.txt                 # Docker dependencies
tests/
├── test_monitoring_next_passages.py # Unit tests
└── conftest.py                      # Pytest configuration
```

## Dependencies

### Core Dependencies
- `pyyaml>=6.0.3` - YAML configuration parsing
- `paho-mqtt>=2.1.0` - MQTT client for message publishing
- `requests>=2.32.5` - HTTP library for API calls

### Development Dependencies
- `pytest>=7.4` - Testing framework
- `pytest-cov>=3.0` - Code coverage reporting

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=transportation_monitoring
```

## Mock Display Development

For Adafruit product `4800`, the current hardware is the **MagTag 2.9" grayscale e-ink display** with a `296x128` screen. This repository now includes a pure-Python mock renderer that generates PNG images matching that target resolution, which makes it possible to iterate on layout without the real hardware.

### Display configuration example

Create a dedicated file such as `display_config.yaml`:

```yaml
max_entries_per_stop: 3
stops:
  - monitoring_ref: "STIF:StopPoint:Q:41855:"
    label: "Division Leclerc"
    lines: ["189", "190"]
```

### Example usage

```python
from transportation_monitoring.display_config import load_display_config
from transportation_monitoring.display_models import build_display_state
from transportation_monitoring.mock_display import MockPngDisplay

config = load_display_config("display_config.yaml")
state = build_display_state(
    passages=next_passages,
    selections=config.selections,
    max_entries_per_stop=config.max_entries_per_stop,
)

MockPngDisplay().save_png(state, "mock_screen.png")
```

The generated `mock_screen.png` can be opened directly and used as a visual snapshot during tests.

Example PNGs can be generated explicitly into `artifacts/` with:

```bash
py -3.12 -m transportation_monitoring.generate_artifacts
```

This command is manual on purpose: the committed sample images live in `artifacts/`, but the test suite does not generate them automatically.

The current layout keeps only the update time in the header. There is no global title and no footer line, and each stop can show up to 3 upcoming passages across the allowed lines for that stop.

## MQTT Display Pipeline

For the Raspberry Pi + Docker publisher and the CircuitPython display, the recommended flow is:

- the Raspberry Pi fetches IDFM data periodically
- it publishes a single MQTT snapshot on `<base_topic>/snapshot`
- the MagTag subscribes to that topic and rebuilds the whole display state from the payload
- the CircuitPython backend then applies only the changed regions when possible

### Snapshot payload shape

```json
{
  "generated_at": "2026-04-14T08:12:00+02:00",
  "passages": [
    {
      "monitoring_ref": "STIF:StopPoint:Q:41855:",
      "stop_name": "Division Leclerc",
      "line": "189",
      "destination": "Clamart Centre",
      "direction": "Clamart",
      "status": "onTime",
      "waiting_seconds": 180
    }
  ]
}
```

### Raspberry Pi publisher

The server-side loop now publishes a snapshot with `publish_display_snapshot(...)`.

### CircuitPython side

Use `CircuitPythonMQTTDisplayController` to:

- subscribe to `<base_topic>/snapshot`
- parse incoming snapshots
- build a `TransitDisplayState`
- send it to `CircuitPythonMagTagBackend`

The included backend skeleton is desktop-testable with `InMemoryCircuitPythonView`, and can later be mapped to real `displayio` labels on the MagTag.

## Display Backend Strategy

The display stack is separated into:

- a pure state builder in `display_models.py`
- an update planner in `display_backends.py`
- a PNG mock backend in `mock_display.py`
- a CircuitPython-oriented backend skeleton that prefers partial updates and only falls back to periodic full refreshes for e-ink cleanup

This keeps the mock simple while avoiding a design that assumes a full screen refresh on every change for the real device.

## API Reference

### IDFM API

The project uses the IDFM PRIM API for accessing real-time transportation data:
- **Endpoint**: `https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring`
- **Authentication**: API key required
- **Response Format**: JSON

Each passage contains:
- `line` - Transport line number/name
- `direction` - Destination direction
- `destination` - Final destination
- `vehicle` - Vehicle identifier
- `expected_arrival` - Estimated arrival time (ISO8601)
- `expected_departure` - Estimated departure time (ISO8601)
- `departure_status` - Status (onTime, delayed, cancelled, etc.)
- `stop_name` - Stop name

## Troubleshooting

### API Authentication Errors
- Verify your API key is correct in `secrets.yaml`
- Check that your IDFM API key has the necessary permissions

### Connection Issues
- Ensure MQTT broker is accessible (if using MQTT publishing)
- Check network connectivity to the IDFM API endpoint

### No Data Returned
- Verify stop identifiers are valid in `stops_monitoring.yaml`
- Check the IDFM PRIM API is operational

## License

License information not currently specified. See `LICENSE` file for details.

## Author

Guillaume PICHON <gupichon@gmail.com>

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Home Assistant Integration

This project is designed to work with Home Assistant's MQTT integration. Configure your Home Assistant instance to subscribe to the published MQTT topics for real-time transportation updates.
