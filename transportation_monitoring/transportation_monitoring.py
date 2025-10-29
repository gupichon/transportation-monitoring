import requests
from .extract_next_passages import *

class IDFMError(Exception):
    pass

def _strip_nones(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}

def idfm_next_passages(
    api_key: str,
    monitoring_ref: str,
    line_ref: str | None = None,
    maximum_stop_visits: int = 6,
    language: str = "fr",
    timeout: float = 10.0,
) -> dict:
    """
    Retourne une liste de passages temps réel pour un StopPoint (quai) IDFM.

    Chaque item contient:
      - line (str)
      - direction (str|None)
      - destination (str|None)
      - vehicle (str|None)
      - expected_arrival (str|None, ISO8601)
      - expected_departure (str|None, ISO8601)
      - departure_status (str|None)  # onTime, delayed, cancelled, etc.
      - stop_name (str|None)
    """
    base_url = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
    params = {
        "MonitoringRef": monitoring_ref,
        #"MaximumStopVisits": maximum_stop_visits,
    }
    if line_ref:
        params["LineRef"] = line_ref

    headers = {
        "Accept": "application/json",
        "Accept-Language": language,
        "apikey": api_key,
    }

    resp = requests.get(base_url, params=params, headers=headers, timeout=timeout)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise IDFMError(f"HTTP {resp.status_code}: {resp.text}") from e

    data = resp.json()
    return data
