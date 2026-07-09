import requests
import pandas as pd
import mplfinance as mpf


def fetch_binance_klines(symbol="BTCUSDT", interval="15m", limit=50):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    raw = r.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore",
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df


def generate_crypto_chart(symbol="BTCUSDT", out_path="/tmp/chart.png"):
    df = fetch_binance_klines(symbol=symbol)
    mpf.plot(
        df, type="candle", style="nightclouds",
        title=f"{symbol}  ·  last 50 x 15m candles",
        volume=False, savefig=out_path,
    )
    return out_path


# To extend to equities/index charts, add a yfinance-based function here,
# e.g. generate_stock_chart("^NSEI") for Nifty, and call it from main.py
# the same way generate_crypto_chart() is called.
