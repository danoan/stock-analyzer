"""Stock info analysis: extracts, grades, and formats data from yfinance Ticker.info."""

import json
import math

from fundascope.core.cache import get_cached, set_cached

# ---------------------------------------------------------------------------
# Tooltips for each metric (educational)
# ---------------------------------------------------------------------------

METRIC_TOOLTIPS = {
    # Company Profile
    "shortName": "The company's common trading name.",
    "sector": "The broad economic sector the company operates in (e.g. Technology, Healthcare).",
    "industry": "The specific industry within the sector (e.g. Consumer Electronics, Drug Manufacturers).",
    "country": "The country where the company is headquartered.",
    "fullTimeEmployees": "Total number of full-time employees reported by the company.",
    "longBusinessSummary": "A brief description of what the company does and its main products or services.",
    # Valuation
    "marketCap": "Total market value of all outstanding shares. Calculated as share price × shares outstanding.",
    "trailingPE": "Price-to-Earnings ratio based on the last 12 months of actual earnings. Lower may indicate undervaluation, but compare within the same industry.",
    "forwardPE": "Price-to-Earnings ratio based on analysts' estimated future earnings. Lower than trailing P/E suggests expected earnings growth.",
    "pegRatio": "Price/Earnings-to-Growth ratio. Adjusts P/E for growth rate. PEG < 1 may indicate undervaluation relative to growth; > 2 may indicate overvaluation.",
    "priceToBook": "Compares share price to book value (assets minus liabilities) per share. Below 1 could mean undervalued or troubled company.",
    "priceToSalesTrailing12Months": "Market cap divided by total revenue. Useful for comparing companies with no earnings. Lower is generally more attractive.",
    "enterpriseToEbitda": "Enterprise Value divided by EBITDA. A valuation metric that accounts for debt. Lower values may indicate better value.",
    "enterpriseToRevenue": "Enterprise Value divided by Revenue. Similar to P/S but includes debt and cash in the calculation.",
    # Profitability
    "profitMargins": "Net income as a percentage of revenue. Shows how much of each dollar of revenue becomes profit after all expenses.",
    "operatingMargins": "Operating income as a percentage of revenue. Shows profitability from core business operations, before interest and taxes.",
    "grossMargins": "Gross profit as a percentage of revenue. Shows how much remains after direct costs (COGS). Higher means better pricing power.",
    "ebitdaMargins": "EBITDA as a percentage of revenue. A proxy for operating cash flow margin, ignoring depreciation and amortization.",
    "returnOnEquity": "Net income divided by shareholder equity. Measures how efficiently the company uses shareholders' invested capital to generate profit.",
    "returnOnAssets": "Net income divided by total assets. Measures how efficiently the company uses all its assets to generate profit.",
    # Financial Health
    "currentRatio": "Current assets divided by current liabilities. Measures short-term liquidity. Above 1.5 is generally healthy; below 1 may signal trouble.",
    "quickRatio": "Like current ratio but excludes inventory. A stricter liquidity test. Above 1 is generally comfortable.",
    "debtToEquity": "Total debt divided by shareholder equity. Higher means more leverage and financial risk. Below 100 is generally conservative.",
    "totalDebt": "The total amount of short-term and long-term debt the company owes.",
    "totalCash": "Total cash and cash equivalents on hand. More cash provides a safety buffer and flexibility.",
    # Growth
    "revenueGrowth": "Year-over-year revenue growth rate. Shows how fast the company's top line is expanding.",
    "earningsGrowth": "Year-over-year earnings growth rate. Shows how fast profitability is increasing.",
    "earningsQuarterlyGrowth": "Most recent quarter's earnings growth vs. the same quarter last year.",
    # Dividends
    "dividendYield": "Annual dividend per share divided by share price. Shows the return from dividends alone as a percentage.",
    "dividendRate": "The total annual dividend payment per share in dollars.",
    "payoutRatio": "Percentage of earnings paid out as dividends. Below 60% is generally sustainable; above 80% may be risky.",
    "fiveYearAvgDividendYield": "Average dividend yield over the past 5 years. Useful to see if current yield is above or below historical norms.",
    "exDividendDate": "The date by which you must own the stock to receive the next dividend payment.",
    # Price & Trading
    "currentPrice": "The most recent trading price of the stock.",
    "fiftyTwoWeekHigh": "The highest price the stock reached in the past 52 weeks.",
    "fiftyTwoWeekLow": "The lowest price the stock reached in the past 52 weeks.",
    "fiftyTwoWeekChange": "The percentage change in stock price over the past 52 weeks.",
    "beta": "A measure of volatility relative to the market. Beta > 1 means more volatile than the market; < 1 means less volatile.",
    "fiftyDayAverage": "Average closing price over the last 50 trading days. A short-term trend indicator.",
    "twoHundredDayAverage": "Average closing price over the last 200 trading days. A long-term trend indicator.",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_number(value, prefix="$"):
    """Format large numbers with abbreviations."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "---"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{prefix}{abs_val / 1e12:.1f}T"
    if abs_val >= 1e9:
        return f"{sign}{prefix}{abs_val / 1e9:.1f}B"
    if abs_val >= 1e6:
        return f"{sign}{prefix}{abs_val / 1e6:.1f}M"
    if abs_val >= 1e3:
        return f"{sign}{prefix}{abs_val / 1e3:.1f}K"
    return f"{sign}{prefix}{abs_val:.1f}"


def _fmt_ratio(value):
    """Format a decimal ratio as a percentage."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "---"
    return f"{value * 100:.1f}%"


def _fmt_multiple(value):
    """Format a multiple (P/E, PEG, etc.)."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "---"
    return f"{value:.2f}x"


def _fmt_plain(value):
    """Format a plain number."""
    if value is None:
        return "---"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "---"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _fmt_price(value):
    """Format a dollar price."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "---"
    return f"${value:,.2f}"


def _fmt_employees(value):
    """Format employee count."""
    if value is None:
        return "---"
    return f"{int(value):,}"


def _fmt_date_ts(value):
    """Format a Unix timestamp to a date string."""
    if value is None:
        return "---"
    try:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(value)


# ---------------------------------------------------------------------------
# Metric extraction with formatting
# ---------------------------------------------------------------------------

def _extract_metric(info: dict, key: str, formatter=_fmt_plain) -> dict:
    """Extract a single metric from info dict, format it, attach tooltip."""
    raw = info.get(key)
    return {
        "key": key,
        "raw": raw,
        "formatted": formatter(raw),
        "tooltip": METRIC_TOOLTIPS.get(key, ""),
    }


# ---------------------------------------------------------------------------
# Grading functions
# ---------------------------------------------------------------------------

def _grade_valuation(info: dict) -> str:
    """Grade valuation based on P/E, PEG, and P/B."""
    scores = []

    pe = info.get("trailingPE")
    if pe is not None and isinstance(pe, (int, float)) and not math.isnan(pe):
        if pe < 0:
            scores.append(1)
        elif pe < 12:
            scores.append(5)
        elif pe < 18:
            scores.append(4)
        elif pe < 25:
            scores.append(3)
        elif pe < 35:
            scores.append(2)
        else:
            scores.append(1)

    peg = info.get("pegRatio")
    if peg is not None and isinstance(peg, (int, float)) and not math.isnan(peg):
        if peg < 0:
            scores.append(1)
        elif peg < 1:
            scores.append(5)
        elif peg < 1.5:
            scores.append(4)
        elif peg < 2:
            scores.append(3)
        elif peg < 3:
            scores.append(2)
        else:
            scores.append(1)

    pb = info.get("priceToBook")
    if pb is not None and isinstance(pb, (int, float)) and not math.isnan(pb):
        if pb < 0:
            scores.append(1)
        elif pb < 1.5:
            scores.append(5)
        elif pb < 3:
            scores.append(4)
        elif pb < 5:
            scores.append(3)
        elif pb < 10:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return "C"
    avg = sum(scores) / len(scores)
    return _num_to_grade(avg)


def _grade_profitability(info: dict) -> str:
    """Grade profitability based on ROE and operating margins."""
    scores = []

    roe = info.get("returnOnEquity")
    if roe is not None and isinstance(roe, (int, float)) and not math.isnan(roe):
        if roe > 0.25:
            scores.append(5)
        elif roe > 0.15:
            scores.append(4)
        elif roe > 0.08:
            scores.append(3)
        elif roe > 0:
            scores.append(2)
        else:
            scores.append(1)

    om = info.get("operatingMargins")
    if om is not None and isinstance(om, (int, float)) and not math.isnan(om):
        if om > 0.25:
            scores.append(5)
        elif om > 0.15:
            scores.append(4)
        elif om > 0.08:
            scores.append(3)
        elif om > 0:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return "C"
    avg = sum(scores) / len(scores)
    return _num_to_grade(avg)


def _grade_financial_health(info: dict) -> str:
    """Grade financial health based on current ratio and debt/equity."""
    scores = []

    cr = info.get("currentRatio")
    if cr is not None and isinstance(cr, (int, float)) and not math.isnan(cr):
        if cr > 2.0:
            scores.append(5)
        elif cr > 1.5:
            scores.append(4)
        elif cr > 1.0:
            scores.append(3)
        elif cr > 0.7:
            scores.append(2)
        else:
            scores.append(1)

    de = info.get("debtToEquity")
    if de is not None and isinstance(de, (int, float)) and not math.isnan(de):
        if de < 30:
            scores.append(5)
        elif de < 60:
            scores.append(4)
        elif de < 100:
            scores.append(3)
        elif de < 200:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return "C"
    avg = sum(scores) / len(scores)
    return _num_to_grade(avg)


def _grade_growth(info: dict) -> str:
    """Grade growth based on revenue and earnings growth."""
    scores = []

    rg = info.get("revenueGrowth")
    if rg is not None and isinstance(rg, (int, float)) and not math.isnan(rg):
        if rg > 0.20:
            scores.append(5)
        elif rg > 0.10:
            scores.append(4)
        elif rg > 0.03:
            scores.append(3)
        elif rg > 0:
            scores.append(2)
        else:
            scores.append(1)

    eg = info.get("earningsGrowth")
    if eg is not None and isinstance(eg, (int, float)) and not math.isnan(eg):
        if eg > 0.25:
            scores.append(5)
        elif eg > 0.10:
            scores.append(4)
        elif eg > 0.03:
            scores.append(3)
        elif eg > 0:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return "C"
    avg = sum(scores) / len(scores)
    return _num_to_grade(avg)


def _grade_dividends(info: dict) -> str | None:
    """Grade dividends. Returns None if no dividend."""
    dy = info.get("dividendYield")
    dr = info.get("dividendRate")
    if not dy and not dr:
        return None

    scores = []

    if dy is not None and isinstance(dy, (int, float)) and not math.isnan(dy):
        if dy > 0.04:
            scores.append(5)
        elif dy > 0.025:
            scores.append(4)
        elif dy > 0.01:
            scores.append(3)
        elif dy > 0:
            scores.append(2)
        else:
            scores.append(1)

    pr = info.get("payoutRatio")
    if pr is not None and isinstance(pr, (int, float)) and not math.isnan(pr):
        if 0 < pr <= 0.4:
            scores.append(5)
        elif pr <= 0.6:
            scores.append(4)
        elif pr <= 0.8:
            scores.append(3)
        elif pr <= 1.0:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return "C"
    avg = sum(scores) / len(scores)
    return _num_to_grade(avg)


def _num_to_grade(num: float) -> str:
    if num >= 4.5:
        return "A"
    if num >= 3.5:
        return "B"
    if num >= 2.5:
        return "C"
    if num >= 1.5:
        return "D"
    return "F"


def _grade_to_num(grade: str) -> float:
    return {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}.get(grade, 3)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_info_analysis(info: dict) -> dict:
    """Build a structured analysis from yfinance Ticker.info data.

    Returns a dict with profile, scorecard (graded sections), and sections
    (each containing rows with label/formatted/tooltip for table rendering).
    """

    # --- Company Profile ---
    profile = {
        "shortName": info.get("shortName", "---"),
        "sector": info.get("sector", "---"),
        "industry": info.get("industry", "---"),
        "country": info.get("country", "---"),
        "fullTimeEmployees": _fmt_employees(info.get("fullTimeEmployees")),
        "longBusinessSummary": info.get("longBusinessSummary", ""),
    }

    # --- Section definitions: (title, keys_with_formatters, grade_fn) ---
    section_defs = [
        ("Valuation", [
            ("marketCap", "Market Cap", _fmt_number),
            ("trailingPE", "Trailing P/E", _fmt_multiple),
            ("forwardPE", "Forward P/E", _fmt_multiple),
            ("pegRatio", "PEG Ratio", _fmt_multiple),
            ("priceToBook", "Price / Book", _fmt_multiple),
            ("priceToSalesTrailing12Months", "Price / Sales", _fmt_multiple),
            ("enterpriseToEbitda", "EV / EBITDA", _fmt_multiple),
            ("enterpriseToRevenue", "EV / Revenue", _fmt_multiple),
        ], _grade_valuation),
        ("Profitability", [
            ("profitMargins", "Profit Margin", _fmt_ratio),
            ("operatingMargins", "Operating Margin", _fmt_ratio),
            ("grossMargins", "Gross Margin", _fmt_ratio),
            ("ebitdaMargins", "EBITDA Margin", _fmt_ratio),
            ("returnOnEquity", "Return on Equity", _fmt_ratio),
            ("returnOnAssets", "Return on Assets", _fmt_ratio),
        ], _grade_profitability),
        ("Financial Health", [
            ("currentRatio", "Current Ratio", _fmt_multiple),
            ("quickRatio", "Quick Ratio", _fmt_multiple),
            ("debtToEquity", "Debt / Equity", _fmt_plain),
            ("totalDebt", "Total Debt", _fmt_number),
            ("totalCash", "Total Cash", _fmt_number),
        ], _grade_financial_health),
        ("Growth", [
            ("revenueGrowth", "Revenue Growth", _fmt_ratio),
            ("earningsGrowth", "Earnings Growth", _fmt_ratio),
            ("earningsQuarterlyGrowth", "Quarterly Earnings Growth", _fmt_ratio),
        ], _grade_growth),
        ("Dividends", [
            ("dividendYield", "Dividend Yield", _fmt_ratio),
            ("dividendRate", "Dividend Rate", _fmt_price),
            ("payoutRatio", "Payout Ratio", _fmt_ratio),
            ("fiveYearAvgDividendYield", "5Y Avg Dividend Yield", _fmt_ratio),
            ("exDividendDate", "Ex-Dividend Date", _fmt_date_ts),
        ], _grade_dividends),
        ("Price & Trading", [
            ("currentPrice", "Current Price", _fmt_price),
            ("fiftyTwoWeekHigh", "52-Week High", _fmt_price),
            ("fiftyTwoWeekLow", "52-Week Low", _fmt_price),
            ("fiftyTwoWeekChange", "52-Week Change", _fmt_ratio),
            ("beta", "Beta", _fmt_plain),
            ("fiftyDayAverage", "50-Day Average", _fmt_price),
            ("twoHundredDayAverage", "200-Day Average", _fmt_price),
        ], None),  # no grade
    ]

    sections = []
    scorecard = []

    for title, keys, grade_fn in section_defs:
        grade = grade_fn(info) if grade_fn else None

        rows = []
        for key, label, fmt in keys:
            raw = info.get(key)
            rows.append({
                "key": key,
                "label": label,
                "formatted": fmt(raw),
                "tooltip": METRIC_TOOLTIPS.get(key, ""),
            })

        sections.append({
            "title": title,
            "grade": grade,
            "rows": rows,
        })

        if grade is not None:
            scorecard.append({"label": title, "grade": grade})

    # --- Overall Grade ---
    graded = [s["grade"] for s in sections if s["grade"] is not None]
    overall_grade = _num_to_grade(
        sum(_grade_to_num(g) for g in graded) / len(graded)
    ) if graded else "C"

    scorecard.insert(0, {"label": "Overall", "grade": overall_grade})

    return {
        "profile": profile,
        "scorecard": scorecard,
        "sections": sections,
    }


def _parse_html_table(html: str) -> dict:
    """Parse a Key/Value HTML table (from api-explorer) back into a dict."""
    from html.parser import HTMLParser

    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_td = False
            self.cells = []
            self.current = ""

        def handle_starttag(self, tag, attrs):
            if tag == "td":
                self.in_td = True
                self.current = ""

        def handle_endtag(self, tag):
            if tag == "td":
                self.in_td = False
                self.cells.append(self.current)

        def handle_data(self, data):
            if self.in_td:
                self.current += data

    parser = TableParser()
    parser.feed(html)

    result = {}
    for i in range(0, len(parser.cells) - 1, 2):
        key = parser.cells[i]
        val_str = parser.cells[i + 1]
        result[key] = _coerce_value(val_str)
    return result


def _coerce_value(val_str: str):
    """Try to convert a string value back to its original Python type."""
    if val_str in ("None", ""):
        return None
    if val_str == "True":
        return True
    if val_str == "False":
        return False
    # Try int
    try:
        return int(val_str)
    except ValueError:
        pass
    # Try float
    try:
        return float(val_str)
    except ValueError:
        pass
    return val_str


def get_stock_info(ticker_symbol: str, force_refresh: bool = False, api_explorer_url: str = "http://localhost:8000") -> dict:
    """Fetch stock info from api-explorer and build analysis."""
    import httpx

    ticker_symbol = ticker_symbol.strip().upper()
    cache_key = "info_analysis"

    if not force_refresh:
        cached = get_cached(ticker_symbol, cache_key)
        if cached:
            return json.loads(cached.data)

    # Fetch from api-explorer
    api_url = f"{api_explorer_url}/api/data"
    resp = httpx.post(
        api_url,
        json={"ticker": ticker_symbol, "method": "info", "force_refresh": force_refresh},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    html = data.get("html", "")
    if "<p class='error'>" in html or "<p class='empty'>" in html:
        raise ValueError(f"No info data found for {ticker_symbol}")

    info = _parse_html_table(html)

    if not info or not info.get("shortName"):
        raise ValueError(f"No info data found for {ticker_symbol}")

    result = build_info_analysis(info)
    set_cached(ticker_symbol, cache_key, json.dumps(result))
    return result
