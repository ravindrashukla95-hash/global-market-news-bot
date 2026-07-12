import json
import hashlib
import os
import time

from config import QUEUE_FILE, QUEUE_MAX_AGE_HOURS

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")


def _hash_item(item):
    key = (item.get("link") or item["title"]).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


# ── "Already posted" dedup — UNCHANGED from the original script ──────────
#
# IMPORTANT (flagged per the task): sent_ids is no longer strictly "already
# POSTED to Telegram". main.py now also adds an item's hash here the moment
# it's added to the queue (not yet posted), so it's really "already seen —
# either posted or queued". This was required to slot the new queue in
# alongside dedup without conflict: filter_new() below only excludes items
# whose hash is already in sent_ids, and RSS feeds keep re-serving their last
# N entries on every poll. Without marking queued items as seen immediately,
# every 10-minute run would re-discover the same still-queued item and
# append a second (third, fourth...) copy of it to queue.json before it
# ever got drained. Marking it seen at queue-time closes that gap, at the
# cost of the sent_ids name being slightly misleading now — consider
# renaming to seen_ids in a follow-up if this trips anyone up.
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


# ── Persistent queue — NEW, sits alongside the dedup logic above ─────────
# Holds non-keyword-matching items between runs so they can be drained a
# few at a time, one minute apart, instead of posted in a burst.

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)


def enqueue(queue, item):
    """Append an item to the queue with a queued_at timestamp (epoch
    seconds) — this timestamp, not the item's original publish time, is
    what the 8-hour staleness rule below is measured against."""
    queue.append({
        "hash": item["_hash"],
        "queued_at": time.time(),
        "item": item,
    })
    return queue


def drop_stale(queue, max_age_hours=None):
    """Drop items that have been sitting in the queue longer than
    QUEUE_MAX_AGE_HOURS instead of posting them late. Returns
    (fresh_queue, dropped_count)."""
    max_age_hours = QUEUE_MAX_AGE_HOURS if max_age_hours is None else max_age_hours
    cutoff = time.time() - (max_age_hours * 3600)
    fresh = [q for q in queue if q.get("queued_at", 0) >= cutoff]
    dropped = len(queue) - len(fresh)
    return fresh, dropped
