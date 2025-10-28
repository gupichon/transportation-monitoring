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
) -> list[dict]:
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
    next_passages = extract_next_passages(data)
    print(next_passages)
    print_passages_table(next_passages)
    siri = data.get("Siri", {}).get("ServiceDelivery", {})
    deliveries = siri.get("StopMonitoringDelivery", [])
    visits_out = []

    for delivery in deliveries:
        for mv in delivery.get("MonitoredStopVisit", []) or []:
            mvj = mv.get("MonitoredVehicleJourney", {}) or {}
            call = mv.get("MonitoredCall", {}) or (mvj.get("OnwardCalls", {}).get("OnwardCall", [{}])[0])

            visits_out.append({
                "line": mvj.get("LineRef"),
                "direction": mvj.get("DirectionRef"),
                "destination": (mvj.get("DestinationName") or mvj.get("PublishedLineName")),
                "vehicle": mvj.get("VehicleRef"),
                "expected_arrival": call.get("ExpectedArrivalTime") or call.get("AimedArrivalTime"),
                "expected_departure": call.get("ExpectedDepartureTime") or call.get("AimedDepartureTime"),
                "departure_status": call.get("DepartureStatus"),
                "stop_name": call.get("StopPointName") or mvj.get("MonitoredCall", {}).get("StopPointName"),
            })

    return visits_out
