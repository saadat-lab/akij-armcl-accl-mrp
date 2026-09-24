---
name: armcl-accl-mrp
description: ARMCL/ACCL 18-month MRP dashboard — REV budget to Spot vs Blanket decision. Use when building or refreshing the Ready-Mix/Cement material requirement plan, Class-A classification, coverage and net order, spot vs blanket logic, market intelligence and offline HTML export (mirrors AAFL pattern).
---

# ARMCL/ACCL — 18M MRP Dashboard Skill

Replicates `AAFL 24M MRP` pattern for `ARMCL (BU 175)` + `ACCL (BU 4)` business units. Covers `17.2M CFT` IBOS approved REV budget `Jul-26→Jun-27` extended to `18M Jul-26→Dec-27` via trend forecast, ABC, cover, net order, spot vs blanket and geopolitics.

## When to Use

- User asks to build/refresh ARMCL/ACCL MRP dashboard, 18-month requirement plan, or spot vs blanket recommendation.
- User provides REV PDF matrix (Qty / Landed Rate / Procurement Value) with 12 months and wants 6-month forecast.
- User wants offline HTML export mirroring AAFL style.

## Inputs Required

1. **SBU confirmation** — ask non-technical: *Which factory? Feed (AAFL) or Concrete/Cement (ARMCL/ACCL)?* `saas.masterBusinessUnitArc` → `AAFL 232, ACCL 4, ARMCL 175`.
2. **REV PDF / matrix** — the `Qty x Landed Rate` table is the source. `Cement Clinker 907Cr, Lime 3/4 220Cr, Slag 219Cr, Limestone 10-20 181Cr, PCC 163Cr, Gabbro 10-20 88Cr, Sand 81Cr` etc. total `~2,255 Cr`.
3. **Cash dict (optional)** — `CASH {Jul-26: Cr, ...}` for cash-calendar; skip if unavailable.
4. **GEO risk per Class-A** — `Clinker Import HIGH, Sand Local LOW, Bitumen Import HIGH` → extend to `GEO {name: (risk, source, ticker, note)}`.

Non-technical simplified prompts:
- *Which factory?*
- *Is the PDF you shared the latest budget? Need old build_dashboard.py? Need monthly cash?*
- *For each main material, is it Import/Local and High/Medium/Low risk?*

## Data Sources

| Source | What it provides | How accessed |
|---|---|---|
| DWH `DWH` on `203.202.241.211:1433` (`DWH.mcp_user`) | `stock/cover`, `monthly consumption`, `landed rate history Σvalue/Σqty*1000`, `FG actual sales` | `@st.cache_data ttl=600` queries; falls back to static when `🔴 OFFLINE` |
| Embedded `RM_DATA` (JSON static) | Per-RM forecast 12M+6M, budget/latest rate, trend, decision, monthly plan | Baked in; refreshed by rebuilding from REV |
| REV PDF matrix | 12M Qty, Landed Rate, Procurement Value | Parsed manually / `pdfplumber` + `rapidfuzz ≥80` |
| Market intel | Futures (`yfinance` Brent/Coal/Iron Ore/FX USD/BDT) + Reuters/FAO headlines | `ttl=1800` |

## Core Logic to Replicate

### 1. Forecast 13-18M
- Linear fit on last 9M: `slope, _ = polyfit(x, y[-9:])`
- 6 forecast months: `pred = last + slope*i`, `blended = 0.7*pred + 0.3*avg6`, capped `±15%` (AAFL was `±40%`). Store `monthly18 = qty12 + forecast6`, `req18 = sum(monthly18)`.

### 2. ABC Classification
- `value12 = Σ(qty * rate)`. Sort descending, cumulative `cum%`. `A = cum<80%` (≈7 items), `B = 80-95%`, `C = rest`. Force `Bitumen` to `A` if strategic despite value.

### 3. Cover & Net Order
- `cover_mo = stock_mt / (req18/18)`, `cover_days = cover*30`. If DWH offline use static stock fallback.
- `net_order = req18 - stock_mt` (conservative, before open POs). Flag `cover<1` as urgent.

### 4. Decision Matrix (same as AAFL)
```
if cover < 1:
  Local → SPOT-URGENT
  Import → BLANKET-URGENT
else:
  (HIGH, Import) → BLANKET (cover LONG)
  (HIGH, Local) → SPOT-URGENT
  (HIGH, Mixed) → BLANKET
  (MODERATE, Import) → BLANKET(part)
  (MODERATE, Local) → SPOT
  (LOW, Import) → BLANKET(dip)
  (LOW, Local) → SPOT
  else → SPOT(verify)
```
Risk from `GEO` dict: `high/moderate/low` + `Import/Local`.

### 5. Price Projection
- Weighted `Σvalue/Σqty*1000` per month, `budget_rate` via PDF fuzzy match, `proj = linear trend`, signal note per RM.

## Output Files

1. `armcl_accl_mrp_dashboard.py` — Streamlit app:
   ```
   pip install streamlit pyodbc pandas plotly rapidfuzz pdfplumber yfinance feedparser
   streamlit run armcl_accl_mrp_dashboard.py
   ```
   Hardcoded `DB` → move to `st.secrets` before commit.

2. `armcl_accl_mrp_dashboard.html` — offline self-contained export (Plotly CDN, `window.DATA` JSON). Same CSS vars as AAFL: `--ink #24333B --amber #C97B2E --red #B23A2F --green #2E7D5B --blue #2C5F8A --slate #5B6B73 --bg #F7F7F5`, KPI cards, `b-blk/b-spt/b-urg` badges, grid2 dual charts.

## Dashboard Sections (in order, same as AAFL)

1. KPIs: 18-mo RM req, Class-A count, <1mo urgent count, DWH live/offline, over-budget banner.
2. Class-A One-line Decision Table: stock, cover d/mo, req18, net order, budget vs latest, trend, DECISION.
3. Item Detail dual graphs: (a) landed rate line + qty bars y2 + budget dot + projection dash, (b) monthly req amber 12M + grey 6M forecast; flags + signal.
4. All RM Month-wise (18M) searchable matrix.
5. Stock Position chart (months covered bar, red <1, amber <1.5).
6. Market Intelligence GEO cards + futures placeholder.
7. Methodology expander.
8. Export button (writes HTML).

## Verification Checklist

- `python -m py_compile armcl_accl_mrp_dashboard.py`
- HTML opens, 8 Class-A badges render, 16 total RMs, 18 months `Jul-26→Dec-27`.
- Urgent logic: Clinker/Slag/Bitumen BLANKET-URGENT, Sand/Limestone 10-20 SPOT-URGENT, Lime 3/4/Gypsum BLANKET(part).

## Caveats

- Static `RM_DATA` needs rebuild on new REV; DWH stock fallback is illustrative until live connection.
- Cement tickers differ from AAFL feed (corn/soy) — use `Brent, Coal, Iron Ore, USD/BDT`.
- Packaging bags are Class C, kept for completeness but not in decision focus.
