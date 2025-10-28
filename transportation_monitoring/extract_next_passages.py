from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def _parse_iso_utc(s: str | None) -> datetime | None:
    """Accepte les timestamps ISO8601 de SIRI (souvent suffixés 'Z') et renvoie un datetime UTC."""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)

def extract_next_passages(
    siri_json: dict,
    tz: str = "Europe/Paris",
    line_map: dict[str, str] | None = None,
) -> list[dict]:
    """
    Transforme la réponse SIRI-Lite StopMonitoring en une liste de passages lisibles.

    Retourne une liste de dicts triée par heure locale croissante, avec les clés :
      - line      : '189', '190', etc. (dérivé de PublishedLineName si présent, sinon LineRef + line_map)
      - direction : texte (DirectionName)
      - destination: texte (DestinationName / DestinationDisplay)
      - stop_name : nom d’arrêt (StopPointName)
      - when_local: datetime en timezone Europe/Paris (ExpectedDepartureTime/ArrivalTime)
      - status    : statut ('onTime', 'delayed', etc.)
      - raw_line_ref: identifiant ligne SIRI ('STIF:Line::C01210:' ...)
      - monitoring_ref: identifiant du quai ('STIF:StopPoint:Q:...:')

    line_map : permet d’écraser le mapping LineRef → numéro (ex. {'STIF:Line::C01210:': '189'})
    """
    if line_map is None:
        # D’après ton cas : C01210 = 189, C01211 = 190
        line_map = {"STIF:Line::C01210:": "189", "STIF:Line::C01211:": "190"}

    tzinfo = ZoneInfo(tz)

    deliveries = (
        siri_json.get("Siri", {})
        .get("ServiceDelivery", {})
        .get("StopMonitoringDelivery", [])
    )
    response_timestamp = siri_json.get("Siri", {}).get("ServiceDelivery", {}).get("ResponseTimestamp", None)
    response_time_utc = _parse_iso_utc(response_timestamp)
    response_time_local = response_time_utc.astimezone(tzinfo) if response_time_utc else None
    print(response_time_utc)
    print(response_time_local)

    results: list[dict] = []
    for delivery in deliveries:
        visits = delivery.get("MonitoredStopVisit", []) or []
        for mv in visits:
            mvj = mv.get("MonitoredVehicleJourney", {}) or {}
            call = mv.get("MonitoredCall", {}) or mvj.get("MonitoredCall", {}) or {}
            onward0 = (
                (mvj.get("OnwardCalls") or {}).get("OnwardCall", [{}]) or [{}]
            )[0]

            # Heures: priorité au départ, sinon arrivée, avec repli sur aimed
            dep = call.get("ExpectedDepartureTime") or call.get("AimedDepartureTime")
            arr = call.get("ExpectedArrivalTime") or call.get("AimedArrivalTime")
            when_utc = _parse_iso_utc(dep or arr)

            # Texte utilitaires
            def _first_text(x):
                # SIRI peut fournir des listes d’objets [{'value': '...'}]
                if isinstance(x, list) and x:
                    v = x[0]
                    if isinstance(v, dict) and "value" in v:
                        return v["value"]
                    return str(v)
                if isinstance(x, dict) and "value" in x:
                    return x["value"]
                return x

            line_ref = _first_text(mvj.get("LineRef"))
            line_num = None
            # PublishedLineName peut contenir le numéro lisible (si présent)
            published = _first_text(mvj.get("PublishedLineName"))
            if published:
                line_num = str(published)
            elif line_ref and line_ref in line_map:
                line_num = line_map[line_ref]
            else:
                # repli: extrait éventuel code 'C01210' → 'C01210'
                if isinstance(line_ref, str) and ":Line::" in line_ref:
                    line_num = line_ref.split(":Line::", 1)[1].strip(":")
                else:
                    line_num = str(line_ref)

            direction = _first_text(mvj.get("DirectionName"))
            destination = (
                _first_text(mvj.get("DestinationName"))
                or _first_text(call.get("DestinationDisplay"))
                or _first_text(mvj.get("DestinationShortName"))
            )
            stop_name = (
                _first_text(call.get("StopPointName"))
                or _first_text(mvj.get("MonitoredCall", {}).get("StopPointName"))
            )
            status = call.get("DepartureStatus") or call.get("ArrivalStatus")

            if when_utc is None:
                # repli sur OnwardCall si jamais
                when_utc = _parse_iso_utc(
                    onward0.get("ExpectedDepartureTime")
                    or onward0.get("AimedDepartureTime")
                    or onward0.get("ExpectedArrivalTime")
                    or onward0.get("AimedArrivalTime")
                )

            when_local = when_utc.astimezone(tzinfo) if when_utc else None
            waiting_time = when_local-response_time_local

            results.append(
                {
                    "line": line_num,
                    "raw_line_ref": line_ref,
                    "direction": direction,
                    "destination": destination,
                    "stop_name": stop_name,
                    "when_local": when_local,
                    "waiting_time": waiting_time,
                    "status": status,
                    "monitoring_ref": _first_text(mv.get("MonitoringRef")),
                }
            )

    # Tri par heure locale
    results = [r for r in results if r["when_local"] is not None]
    results.sort(key=lambda r: r["when_local"])
    return results

def _fmt(dt):
    if dt is None:
        return "—"
    if isinstance(dt, timedelta):
        total_seconds = int(dt.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours < 0:
            return "On approach"
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if isinstance(dt, datetime):
        return dt.strftime("%H:%M:%S")
    raise TypeError(f"Unsupported type: {type(dt)}")

def print_passages_table(passages: list[dict]):
    if not passages:
        print("Aucun passage trouvé.")
        return

    print(f"{'Ligne':>5}  {'Départ (local)':>14}  {'Destination':<30}  {'Statut':<10}  Arrêt")
    print("-" * 90)
    for r in passages:
        print(
            f"{r['line']:>5}  {_fmt(r['waiting_time']):>14}  {str(r['destination'] or ''):<30}  "
            f"{str(r['status'] or ''):<10}  {r['stop_name'] or ''}"
        )
