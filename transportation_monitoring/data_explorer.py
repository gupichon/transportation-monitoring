import json

def jload(filename: str):
    with open(filename) as file:
        return json.load(file)


def get(d: dict, path: str, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


