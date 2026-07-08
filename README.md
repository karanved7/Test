# Test

## Scrip trigger alerts (sheet monitor)

Monitors the [calls Google Sheet](https://docs.google.com/spreadsheets/d/1v1d2bcNRR6oqWktjCv6lw61PerOoun1J83h9Jl5hLi8/edit)
and raises alerts for two markets, from two tabs of the same spreadsheet:

| Market | Sheet tab | Alert channel |
|---|---|---|
| India (NSE) | `Shortlisted_Stocks` | GitHub issue `🔔 India scrip trigger: …` |
| US stocks/ETFs | `GLOBAL EQUITY_calls` | GitHub issue `🇺🇸 US stock signal: …` **and** email to karanved7@gmail.com + radhikakhandelwal1993@gmail.com |

Trigger rules per call row:

| Condition | Rule | US wording |
|---|---|---|
| Entry zone | current price ≤ entry price | BUY |
| Stop loss | current price ≤ stop loss | SELL |
| Target hit | current price ≥ target | SELL |

### How it works

- `.github/workflows/scrip-alerts.yml` runs every 10 minutes during NSE hours
  (09:15–15:30 IST) and US market hours (09:30–16:00 ET), Mon–Fri. It can also
  be run manually from the Actions tab ("Run workflow").
- `monitor/check_triggers.py` fetches both tabs as CSV (the sheet is
  link-shared, so no Google credentials are needed), evaluates every call row,
  and diffs against `monitor/state.json` so each (market, scrip, call date,
  condition) alerts exactly once.
- US emails are sent through Gmail SMTP and require one repository secret:
  **`GMAIL_APP_PASSWORD`** — a [Google app password](https://myaccount.google.com/apppasswords)
  for karanved7@gmail.com, added under Settings → Secrets and variables →
  Actions. Until the secret exists, the email step is skipped (issues still open).
- On the first run for a market, rows older than 14 days are baselined silently
  so historical triggers don't flood alerts.

### Run locally

```bash
python3 monitor/check_triggers.py --state monitor/state.json --print
```

### Notes on latency

Sheet prices come from GOOGLEFINANCE (quotes are ~15 min delayed) and the
workflow polls every ~10 min, so expect alerts within roughly 10–25 minutes of
a level being crossed. Scheduled runs only happen from the default branch
(`main`).
