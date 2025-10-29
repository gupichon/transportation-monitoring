import json
from pathlib import Path
from typing import Any

import yaml

def jload(filename: str):
    with open(filename) as file:
        return json.load(file)

def yload(filename: str) -> Any:
    path = Path(filename)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get(d: dict, path: str, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


