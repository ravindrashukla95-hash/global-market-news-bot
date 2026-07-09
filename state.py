import json
import hashlib
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")


def _hash_item(item):
    key = (item.get("link") or item["title"]).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def load_sent_ids():
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_sent_ids(ids, keep_last=2000):
    trimmed = list(ids)[-keep_last:]
    with open(STATE_FILE, "w") as f:
        json.dump(trimmed, f)


def filter_new(items, sent_ids):
    new_items = []
    for item in items:
        h = _hash_item(item)
        if h not in sent_ids:
            item["_hash"] = h
            new_items.append(item)
    return new_items
