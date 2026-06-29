# Ekaiva US Stocks 100-EMA Tracker — Full Specification

## Overview
Real-time dashboard tracking **all Nasdaq 100 + S&P 500 stocks** (~600 stocks total). Daily and weekly 100-EMA trend analysis. Identifies stocks that **crossed above both 100-EMAs today**, **qualified stocks** (already above both), and watch lists (daily-only or weekly-only).

Runs automatically **every trading day at 4:00 PM ET (9:30 PM IST)** via GitHub Actions. Global link updates itself daily — no PC needed.

---

## Universe Definition

**Total: ~600 stocks**
- Nasdaq 100: 100 stocks
- S&P 500: 500 stocks
- Combined: all unique tickers (minor overlap deduplicated)

**Data source:** Ticker lists from:
- Nasdaq: official Nasdaq-100 components (ticker symbols)
- S&P 500: official S&P 500 components (ticker symbols)

Both lists are static and built into the script. If needed, they're updated annually (not monthly like AMFI).

---

## Core Analysis Logic

### Timeframes
- **Daily:** 0–6 score based on price vs. 5/10/20/50/100/200-day EMAs
- **Weekly:** Friday close vs. 100-week EMA (100-week moving average)

### The Four Boxes

**1. ⚡ Crossed Today (ORANGE)**
- Stocks that were NOT above both 100-EMAs yesterday
- Closed above BOTH (daily 100-EMA AND weekly 100-EMA) today
- Fresh breakouts; reset daily
- Sorted by score (6/6 first)

**2. ▲ Qualified (GREEN)**
- Currently above 100-EMA on BOTH daily AND weekly
- Established trend-followers, not fresh
- Shows the full qualified universe

**3. Daily-100 only (ORANGE watch list)**
- Above daily 100-EMA, below weekly 100-EMA
- "Building" — daily strength but weekly not yet in uptrend
- Potential candidates to join Qualified

**4. Weekly-100 only (BLUE watch list)**
- Above weekly 100-EMA, below daily 100-EMA
- "Cooling" — longer-term trend intact but daily weakness
- Potential setups if daily bounces

### Per-Stock Metrics

**Daily Score (0–6):**
Count how many of the 6 EMAs (5/10/20/50/100/200) the latest daily close is above.

**Weekly History:**
Stores the last ~2 years of Friday closes + scores + qualified flag. Accumulated in a CSV, persists forever. Click any stock to see this history in a modal popup.

**EMA Panel (Modal):**
When you click a stock, see all 6 daily EMAs with their values and Above/Below tags (green/red).

---

## Dashboard Layout

**Header:**
- Ekaiva branding
- "Market data as of [DATE] ([TIME] ET)"
- Cap toggle: All / Nasdaq-100 / S&P-500

**Tiles (5 summary boxes):**
- Crossed Today (count)
- Qualified (count)
- Daily-100 only (count)
- Weekly-100 only (count)
- Score 6/6 (count)

**Main content:**
1. **⚡ Crossed Today** box (orange header) — scrollable grid, first thing users see
2. **▲ Qualified** box (green header) — full universe
3. **Watch lists** (side-by-side, orange + blue)

**Footer:**
- Ekaiva contact: ekaivawealth.com · +91 93766 98983 · ekaivaoffice@gmail.com · ARN 305896
- Disclaimer: "Not investment advice"

---

## Data & Caching

**Source:** yfinance (Yahoo Finance) — free, no API key needed

**History:**
- Daily prices: ~5 years cached in parquet file (`prices_cache_us.parquet`)
- Weekly history: accumulated in CSV (`history_weekly_stocks_us.csv`), persists forever
- On re-run: only fetches new days, incremental update

**First run:** ~10–15 minutes (pulling ~5 years for 600 stocks, batch size 50)
**Daily run:** ~3–5 minutes (only new day)

---

## Automation

**Schedule:** Every trading day (Mon–Fri) at **4:00 PM ET (9:30 PM IST)**

**Platform:** GitHub Actions (free, runs on GitHub's servers)

**Files in repo:**
- `ekaiva_stocks_us.py` (main script)
- `prices_cache_us.parquet` (price history, updates daily)
- `history_weekly_stocks_us.csv` (weekly snapshots, persists)
- `.github/workflows/us_daily.yml` (automation trigger)

**Output:** `dashboard_stocks_us.html` (static HTML, self-contained, click-to-view)

**Link:** `https://YOURUSERNAME.github.io/stocks-us/dashboard_stocks_us.html`

---

## UI / Styling

**Palette:**
- Orange: #E8734A (Crossed Today, Daily-100 only)
- Green: #4A8C5C (Qualified, ✓ score bars)
- Cream bg: #F5F0EB
- Dark text: #2D2D2D
- Olive/brown accents: #8B7355

**Card Layout:**
- Symbol + company name
- Close price + 1-day %
- Score bar (0–6)
- Clickable for weekly history modal
- No overlap, proper spacing

**Modal (click stock):**
- Header: Symbol · Company · Cap · Score · Close · D>100 / W>100
- EMA panel: 6 daily EMAs with Above/Below tags
- Weekly history table: scrollable, last ~104 weeks

---

## Configuration Knobs (user-adjustable)

```python
EMAS = [5, 10, 20, 50, 100, 200]          # Daily EMA periods
YEARS_BACK = 5                             # Historical data depth
WEEKS_SHOWN = 104                          # Weeks in modal history
THIN_WEEKLY_BARS = 150                     # Flag if < 150 weekly bars (~3 yrs)
BATCH = 50                                 # Tickers per yfinance call (smaller = gentler on Yahoo)
SLEEP_BETWEEN = 1.5                        # Seconds between batches
```

---

## Maintenance Calendar

**Once per year (end of year or start of new year):**
- Nasdaq publishes updated Nasdaq-100 components
- S&P publishes updated S&P-500 components
- Update the ticker lists in the script
- Re-run to pick up any new/removed stocks

**Monthly:**
- Keepalive workflow runs (auto) — keeps GitHub scheduler active

**Never (automatic forever):**
- Price cache — updates itself daily
- Weekly history — accumulates forever, never needs manual maintenance

---

## Files You'll Create / Upload to GitHub

1. **`ekaiva_stocks_us.py`** — Python script (provided below)
2. **`prices_cache_us.parquet`** — Empty or starter cache (auto-populates on first run)
3. **`.github/workflows/us_daily.yml`** — Workflow file (provided below)
4. **`README.md`** (optional) — Description for the repo

---

## Setup (One-Time)

1. Create a new GitHub repo called `stocks-us` (public)
2. Upload the 3 files above
3. Enable GitHub Pages (Settings → Pages → Deploy from main branch, root folder)
4. Manually trigger the workflow once to build the first dashboard
5. Your link: `https://YOURUSERNAME.github.io/stocks-us/dashboard_stocks_us.html`

---

## Known Limitations / Notes

- **Yahoo throttling:** Free tier occasionally skips tickers when pulling 600 at once. Script auto-retries; if a few still skip, they're added back on the next day's run.
- **Weekends/holidays:** No run (schedule is Mon–Fri only).
- **US market timezones:** All times in ET (Eastern Time). Converted to IST for your reference.
- **Link is public:** Anyone with the URL can view. OK for market-breadth data; never put client names here.

---

End of Specification.
