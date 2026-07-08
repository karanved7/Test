#!/usr/bin/env python3
"""Watch the calls Google Sheet and detect scrip trigger events.

Two markets, two tabs in the same spreadsheet:

  * india  - "Shortlisted_Stocks" (NSE calls; the spreadsheet's first tab)
  * us     - "GLOBAL EQUITY_calls" (US stocks / ETFs)

The sheet is link-shared, so it can be fetched as CSV with no credentials.
Each call row is evaluated against its levels:

  * ENTRY ZONE / BUY  - current price <= entry price
  * STOP LOSS  / SELL - current price <= stop loss
  * TARGET HIT / SELL - current price >= target

US events are reported with BUY/SELL wording. Already-alerted events are
remembered in a state file so each (market, scrip, call date, condition)
alerts only once. On the very first run for a market, rows older than
BASELINE_DAYS are baselined silently so history doesn't flood alerts.

Usage:
    python3 check_triggers.py --state state.json \
        [--out alerts.md] [--out-us us_alerts.md] [--print]

--out receives India alerts (markdown), --out-us receives US alerts
(markdown plus a us_alerts.json next to it for the email webhook).
"""

import argparse
import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SHEET_ID = "1v1d2bcNRR6oqWktjCv6lw61PerOoun1J83h9Jl5hLi8"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
BASELINE_DAYS = 14  # on a market's first run, only calls newer than this may alert

MARKETS = {
    "india": {
        "csv": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv",
        # DATE, Scrip, Current Price, Target, Entry, SL column indexes
        "cols": {"date": 0, "scrip": 3, "price": 7, "target": 8, "entry": 9, "sl": 10},
        "labels": {"entry": "ENTRY ZONE", "sl": "STOP LOSS", "target": "TARGET HIT"},
    },
    "us": {
        "csv": (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
                "/gviz/tq?tqx=out:csv&sheet=GLOBAL%20EQUITY_calls"),
        "cols": {"date": 0, "scrip": 1, "price": 9, "target": 10, "entry": 11, "sl": 12},
        "labels": {"entry": "BUY (entry zone)", "sl": "SELL (stop loss)",
                   "target": "SELL (target hit)"},
    },
}


def to_float(cell):
    cell = (cell or "").strip().replace(",", "")
    if not cell or cell.startswith("#"):
        return None
    try:
        return float(cell)
    except ValueError:
        return None


def parse_date(cell):
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cell.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fetch_rows(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(text)))


def evaluate(market):
    """Return currently-true trigger events for one market's tab."""
    cfg = MARKETS[market]
    c = cfg["cols"]
    labels = cfg["labels"]
    events = []
    for row in fetch_rows(cfg["csv"]):
        if len(row) <= max(c.values()):
            continue
        scrip = row[c["scrip"]].strip()
        price = to_float(row[c["price"]])
        if not scrip or scrip.lower() == "scrip" or price is None:
            continue
        date = row[c["date"]].strip()
        target = to_float(row[c["target"]])
        entry = to_float(row[c["entry"]])
        sl = to_float(row[c["sl"]])

        checks = [
            (labels["sl"], sl is not None and price <= sl,
             f"price {price:g} <= stop loss {sl:g}" if sl is not None else ""),
            (labels["entry"], entry is not None and price <= entry,
             f"price {price:g} <= entry {entry:g}" if entry is not None else ""),
            (labels["target"], target is not None and price >= target,
             f"price {price:g} >= target {target:g}" if target is not None else ""),
        ]
        for cond, hit, detail in checks:
            if hit:
                events.append({
                    "key": f"{market}|{scrip.upper()}|{date}|{cond}",
                    "market": market,
                    "scrip": scrip.upper(),
                    "call_date": date,
                    "condition": cond,
                    "detail": detail,
                })
    return events


def write_markdown(path, title, alerts):
    lines = [f"## {title}", "",
             "| Scrip | Signal | Detail | Call date |", "|---|---|---|---|"]
    lines += [f"| **{e['scrip']}** | {e['condition']} | {e['detail']} | {e['call_date']} |"
              for e in alerts]
    lines += ["", f"[Open the sheet]({SHEET_URL})"]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--out", help="markdown output for new India alerts")
    ap.add_argument("--out-us", help="markdown output for new US alerts "
                                     "(also writes <same path>.json)")
    ap.add_argument("--print", dest="do_print", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=BASELINE_DAYS)

    try:
        with open(args.state) as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"alerted": {}}
    state.setdefault("seen_markets", [])

    new_by_market = {"india": [], "us": []}
    totals = {}
    for market in MARKETS:
        events = evaluate(market)
        totals[market] = len(events)
        first_run = market not in state["seen_markets"]
        # india predates market prefixes in state keys; honour old entries
        legacy = market == "india"
        for e in events:
            old_key = e["key"].split("|", 1)[1] if legacy else None
            if e["key"] in state["alerted"] or (old_key and old_key in state["alerted"]):
                continue
            call_dt = parse_date(e["call_date"])
            if first_run and (call_dt is None or call_dt < cutoff):
                state["alerted"][e["key"]] = {"baselined": now.isoformat()}
                continue
            state["alerted"][e["key"]] = {"alerted": now.isoformat()}
            new_by_market[market].append(e)
        if first_run:
            state["seen_markets"].append(market)
        if args.do_print:
            for e in events:
                print(f"[{market:>5}] {e['condition']:<18} {e['scrip']:<12}"
                      f" (call {e['call_date']}): {e['detail']}")

    with open(args.state, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)

    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    if new_by_market["india"] and args.out:
        write_markdown(args.out, f"India scrip triggers at {stamp}",
                       new_by_market["india"])
    if new_by_market["us"] and args.out_us:
        write_markdown(args.out_us, f"US stock signals at {stamp}",
                       new_by_market["us"])
        with open(args.out_us + ".json", "w") as f:
            json.dump({
                "subject": "US Stock Alert: " + ", ".join(
                    f"{e['scrip']} {e['condition'].split(' ')[0]}"
                    for e in new_by_market["us"][:6]),
                "text": "\n".join(
                    f"{e['condition']}: {e['scrip']} — {e['detail']}"
                    f" (call dated {e['call_date']})"
                    for e in new_by_market["us"]
                ) + f"\n\nSheet: {SHEET_URL}",
                "alerts": new_by_market["us"],
            }, f, indent=2)

    print(f"India: {len(new_by_market['india'])} new / {totals['india']} true. "
          f"US: {len(new_by_market['us'])} new / {totals['us']} true.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
