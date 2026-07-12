import os
import time
from datetime import datetime, timezone

from sources import fetch_all_sources, fetch_crypto_move
from classify import process_items
from charts import generate_crypto_chart
from telegram_bot import post_item
from state import (
    load_sent_ids, save_sent_ids, filter_new,
    load_queue, save_queue, enqueue, drop_stale,
)
from config import QUEUE_DRAIN_MAX, QUEUE_DRAIN_INTERVAL_SECONDS

HEARTBEAT_FILE = os.path.join(os.path.dirname(__file__), "last_run.txt")


def write_heartbeat():
    """Touch a timestamp file every run so the workflow always has something to
    commit — this keeps the repo 'active' and stops GitHub from auto-disabling
    the scheduled trigger after 60 days of no repository activity."""
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat() + "\n")


def _maybe_attach_chart(item, attach_chart_once):
    """Unchanged from the original script: attach a BTC candlestick chart at
    most once per run, only to a CRYPTO item, when BTC has moved >=2% in 24h."""
    if attach_chart_once and item["category"] == "CRYPTO":
        try:
            return generate_crypto_chart("BTCUSDT"), False
        except Exception as e:
            print(f"[main] chart generation failed: {e}")
            return None, False
    return None, attach_chart_once


def main():
    sent_ids = load_sent_ids()
    queue = load_queue()

    raw_items = fetch_all_sources()
    print(f"[main] fetched {len(raw_items)} raw items")

    new_items = filter_new(raw_items, sent_ids)
    print(f"[main] {len(new_items)} new after dedupe")

    processed = process_items(new_items)

    btc_move = fetch_crypto_move("BTCUSDT")
    attach_chart_once = abs(btc_move) >= 2.0  # >=2% move in 24h -> worth a chart

    # ── Step 1: route every fetched item — identically, no source special-
    # casing (including Trump's posts). Keyword match -> post immediately,
    # no delay/queue/pacing, bypasses everything else. No match -> queue.
    queued_count = 0
    for item in processed:
        if item.get("routing_match"):
            photo_path, attach_chart_once = _maybe_attach_chart(item, attach_chart_once)
            ok = post_item(item, photo_path=photo_path)
            if ok:
                sent_ids.add(item["_hash"])
            else:
                print(f"[main] immediate post failed, will retry next run: {item['title'][:80]}")
        else:
            enqueue(queue, item)
            # Mark seen now (not just on eventual post) so the next run's
            # fetch doesn't re-discover the same still-queued item from its
            # source feed and append a duplicate copy — see state.py note.
            sent_ids.add(item["_hash"])
            queued_count += 1
    print(f"[main] {queued_count} items added to queue (not keyword-matched)")

    # ── Step 2: drain the queue — oldest first, up to QUEUE_DRAIN_MAX items,
    # spaced QUEUE_DRAIN_INTERVAL_SECONDS apart. Drop anything older than
    # QUEUE_MAX_AGE_HOURS instead of posting it late.
    queue, dropped = drop_stale(queue)
    if dropped:
        print(f"[main] dropped {dropped} stale queued item(s) (>8h old)")

    queue.sort(key=lambda q: q.get("queued_at", 0))
    to_drain = queue[:QUEUE_DRAIN_MAX]
    remaining = queue[QUEUE_DRAIN_MAX:]

    for i, entry in enumerate(to_drain):
        item = entry["item"]
        photo_path, attach_chart_once = _maybe_attach_chart(item, attach_chart_once)
        ok = post_item(item, photo_path=photo_path)
        if not ok:
            print(f"[main] drained post failed, leaving in queue for retry: {item['title'][:80]}")
            remaining.append(entry)  # keep it — bounded by the 8h expiry above
        if i < len(to_drain) - 1:
            time.sleep(QUEUE_DRAIN_INTERVAL_SECONDS)

    save_queue(remaining)
    print(f"[main] drained {len(to_drain)} queued item(s), {len(remaining)} remain queued")

    save_sent_ids(sent_ids)
    write_heartbeat()
    print("[main] done")


if __name__ == "__main__":
    main()
