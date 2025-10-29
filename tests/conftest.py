import pytest
from transportation_monitoring.data_explorer import *

@pytest.fixture(autouse=True)
def api_key() -> str:
    secrets = yload("secrets.yaml")
    return secrets["API_KEY"]
