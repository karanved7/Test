# Test

## Scrip trigger alerts (real-time sheet monitor)

Monitors the [NSE calls Google Sheet](https://docs.google.com/spreadsheets/d/1v1d2bcNRR6oqWktjCv6lw61PerOoun1J83h9Jl5hLi8/edit)
and raises an alert whenever a scrip triggers one of its levels:

| Condition | Rule |
|---|---|
| ENTRY ZONE | current price ≤ entry price |
| STOP LOSS | current price ≤ stop loss |
| TARGET HIT | current price ≥ target |

### How it works

- `.github/workflows/scrip-alerts.yml` runs every 10 minutes during NSE market
  hours (09:15–15:30 IST, Mon–Fri). It can also be run manually from the
  Actions tab ("Run workflow").
- `monitor/check_triggers.py` fetches the sheet as CSV (the sheet is
  link-shared, so no Google credentials are needed), evaluates every call row,
  and diffs against `monitor/state.json` so each (scrip, call date, condition)
  alerts exactly once.
- New triggers open a **GitHub issue** in this repo titled `🔔 Scrip trigger: …`
  — watch the repo (Watch → All activity) to get these as email/push
  notifications.
- On the very first run, historical rows (call date older than 14 days) are
  baselined silently so years-old triggers don't flood the issue tracker.

### Run locally

```bash
python3 monitor/check_triggers.py --state monitor/state.json --print
```

`--print` lists every condition currently true, regardless of alert state.

### Notes on latency

"Real time" here means: sheet prices come from GOOGLEFINANCE (NSE quotes are
delayed ~15 min) and the workflow polls every ~10 min, so expect alerts within
roughly 10–25 minutes of a level being crossed. GitHub schedule runs only
activate once this workflow is on the default branch (`main`).
