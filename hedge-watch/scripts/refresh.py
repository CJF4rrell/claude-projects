#!/usr/bin/env python3
"""
Daily refresh for the Hedge Watch FX/crypto tracker.

Reads hedge-watch/data/fx-data.json, fetches any missing business days
(prior day's close-of-business rates) from Frankfurter (ECB) for fiat
and Kraken for BTC/ETH, appends them, and writes the file back in place.
Designed to be idempotent: if the dataset is already current, it exits
without changing anything.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "fx-data.json"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hedge-watch-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    data = json.loads(DATA_PATH.read_text())
    if not data:
        print("Dataset is empty — refusing to guess a start date. Aborting.")
        sys.exit(1)

    last_date = max(row["date"] for row in data)
    last_dt = datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    start_dt = last_dt + timedelta(days=1)
    if start_dt > yesterday:
        print(f"Already current (last date {last_date}); nothing to do.")
        return

    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = yesterday.strftime("%Y-%m-%d")
    print(f"Fetching {start_date}..{end_date}")

    # --- Fiat rates (Frankfurter / ECB reference rates), EUR base ---
    fiat_url = (
        f"https://api.frankfurter.dev/v1/{start_date}..{end_date}"
        f"?from=EUR&to=USD,GBP,JPY,CHF"
    )
    fiat = fetch_json(fiat_url)
    fiat_rates = fiat.get("rates", {})
    if not fiat_rates:
        print("No new fiat business days in range (weekend/holiday gap); nothing to do.")
        return

    # --- Crypto (Kraken daily OHLC), USD priced ---
    since_ts = int(start_dt.timestamp())

    def kraken_closes(pair, result_key):
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440&since={since_ts}"
        payload = fetch_json(url)
        if payload.get("error"):
            raise RuntimeError(f"Kraken error for {pair}: {payload['error']}")
        rows = payload["result"][result_key]
        out = {}
        for ts, o, h, l, c, vwap, vol, count in rows:
            d = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            out[d] = round(float(c), 2)
        return out

    btc = kraken_closes("XBTUSD", "XXBTZUSD")
    eth = kraken_closes("ETHUSD", "XETHZUSD")

    existing_dates = {row["date"] for row in data}
    new_rows = []
    for date, rates in sorted(fiat_rates.items()):
        if date in existing_dates:
            continue
        if date not in btc or date not in eth:
            print(f"Skipping {date}: no matching crypto close yet")
            continue
        new_rows.append(
            {
                "date": date,
                "USD": rates["USD"],
                "GBP": rates["GBP"],
                "JPY": rates["JPY"],
                "CHF": rates["CHF"],
                "BTC": btc[date],
                "ETH": eth[date],
            }
        )

    if not new_rows:
        print("No new rows to add.")
        return

    data.extend(new_rows)
    data.sort(key=lambda r: r["date"])
    DATA_PATH.write_text(json.dumps(data, separators=(",", ":")))
    print(f"Added {len(new_rows)} row(s): {[r['date'] for r in new_rows]}")


if __name__ == "__main__":
    main()
