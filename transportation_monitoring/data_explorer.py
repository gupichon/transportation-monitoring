import json
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


def resolve_path(filename: str | Path) -> Path:
    path = Path(filename)
    candidates = []

    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.extend(
            [
                Path.cwd() / path,
                PROJECT_ROOT / path,
                PACKAGE_DIR / path,
                PACKAGE_DIR / path.name,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def jload(filename: str):
    with resolve_path(filename).open("r", encoding="utf-8") as file:
        return json.load(file)

def yload(filename: str) -> Any:
    path = resolve_path(filename)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get(d: dict, path: str, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

