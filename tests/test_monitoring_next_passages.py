import pytest

from transportation_monitoring.transportation_monitoring import idfm_next_passages
from transportation_monitoring.extract_next_passages import *


@pytest.mark.parametrize("monitoring_ref", [
    "STIF:StopPoint:Q:41855:",
    "STIF:StopPoint:Q:12406:",
])
def test_next_passages(api_key,monitoring_ref):
    stops = idfm_next_passages(api_key, monitoring_ref)
    res = extract_next_passages(stops)
    print_passages_table(res)
    #print(res)


@pytest.mark.parametrize(("city", "stop_names"), [
    ("Clamart", ["Cimeti\u00e8re", "Cimeti\u00e8re de Clamart"]),
    ("Ch\u00e2tillon", ["Division Leclerc"]),
    ("Fontenay-aux-Roses", ["Division Leclerc"]),
])
def test_json_stops_explore(city, stop_names):
    json_data = jload("transportation_monitoring/arrets-lignes.json")
    matching_stops = []
    for stop in json_data:
        commune:str = get(stop, "nom_commune")
        name:str = get(stop, "stop_name")
        stop_id:str = get(stop, "stop_id")
        id:str = get(stop, "id")
        if commune == city and name in stop_names:
            matching_stops.append(stop)
    assert len(matching_stops)>0

    for stop in matching_stops:
        print(stop)


@pytest.mark.parametrize("wanted_line_name", [
    "189", "190",
])
def test_json_lines_explore(wanted_line_name:str):
    json_data = jload("transportation_monitoring/referentiel-des-lignes.json")
    for line in json_data:
        short_name:str = get(line, "shortname_line")
        if short_name == wanted_line_name:
            print(line)
