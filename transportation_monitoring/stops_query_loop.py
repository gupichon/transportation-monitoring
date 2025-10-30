from time import sleep

from .data_explorer import yload
from .extract_next_passages import extract_next_passages, print_passages_table
from .transportation_monitoring import idfm_next_passages

SECRETS_FILE = "secrets.yaml"
MONITORING_FILE = "stops_monitoring.yaml"

def get_api_key() -> str:
    secrets = yload(SECRETS_FILE)
    return secrets["API_KEY"]

def stops_query_loop():
    api_key = get_api_key()
    stops_monitoring = yload(MONITORING_FILE)
    stops = stops_monitoring["stops"]
    sleeping_time = stops_monitoring["sleeping_time"]
    max_loop = stops_monitoring.get("max_loop")
    loop_count = 0
    while True:
        loop_count += 1
        next_passages:list[dict] = []
        for monitoring_ref in stops:
            next_passages_for_stop = idfm_next_passages(api_key, monitoring_ref)
            res = extract_next_passages(next_passages_for_stop)
            next_passages.extend(res)
        print_passages_table(next_passages)
        if max_loop is not None and loop_count >= max_loop:
            print(f"Max loop count ({max_loop}) reached. Exiting.")
            break
        sleep(sleeping_time)

def main():
    stops_query_loop()

if __name__ == "__main__":
    main()