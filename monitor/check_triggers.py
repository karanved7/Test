#!/usr/bin/env python3
"""Watch the NSE calls Google Sheet and detect scrip trigger events.

Fetches the sheet as CSV (it is link-shared, so no credentials are needed),
evaluates every call row against its levels, and reports NEW events since the
last run:

  * ENTRY ZONE   - current price <= entry price
  * STOP LOSS    - current price <= stop loss
  * TARGET HIT   - current price >= target

Already-alerted events are remembered in a state file so each (scrip, call
date, condition) alerts only once. On the very first run (no state file) old
rows are baselined silently; only calls dated within the last BASELINE_DAYS
days may alert, so the first run doesn't flood alerts for years-old history.

Usage:
    python3 check_triggers.py --state state.json --out alerts.md [--print]
"""

import argparse
import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

SHEET_ID = "1v1d2bcNRR6oqWktjCv6lw61PerOoun1J83h9Jl5hLi8"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Column indexes in the sheet
COL_DATE, COL_SCRIP, COL_PRICE, COL_TARGET, COL_ENTRY, COL_SL = 0, 3, 7, 8, 9, 10

BASELINE_DAYS = 14  # on first run, only calls newer than this may alert


def to_float(cell):
    cell = (cell or "").strip().replace(",", "")
    if not cell or cell.startswith("#"):
        return None
    try:
        return float(cell)
    except ValueError:
        return None


def parse_date(cell):
    try:
        return datetime.strptime(cell.strip(), "%d-%b-%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def fetch_rows():
    with urllib.request.urlopen(CSV_URL, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(text)))


def evaluate(rows):
    """Return a list of currently-true trigger events across all call rows."""
    events = []
    for row in rows:
        if len(row) <= COL_SL:
            continue
        scrip = row[COL_SCRIP].strip()
        price = to_float(row[COL_PRICE])
        if not scrip or scrip == "Scrip" or price is None:
            continue
        date = row[COL_DATE].strip()
        target = to_float(row[COL_TARGET])
        entry = to_float(row[COL_ENTRY])
        sl = to_float(row[COL_SL])

        checks = [
            ("STOP LOSS", sl is not None and price <= sl,
             f"price {price:g} <= stop loss {sl:g}" if sl is not None else ""),
            ("ENTRY ZONE", entry is not None and price <= entry,
             f"price {price:g} <= entry {entry:g}" if entry is not None else ""),
            ("TARGET HIT", target is not None and price >= target,
             f"price {price:g} >= target {target:g}" if target is not None else ""),
        ]
        for cond, hit, detail in checks:
            if hit:
                events.append({
                    "key": f"{scrip}|{date}|{cond}",
                    "scrip": scrip,
                    "call_date": date,
                    "condition": cond,
                    "detail": detail,
                })
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True, help="path to state JSON file")
    ap.add_argument("--out", help="write new alerts as markdown to this file")
    ap.add_argument("--print", dest="do_print", action="store_true",
                    help="print all currently-true events (ignores state)")
    args = ap.parse_args()

    rows = fetch_rows()
    events = evaluate(rows)
    now = datetime.now(timezone.utc)

    if args.do_print:
        for e in events:
            print(f"{e['condition']:>10}  {e['scrip']:<12} (call {e['call_date']}): {e['detail']}")
        print(f"\n{len(events)} condition(s) currently true.")

    try:
        with open(args.state) as f:
            state = json.load(f)
        first_run = False
    except FileNotFoundError:
        state = {"alerted": {}}
        first_run = True

    cutoff = now - timedelta(days=BASELINE_DAYS)
    new_alerts = []
    for e in events:
        if e["key"] in state["alerted"]:
            continue
        call_dt = parse_date(e["call_date"])
        if first_run and (call_dt is None or call_dt < cutoff):
            state["alerted"][e["key"]] = {"baselined": now.isoformat()}
            continue
        state["alerted"][e["key"]] = {"alerted": now.isoformat()}
        new_alerts.append(e)

    with open(args.state, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)

    if new_alerts and args.out:
        lines = [f"## Scrip triggers detected at {now.strftime('%Y-%m-%d %H:%M UTC')}", ""]
        lines += ["| Scrip | Condition | Detail | Call date |", "|---|---|---|---|"]
        lines += [f"| **{e['scrip']}** | {e['condition']} | {e['detail']} | {e['call_date']} |"
                  for e in new_alerts]
        lines += ["", f"[Open the sheet](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)"]
        with open(args.out, "w") as f:
            f.write("\n".join(lines) + "\n")

    print(f"{len(new_alerts)} new alert(s); {len(events)} condition(s) true overall."
          + (" (first run: older rows baselined)" if first_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
