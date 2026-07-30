import argparse
from datetime import datetime
from time import sleep
from zoneinfo import ZoneInfo

from transportation_monitoring import secrets, MONITORING_FILE
from transportation_monitoring.publish_passages import publish_display_snapshot
from .data_explorer import yload
from .extract_next_passages import extract_next_passages, print_passages_table
from .transportation_monitoring import idfm_next_passages
from .monitoring_schedule import daily_call_count, interval_for, next_run_after


def get_api_key() -> str:
    return secrets["API_KEY"]


def query_stops(api_key: str, stops: list[str]) -> list[dict] | None:
    passages: list[dict] = []
    for monitoring_ref in stops:
        try:
            response = idfm_next_passages(api_key, monitoring_ref)
            passages.extend(extract_next_passages(response))
        except Exception as exc:
            print(f"IDFM query failed for {monitoring_ref}: {exc}")
            return None
    return passages


def run_once() -> bool:
    config = yload(MONITORING_FILE)
    passages = query_stops(get_api_key(), config["stops"])
    if passages is None:
        print("Incomplete IDFM cycle: snapshot not published.")
        return False
    print_passages_table(passages)
    publish_display_snapshot(passages)
    return True


def stops_query_loop(now_provider=None, sleep_fn=sleep):
    api_key = get_api_key()
    stops_monitoring = yload(MONITORING_FILE)
    stops = stops_monitoring["stops"]
    timezone = stops_monitoring.get("timezone", "Europe/Paris")
    tz = ZoneInfo(timezone)
    schedule = stops_monitoring["schedule"]
    max_loop = stops_monitoring.get("max_loop")
    now_provider = now_provider or (lambda: datetime.now(tz))
    print(f"Configured IDFM calls per day: {daily_call_count(schedule, len(stops))}")
    loop_count = 0
    while True:
        now = now_provider()
        if interval_for(now, schedule) is None:
            sleep_fn(max(0.0, (next_run_after(now, schedule, timezone) - now).total_seconds()))
            continue

        loop_count += 1
        next_passages = query_stops(api_key, stops)
        if next_passages is not None:
            print_passages_table(next_passages)
            publish_display_snapshot(next_passages)
        else:
            print("Incomplete IDFM cycle: snapshot not published.")
        if max_loop is not None and loop_count >= max_loop:
            print(f"Max loop count ({max_loop}) reached. Exiting.")
            break
        now = now_provider()
        sleep_fn(max(0.0, (next_run_after(now, schedule, timezone) - now).total_seconds()))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Monitor IDFM stops and publish MQTT snapshots.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one complete cycle immediately, ignoring the daily schedule.",
    )
    args = parser.parse_args(argv)
    if args.once:
        raise SystemExit(0 if run_once() else 1)
    stops_query_loop()

if __name__ == "__main__":
    main()
