from sources import fetch_all_sources, fetch_crypto_move
from classify import process_items
from charts import generate_crypto_chart
from telegram_bot import post_item
from state import load_sent_ids, save_sent_ids, filter_new
from config import MAX_POSTS_PER_RUN


def main():
    sent_ids = load_sent_ids()

    raw_items = fetch_all_sources()
    print(f"[main] fetched {len(raw_items)} raw items")

    new_items = filter_new(raw_items, sent_ids)
    print(f"[main] {len(new_items)} new after dedupe")

    processed = process_items(new_items)
    to_post = processed[:MAX_POSTS_PER_RUN]

    # attach a candlestick chart once per run if BTC has moved sharply
    # and a crypto item is going out — mirrors the LMWM "chart + JUST IN" style
    btc_move = fetch_crypto_move("BTCUSDT")
    attach_chart_once = abs(btc_move) >= 2.0  # >=2% move in 24h -> worth a chart

    for item in to_post:
        photo_path = None
        if attach_chart_once and item["category"] == "CRYPTO":
            try:
                photo_path = generate_crypto_chart("BTCUSDT")
            except Exception as e:
                print(f"[main] chart generation failed: {e}")
            attach_chart_once = False  # only once per run

        ok = post_item(item, photo_path=photo_path)
        if ok:
            sent_ids.add(item["_hash"])

    save_sent_ids(sent_ids)
    print("[main] done")


if __name__ == "__main__":
    main()
