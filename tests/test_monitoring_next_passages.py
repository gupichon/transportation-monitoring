import pytest

from transportation_monitoring.transportation_monitoring import idfm_next_passages
from transportation_monitoring.extract_next_passages import *


@pytest.mark.parametrize("monitoring_ref", [
    "STIF:StopPoint:Q:463158:",
    "STIF:StopPoint:Q:12406:",
])
def test_next_passages(api_key,monitoring_ref):
    stops = idfm_next_passages(api_key, monitoring_ref)
    res = extract_next_passages(stops)
    print_passages_table(res)
    print(res)


def test_json_stops_explore():
    json_data = jload("arrets-lignes.json")
    for stop in json_data:
        commune:str = get(stop, "nom_commune")
        name:str = get(stop, "stop_name")
        stop_id:str = get(stop, "stop_id")
        id:str = get(stop, "id")
        if commune == "Clamart" and name == "Cimeti\u00e8re":
            print(stop)

@pytest.mark.parametrize("wanted_line_name", [
    "189", "190",
])
def test_json_stops_explore(wanted_line_name:str):
    json_data = jload("transportation_monitoring/referentiel-des-lignes.json")
    for line in json_data:
        short_name:str = get(line, "shortname_line")
        if short_name == wanted_line_name:
            print(line)
