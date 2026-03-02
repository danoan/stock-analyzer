# Fundascope Score Reference

## Stock Info Cards (`info_api.py`)

Computed from `yfinance Ticker.info` data. Displayed as letter grades (A–F).

### Overall Grade
Average of all graded section scores below (A≥4.5, B≥3.5, C≥2.5, D≥1.5, F<1.5).

### Valuation Grade
Averages scores from 3 metrics:
- **Trailing P/E**: <0→1, <12→5, <18→4, <25→3, <35→2, ≥35→1
- **PEG Ratio**: <0→1, <1→5, <1.5→4, <2→3, <3→2, ≥3→1
- **Price/Book**: <0→1, <1.5→5, <3→4, <5→3, <10→2, ≥10→1

### Profitability Grade
Averages scores from 2 metrics:
- **Return on Equity**: >25%→5, >15%→4, >8%→3, >0%→2, ≤0%→1
- **Operating Margin**: >25%→5, >15%→4, >8%→3, >0%→2, ≤0%→1

### Financial Health Grade
Averages scores from 2 metrics:
- **Current Ratio**: >2.0→5, >1.5→4, >1.0→3, >0.7→2, ≤0.7→1
- **Debt/Equity**: <30→5, <60→4, <100→3, <200→2, ≥200→1

### Growth Grade
Averages scores from 2 metrics:
- **Revenue Growth (YoY)**: >20%→5, >10%→4, >3%→3, >0%→2, ≤0%→1
- **Earnings Growth (YoY)**: >25%→5, >10%→4, >3%→3, >0%→2, ≤0%→1

### Dividends Grade *(only shown if stock pays dividends)*
Averages scores from 2 metrics:
- **Dividend Yield**: >4%→5, >2.5%→4, >1%→3, >0%→2, ≤0%→1
- **Payout Ratio**: 0–40%→5, ≤60%→4, ≤80%→3, ≤100%→2, >100%→1

---

## Income Statement Cards (`api.py`)

Computed from historical income statement data. Displayed as a label + letter grade.

### Revenue Growth Grade
CAGR computed across all available years: `(end/start)^(1/n) - 1`
- >10%→A, >5%→B, >0%→C, >-5%→D, ≤-5%→F

### Profit Trend Grade
Counts how often Net Income increased year-over-year:
- ≥66% of years improving → "Improving" → **A**
- ≥33% → "Mixed" → **C**
- <33% → "Declining" → **F**
- (Stable if <2 years of data) → **B**

### Margin Health Grade
Average operating margin across all years:
- >15% → "Strong" → **A**
- >8% → "Moderate" → **B**
- >0% → "Weak" → **D**
- ≤0% → "Negative" → **F**

### Earnings Quality Grade
Based on whether Net Income is consistently positive and stable (low coefficient of variation):
- All positive + stable (CV < 0.4) → "High" → **A**
- All positive but volatile → "Moderate" → **B**
- Any negatives → "Low" → **D**

### Dividend Safety Grade *(only shown if stock pays dividends)*
Weighted score on a 1–5 scale:

| Component | Weight | Scoring |
|---|---|---|
| Payout ratio | 30% | ≤30%→5, ≤50%→4, ≤70%→3, ≤90%→2, >90%→1 |
| Net income trend | 25% | ≥75% up years→5, ≥50%→4, ≥25%→2, <25%→1 |
| Earnings stability (CV) | 20% | CV<0.1→5, <0.2→4, <0.4→3, <0.6→2, ≥0.6→1 |
| Avg operating margin | 15% | >20%→5, >12%→4, >5%→3, >0%→2, ≤0%→1 |
| Revenue trend | 10% | Same formula as net income trend |

Result: 5→"Very Safe"→A, 4→"Safe"→B, 3→"Borderline"→C, 2→"Unsafe"→D, 1→"Dangerous"→F

### Overall Health Grade *(Income Statement)*
Average of all income-statement grades (Revenue Growth, Profit Trend, Margin Health, Earnings Quality, and Dividend Safety if present).
