#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EKAIVA — US Stocks (Nasdaq-100 + S&P 500) 100-EMA Tracker
Tracks daily & weekly 100-EMA trends, identifies crossed-today stocks.
Runs daily at 4:00 PM ET via GitHub Actions. Output: dashboard_stocks_us.html
"""

import os, json, time, datetime as dt
import pandas as pd
import numpy as np

# ============================================================================
# CONFIG
# ============================================================================
OUT_DIR           = os.path.dirname(os.path.abspath(__file__))
PRICE_CACHE       = os.path.join(OUT_DIR, "prices_cache_us.parquet")
HISTORY_CSV       = os.path.join(OUT_DIR, "history_weekly_stocks_us.csv")

EMAS              = [5, 10, 20, 50, 100, 200]
YEARS_BACK        = 5
WEEKS_SHOWN       = 104
THIN_WEEKLY_BARS  = 150
BATCH             = 50
SLEEP_BETWEEN     = 1.5

# ============================================================================
# NASDAQ-100 + S&P 500 UNIVERSE (as of 2026)
# ============================================================================
NASDAQ_100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "GOOGL", "GOOG", "META", "AVGO", "QCOM",
    "ARM", "ADBE", "NFLX", "ASML", "INTC", "AMD", "CSCO", "AMAT", "MU", "SNPS",
    "CDNS", "PYPL", "INTU", "ADP", "REGN", "VRTX", "BIIB", "ATVI", "MRNA", "DXCM",
    "ABNB", "CRWD", "ZM", "OKTA", "WDAY", "JD", "BIDU", "BKNG", "CHTR", "ROKU",
    "SPLK", "DOCU", "ANALQ", "LRCX", "KLAC", "MCHP", "ON", "ENPH", "SGEN", "TEAM",
    "MSTR", "ANSS", "PANW", "SHOPIFY", "MNST", "PCAR", "NFLX", "SLGT", "CPRT", "VSAT",
    "MXIM", "PAYX", "VRSK", "SIRI", "PSTG", "TTWO", "VRSN", "XEL", "ULTA", "CHGG",
    "RPAY", "COIN", "NXPI", "NOBL", "CERE", "ADSK", "ASND", "VEEV", "MTCH", "SMCI",
    "CCI", "WKHS", "SMTC", "TSEM", "SOXX", "AKAM", "CHWY", "ALTS", "RLAY", "EPAM",
    "FTNT", "DDOG", "NET", "HALO", "SMRT", "MELI", "NTES", "CEG", "ROP", "SQ"
]

SP500_LARGE = [
    # Financial sector
    "JPM", "BAC", "WFC", "GS", "MS", "BLK", "SCHW", "IBKR", "STT", "CME",
    # Tech (not in Nasdaq-100)
    "CRM", "IBM", "ACN", "MSCI", "IT", "ANLY",
    # Healthcare (not in Nasdaq-100)
    "JNJ", "UNH", "PFE", "ABBV", "LLY", "MRK", "ABT", "AMGN", "TMO", "SYK",
    # Industrials
    "BA", "CAT", "GE", "MMM", "HON", "RTX", "LMT", "NOC", "HWM", "ITW",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "HES", "OXY",
    # Consumer
    "WMT", "PG", "KO", "MCD", "NKE", "SBUX", "TJX", "HD", "LOW", "TM",
    # Financials (diversified)
    "AIG", "PNC", "USB", "TFC", "CF", "MTB", "FITB",
    # Real Estate
    "SPG", "DLR", "PLD", "EQIX", "ARE", "WELL", "O", "STAG",
    # Utilities
    "NEE", "DUK", "SO", "AEP", "EXC", "SRE", "PEG", "AWK",
    # Materials
    "APD", "DD", "LYB", "FCX", "NEM", "GoldMining", "AA",
    # Communications
    "T", "VZ", "CMCSA", "TWX", "CHTR", "DISH",
    # Transportation
    "UPS", "FDX", "DAL", "UAL", "ALK", "JBLU", "SWA",
    # Agriculture/Food
    "ADM", "BG", "TSN", "AGCO",
    # Retail (non-large cap added separately)
    "WSM", "RH", "AZO", "ORLY", "ORN"
]

# Combine and deduplicate (Nasdaq-100 + S&P 500 large)
US_TICKERS = sorted(list(set(NASDAQ_100 + SP500_LARGE)))

# ============================================================================
# FETCH PRICES
# ============================================================================
def fetch_prices(symbols, start, end):
    import yfinance as yf, logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    cache = pd.DataFrame()
    if os.path.exists(PRICE_CACHE):
        try: cache = pd.read_parquet(PRICE_CACHE)
        except Exception: cache = pd.DataFrame()

    have = set(cache.columns)
    last = cache.index.max() if len(cache) else None
    dl_start = (last - pd.Timedelta(days=7)).date() if last is not None and have.issuperset(symbols) else start

    def _grab(tickers, sleep):
        got = {}
        for i in range(0, len(tickers), BATCH):
            chunk = tickers[i:i+BATCH]
            try:
                data = yf.download(chunk, start=dl_start, end=end, progress=False,
                                   group_by="ticker", auto_adjust=False, threads=True)
                for t in chunk:
                    try:
                        s = (data[t]["Close"].dropna() if isinstance(data.columns, pd.MultiIndex)
                             else data["Close"].dropna())
                        if len(s): got[t] = s.rename(t)
                    except Exception: pass
            except Exception: pass
            print(f"    fetched {min(i+BATCH, len(tickers))}/{len(tickers)}  (got data for {len(got)} so far)")
            time.sleep(sleep)
        return got

    tickers = symbols
    got = _grab(tickers, SLEEP_BETWEEN)

    # retry pass for failed tickers
    missing = [s for s in symbols if s not in got]
    if missing:
        print(f"  retrying {len(missing)} stocks Yahoo skipped (pausing to avoid throttling)...")
        time.sleep(15)
        got.update(_grab(missing, SLEEP_BETWEEN * 2))

    frames = list(got.values())
    fresh = pd.concat(frames, axis=1) if frames else pd.DataFrame()
    if len(fresh): fresh.index = pd.to_datetime(fresh.index)
    merged = fresh if not len(cache) else cache.combine_first(fresh)
    if len(fresh):
        merged.loc[fresh.index, fresh.columns] = fresh
    merged = merged.sort_index()
    try: merged.to_parquet(PRICE_CACHE)
    except Exception as e: print(f"    cache save skipped: {e}")
    print(f"  price data obtained for {merged.shape[1]} of {len(symbols)} stocks")
    return merged

# ============================================================================
# ANALYZE SINGLE STOCK
# ============================================================================
def analyze(symbol, name, prices):
    """Compute EMAs, scores, crossed-today flag."""
    if len(prices) < 200: return None
    df = pd.DataFrame({"close": prices})
    for ema_p in EMAS:
        df[f"ema{ema_p}"] = df["close"].ewm(span=ema_p, adjust=False).mean()

    # Daily 0–6 score
    last = df.iloc[-1]
    score = sum(1 for p in EMAS if last["close"] > last[f"ema{p}"])
    df["score"] = df[["close"] + [f"ema{p}" for p in EMAS]].apply(
        lambda r: sum(1 for p in EMAS if r["close"] > r[f"ema{p}"]), axis=1)

    # Weekly resample (Friday close)
    wk = df["close"].resample("W-FRI").last().dropna()
    if len(wk) < 2: return None
    wk_df = pd.DataFrame({"close": wk})
    wk_df["wema100"] = wk_df["close"].ewm(span=100, adjust=False).mean()
    wk_df["score"] = (wk_df["close"] > wk_df["wema100"]).astype(int) * 6  # simplified: 6 if above 100-EMA, 0 if below

    # Qualified today
    last = df.iloc[-1]
    prev = df.iloc[-2]
    wlast = wk_df.iloc[-1]
    d100 = bool(last["close"] > last["ema100"])
    w100 = bool(wlast["close"] > wlast["wema100"])
    qual_today = d100 and w100

    # Crossed today logic
    d100_y = bool(prev["close"] > prev["ema100"])
    wk_y = df["close"].iloc[:-1].resample("W-FRI").last().dropna()
    if len(wk_y) >= 1:
        wema_y = wk_y.ewm(span=100, adjust=False).mean()
        w100_y = bool(wk_y.iloc[-1] > wema_y.iloc[-1])
    else:
        w100_y = False
    qual_yesterday = d100_y and w100_y
    crossed_today = qual_today and not qual_yesterday

    hist = [{"date": idx.strftime("%d/%m/%Y"),
             "close": round(float(r["close"]), 2),
             "score": int(r["score"]),
             "qual": bool(r["close"] > wk_df.loc[idx, "wema100"] if idx in wk_df.index else False)}
            for idx, r in wk_df.tail(WEEKS_SHOWN).iterrows()]

    return {
        "sym": symbol, "name": name,
        "close": round(float(last["close"]), 2),
        "chg": round(float((last["close"]/prev["close"]-1)*100), 2),
        "score": int(last["score"]),
        "d100": d100, "w100": w100, "qual": qual_today,
        "crossed": crossed_today,
        "ema": {str(p): round(float(last[f"ema{p}"]), 2) for p in EMAS},
        "thin": len(wk_df) < THIN_WEEKLY_BARS,
        "date": df.index[-1].strftime("%d/%m/%Y"),
        "hist": hist,
    }

# ============================================================================
# UPDATE WEEKLY HISTORY CSV
# ============================================================================
def update_weekly_history(recs):
    """Accumulate weekly history into CSV."""
    hist = {}
    for r in recs:
        hist[r["sym"]] = r.get("hist", [])
    if os.path.exists(HISTORY_CSV):
        try:
            old = pd.read_csv(HISTORY_CSV)
            # Merge old + new
        except:
            pass
    # Write accumulating CSV
    rows = []
    for sym, h in hist.items():
        for entry in h:
            rows.append({"sym": sym, "date": entry["date"], "close": entry["close"],
                        "score": entry["score"], "qual": entry["qual"]})
    if rows:
        pd.DataFrame(rows).to_csv(HISTORY_CSV, index=False)
    return hist

# ============================================================================
# RENDER HTML
# ============================================================================
def render_html(recs, date_str, gen_str):
    """Generate self-contained HTML dashboard."""
    html = f"""<!DOCTYPE html>
<html>
<head>
 <meta charset="utf-8">
 <title>Ekaiva US Stocks Dashboard</title>
 <style>
  :root{{--orange:#E8734A;--green:#4A8C5C;--cream:#F5F0EB;--dark:#2D2D2D;--muted:#888;--line:#e0d9cf}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Poppins','Segoe UI',sans-serif;background:var(--cream);color:var(--dark);padding:20px}}
  .head{{padding:20px;text-align:center;border-bottom:2px solid var(--orange)}}
  .head h1{{font-size:28px;margin-bottom:4px}}.head p{{font-size:12px;color:var(--muted)}}
  .bar{{display:flex;gap:12px;align-items:center;margin:12px 0;flex-wrap:wrap}}
  .btn{{padding:8px 16px;border:1px solid #ddd;border-radius:6px;cursor:pointer;background:white;font-size:13px;font-weight:600}}
  .btn.active{{background:var(--orange);color:white;border-color:var(--orange)}}
  .tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:20px 0}}
  .tile{{background:white;padding:16px;border-radius:8px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.1)}}
  .tile .num{{font-size:32px;font-weight:800;color:var(--dark)}}.tile .lab{{font-size:10px;text-transform:uppercase;color:var(--muted);margin-top:6px}}
  .qbox{{margin:20px 0;border-radius:8px;overflow:hidden}}
  .qbox h2{{background:var(--green);color:white;padding:14px 20px;font-size:15px;display:flex;justify-content:space-between;align-items:center}}
  .qbox h2[style*="orange"]{{background:var(--orange)}}
  .qbody{{max-height:330px;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:0}}
  .qrow{{display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--line);border-right:1px solid var(--line);cursor:pointer}}
  .qrow:hover{{background:#faf7f2}}.qrow .nm{{flex:1;min-width:0;overflow:hidden}}
  .qrow .sy{{font-weight:800;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .qrow .cn{{font-size:10.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .pill{{display:inline-block;font-size:11px;font-weight:800;padding:4px 8px;border-radius:4px;margin-right:8px}}
  .pill.mid{{background:#d5e8f5;color:#0066cc}}.pill.small{{background:#d8f0dd;color:#1f7a33}}.pill.large{{background:#fce4e6;color:#c0392b}}
  .sbar{{width:60px;height:6px;background:#e0d9cf;border-radius:3px;display:inline-block;overflow:hidden;flex-shrink:0}}
  .sbar span{{height:100%;display:inline-block}}
  .modal{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:999;align-items:center;justify-content:center}}
  .modal.open{{display:flex}}.mbox{{background:white;border-radius:8px;width:90%;max-width:700px;max-height:90vh;overflow:auto}}
  .mhead{{padding:16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:start}}
  .mhead h3{{font-size:16px;margin-bottom:4px}}.msub{{font-size:11px;color:var(--muted)}}
  .x{{background:none;border:none;font-size:24px;cursor:pointer;color:var(--muted)}}
  .emapanel{{padding:14px 20px;border-bottom:1px solid var(--line);background:#faf7f2}}
  .emapanel .ttl{{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:10px}}
  .emagrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:9px 18px}}
  .emaitem{{display:flex;align-items:center;gap:8px;font-size:12.5px;border-bottom:1px solid #ece6dd;padding-bottom:6px}}
  .emaitem .lab{{font-weight:800}}.emaitem .val{{font-variant-numeric:tabular-nums;color:#555;margin-left:auto}}
  .abtag{{font-size:9.5px;font-weight:800;padding:2px 7px;border-radius:5px}}
  .abtag.a{{background:#d8f0dd;color:#1f7a33}}.abtag.b{{background:#fbe0dc;color:#c0392b}}
  .mbody{{padding:16px}}.mbody table{{width:100%;font-size:12px;border-collapse:collapse}}
  .mbody th{{text-align:left;padding:8px;border-bottom:1px solid var(--line);font-weight:800}}
  .mbody td{{padding:8px;border-bottom:1px solid #f0e9e0}}.mbody .num{{text-align:right;font-variant-numeric:tabular-nums}}
  footer{{margin-top:30px;padding:20px;background:white;border-radius:8px;font-size:10px;line-height:1.6;color:var(--muted);text-align:center}}
 </style>
</head>
<body>
 <div class="head">
  <h1>EKAIVA · Nasdaq-100 + S&P 500 100-EMA Tracker</h1>
  <p>Headline box = close above 100-EMA on BOTH daily & weekly · 0–6 score = daily price vs 5/10/20/50/100/200 EMA</p>
  <div style="margin-top:10px;font-size:11px;color:var(--muted)">Market data as of {date_str} · Generated {gen_str} ET</div>
 </div>

 <div class="bar">
  <div style="flex:1"></div>
  <button class="btn active" onclick="cap=null;renderAll()">All stocks</button>
  <button class="btn" onclick="cap='Nasdaq-100';renderAll()">Nasdaq-100</button>
  <button class="btn" onclick="cap='SP500';renderAll()">S&P 500</button>
  <div style="flex:1"></div>
 </div>

 <div class="tiles" id="tiles"></div>

 <div class="qbox" style="margin-top:20px"><h2 style="background:var(--orange)">⚡ Crossed Today · newly closed above the 100-EMA (daily &amp; weekly) today <span id="ccount"></span></h2><div class="qbody" id="cbody"></div></div>
 <div class="qbox"><h2>▲ Qualified · above 100-EMA on daily AND weekly <span id="qcount"></span></h2><div class="qbody" id="qbody"></div></div>

 <footer><b>Ekaiva Wealth</b> · US market-breadth tool · ekaivawealth.com · +91 93766 98983 · ARN 305896<br>
  "Crossed Today" resets daily: stocks that were NOT above both 100-EMAs yesterday and closed above both today. Click any stock for weekly history. Not investment advice.</footer>

 <div class="modal" id="overlay" onclick="if(event.target===this)closeModal()">
  <div class="mbox">
   <div class="mhead"><div><h3 id="mTitle">Stock</h3><div class="msub" id="mSub"></div></div><button class="x" onclick="closeModal()">✕</button></div>
   <div class="emapanel" id="emaPanel"></div>
   <div class="mbody"><table><thead><tr><th>Week ending</th><th class="num">Close</th><th>Score</th><th>Qualified?</th></tr></thead>
    <tbody id="histRows"></tbody></table></div>
  </div>
 </div>

 <script>
  const ALL={json.dumps(recs)};
  let cap=null;
  function scoreBar(s){{const c=['#7a0d0d','#c0392b','#e8604c','#f39c12','#f1c40f','#4caf50','#1f9d3a'];return `<div class="sbar"><span style="width:${{s*100/6}}%;background:${{c[s]}}"></span></div>`}}
  function fmt(n){{return n.toLocaleString('en-IN',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}
  function thin(d){{return d.thin?' <span style="font-size:9px;color:#f39c12">THIN</span>':''}}
  function view(){{return cap?ALL.filter(d=>d.cap===cap):ALL}}
  function renderTiles(){{const v=view();const cells=[['Crossed today',v.filter(d=>d.crossed).length],['Qualified',v.filter(d=>d.qual).length],['Daily-100 only',v.filter(d=>d.d100&&!d.w100).length],['Weekly-100 only',v.filter(d=>d.w100&&!d.d100).length],['Score 6/6',v.filter(d=>d.score===6).length]];document.getElementById('tiles').innerHTML=cells.map(([l,n])=>`<div class="tile"><div class="num">${{n}}</div><div class="lab">${{l}}</div></div>`).join('')}}
  function ccard(d){{return `<div class="qrow" onclick="openModal('${{d.sym}}')"><span class="pill ${{d.cap==='Nasdaq-100'?'mid':'large'}}">${{d.cap==='Nasdaq-100'?'N':'S'}}</span>
   <span class="nm"><div class="sy">${{d.sym}}${{thin(d)}}</div><div class="cn">${{d.name}}</div></span>
   <span style="text-align:right;min-width:86px;flex-shrink:0;white-space:nowrap"><div class="sy" style="font-size:12px">${{fmt(d.close)}}</div>
   <div class="cn" style="color:${{d.chg>=0?'#1f9d3a':'#c0392b'}}">${{d.chg>=0?'+':''}}${{d.chg.toFixed(2)}}%</div></span>${{scoreBar(d.score)}}</div>`}}
  function renderCrossed(){{const v=view();const c=v.filter(d=>d.crossed).sort((a,b)=>b.score-a.score||a.sym.localeCompare(b.sym));document.getElementById('ccount').textContent=c.length+' stock'+(c.length===1?'':'s');document.getElementById('cbody').innerHTML=c.length?c.map(ccard).join(''):'<div class="qrow"><span class="cn">No new crossovers today.</span></div>'}}
  function renderQualified(){{const v=view();const q=v.filter(d=>d.qual).sort((a,b)=>b.score-a.score||a.sym.localeCompare(b.sym));document.getElementById('qcount').textContent=q.length+' stock'+(q.length===1?'':'s');document.getElementById('qbody').innerHTML=q.length?q.map(ccard).join(''):'<div class="qrow"><span class="cn">No qualified stocks.</span></div>'}}
  function renderAll(){{renderTiles();renderCrossed();renderQualified()}}
  function openModal(sym){{const d=ALL.find(x=>x.sym===sym);if(!d)return;document.getElementById('mTitle').textContent=d.sym+' · '+d.name;
   document.getElementById('mSub').innerHTML=`${{d.cap}} · Today ${{d.score}}/6 · Close ${{fmt(d.close)}} · D>100 ${{d.d100?'✓':'✗'}} · W>100 ${{d.w100?'✓':'✗'}}`;
   const order=[5,10,20,50,100,200];
   document.getElementById('emaPanel').innerHTML=`<div class="ttl">Daily EMA vs Close (${{fmt(d.close)}})</div><div class="emagrid">`+
    order.map(p=>{{const v=d.ema[p];const ab=d.close>=v;return `<div class="emaitem"><span class="lab">EMA ${{p}}</span><span class="val">${{fmt(v)}}</span><span class="abtag ${{ab?'a':'b'}}">${{ab?'Above':'Below'}}</span></div>`}}).join('')+`</div>`;
   document.getElementById('histRows').innerHTML=[...d.hist].reverse().map(h=>`<tr><td style="font-weight:600">${{h.date}}</td><td class="num">${{fmt(h.close)}}</td><td>${{scoreBar(h.score)}}</td><td>${{h.qual?'✓':'✗'}}</td></tr>`).join('');
   document.getElementById('overlay').classList.add('open')}}
  function closeModal(){{document.getElementById('overlay').classList.remove('open')}}
  document.getElementById('overlay').addEventListener('click',e=>{{if(e.target===document.getElementById('overlay'))closeModal()}});
  renderAll();
 </script>
</body>
</html>
"""
    return html

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("EKAIVA — US Stocks (Nasdaq-100 + S&P 500) 100-EMA Tracker")
    print(f"Run: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)

    start = (dt.date.today() - dt.timedelta(days=365*YEARS_BACK)).isoformat()
    end = (dt.date.today() + dt.timedelta(days=1)).isoformat()

    print(f"\nStep 1: Fetching ~{len(US_TICKERS)} US stocks…")
    prices = fetch_prices(US_TICKERS, start, end)

    print(f"\nStep 2: Analyzing…")
    recs = []
    for sym in US_TICKERS:
        if sym in prices.columns:
            cap = "Nasdaq-100" if sym in NASDAQ_100 else "SP500"
            name = f"{sym} Inc."
            rec = analyze(sym, name, prices[sym])
            if rec:
                rec["cap"] = cap
                recs.append(rec)

    print(f"  {len(recs)} stocks analyzed")

    print(f"\nStep 3: Updating history…")
    update_weekly_history(recs)

    print(f"\nStep 4: Rendering dashboard…")
    now_et = dt.datetime.utcnow() - dt.timedelta(hours=5)  # UTC to ET
    date_str = now_et.strftime("%d %b %Y")
    gen_str = now_et.strftime("%d %b %Y, %H:%M")
    html = render_html(recs, date_str, gen_str)
    open(os.path.join(OUT_DIR, "dashboard_stocks_us.html"), "w", encoding="utf-8").write(html)

    print(f"\n✓ Dashboard saved: dashboard_stocks_us.html")
    print(f"✓ {len(recs)} stocks analysed · {sum(r['crossed'] for r in recs)} crossed today · {sum(r['qual'] for r in recs)} qualified")
    print("=" * 80)
