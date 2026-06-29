# Setup Guide — Ekaiva US Stocks Dashboard on GitHub

## What You'll Have
A global web link that shows **Nasdaq 100 + S&P 500 stocks** (600+ tickers) with daily + weekly 100-EMA analysis. Auto-updates every weekday at **4 PM ET (9:30 PM IST)**. Your laptop stays off.

Link format: `https://YOUR-GITHUB-USERNAME.github.io/stocks-us/dashboard_stocks_us.html`

---

## One-Time Setup (15 minutes)

### Phase 1 — Create a new GitHub repo

1. Go to **github.com** and sign in.
2. Click the **+** at top-right → **New repository**.
3. **Repository name:** `stocks-us`
4. Choose **Public**.
5. Tick **"Add a README file."**
6. Click **Create repository**.

### Phase 2 — Upload the 3 files

7. On your new repo page, click **Add file → Upload files**.
8. From the outputs folder I gave you, drag in these three files:
   - `ekaiva_stocks_us.py`
   - `prices_cache_us.parquet` (leave empty or use a starter; it auto-populates)
   - `us_daily.yml` (the workflow file)
9. Scroll down and click **Commit changes**.

### Phase 3 — Add the automation file

10. Click **Add file → Create new file**.
11. In the **filename box**, type exactly:
    ```
    .github/workflows/us_daily.yml
    ```
    (GitHub creates the folders as you type each `/`.)
12. Open the `us_daily.yml` file from the outputs folder. Copy all the text (Ctrl+A, Ctrl+C).
13. Paste it into the big box on GitHub (Ctrl+V).
14. Click **Commit changes**.

### Phase 4 — Turn on the auto-run

15. Click the **Actions** tab.
16. If you see an enable button, click it.
17. On the left, click **Ekaiva US Stocks Daily**.
18. Click **Run workflow** → green **Run workflow** button.
19. Wait for a **green check ✓** (takes a few minutes). This means it ran successfully and built your dashboard.

### Phase 5 — Enable the web link

20. Click **Settings** (top of repo).
21. On the left, click **Pages**.
22. Under **Source**, choose **Deploy from a branch**.
23. Set **Branch = main**, folder **= / (root)**.
24. Click **Save**.
25. Wait ~1 minute. Your link is:
    ```
    https://YOURUSERNAME.github.io/stocks-us/dashboard_stocks_us.html
    ```
    (Replace YOURUSERNAME with your GitHub username.)

**Test it:** Open that link on your phone or desktop. Add it to your home screen for quick access.

---

## What Happens Next

- **Every weekday at 4 PM ET (9:30 PM IST)**, the workflow runs automatically.
- It fetches the latest prices from Yahoo Finance.
- It analyzes all 600+ stocks, identifies fresh crossovers, builds the dashboard.
- Your link refreshes on its own — just open it anytime after 4:30 PM ET to see today's data.

---

## Maintenance

- **Never manually touch anything.** It runs by itself.
- **Once per year** (Dec/Jan): If you want to update the Nasdaq-100 or S&P-500 lists (they change slightly), let me know and I'll send you the updated script.
- **January and July**: AMFI publishes updated lists (irrelevant for US, but relevant if you keep the Indian dashboard too).

---

## Troubleshooting

**"I don't see today's data on the link"**
- Go to **Actions** tab. Is there a run for today with a green ✓?
  - If **yes** ✓ → Try a hard refresh (**Ctrl+F5**) on your dashboard link. GitHub's cache can lag by a minute or two.
  - If **no** → The scheduler hasn't fired yet. GitHub's schedule can be 30+ minutes late on the first day. Wait an hour or manually trigger it (click **Run workflow** again).

**"The numbers look identical to yesterday"**
- Yahoo sometimes publishes prices late (up to 7–8 PM ET). If the run happened at 4 PM and prices aren't available yet, you'll see yesterday's data. By next day it'll be fresh. Or manually run at 6–7 PM if you want the absolute latest.

**"I want to change the time"**
- It's currently set to **4 PM ET (20:00 UTC)** in the workflow file. If you want a different time (e.g., 6 PM ET), tell me and I'll give you the one line to change.

---

## Your New Dashboard Link

Bookmark this once it's live:

**`https://YOURUSERNAME.github.io/stocks-us/dashboard_stocks_us.html`**

(Replace YOURUSERNAME with your actual GitHub username.)

---

Need help? Any step unclear? Take a screenshot and send it — I'll point you to the exact next click.
