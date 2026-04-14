from transportation_monitoring.data_explorer import yload
from transportation_monitoring.extract_next_passages import load_ref_lines

__version__ = "0.1.0"

SECRETS_FILE = "secrets.yaml"
MONITORING_FILE = "stops_monitoring.yaml"
try:
    secrets = yload(SECRETS_FILE)
except FileNotFoundError:
    secrets = {}

load_ref_lines()
