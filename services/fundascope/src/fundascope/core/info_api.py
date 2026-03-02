"""Stock info analysis: extracts, grades, and formats data from yfinance Ticker.info."""

import json
import math

import httpx

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

# Maps section title to the score id in the fundascope_info spec
_SECTION_SCORE_ID: dict[str, str] = {
    "Valuation": "valuation",
    "Profitability": "profitability",
    "Financial Health": "financial_health",
    "Growth": "growth",
    "Dividends": "dividends",
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
# Grading via stock-ranker score engine
# ---------------------------------------------------------------------------

def _fetch_grades(info: dict, stock_ranker_url: str) -> tuple[dict[str, str | None], str]:
    """Call stock-ranker POST /scores/evaluate and return (grades_by_id, overall_grade).

    On failure returns empty grades and overall_grade="C".
    """
    try:
        resp = httpx.post(
            f"{stock_ranker_url}/scores/evaluate",
            json={"spec_name": "fundascope_info", "info": info},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        grades_by_id: dict[str, str | None] = {
            r["id"]: r.get("grade") for r in data.get("results", [])
        }
        overall_grade: str = data.get("overall_grade") or "C"
        return grades_by_id, overall_grade
    except Exception:
        return {}, "C"


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_info_analysis(info: dict, stock_ranker_url: str) -> dict:
    """Build a structured analysis from yfinance Ticker.info data.

    Returns a dict with profile, scorecard (graded sections), and sections
    (each containing rows with label/formatted/tooltip for table rendering).
    Grades are computed by calling the stock-ranker score engine.
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

    # --- Fetch grades from stock-ranker ---
    grades_by_id, overall_grade = _fetch_grades(info, stock_ranker_url)

    # --- Section definitions: (title, keys_with_formatters) ---
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
        ]),
        ("Profitability", [
            ("profitMargins", "Profit Margin", _fmt_ratio),
            ("operatingMargins", "Operating Margin", _fmt_ratio),
            ("grossMargins", "Gross Margin", _fmt_ratio),
            ("ebitdaMargins", "EBITDA Margin", _fmt_ratio),
            ("returnOnEquity", "Return on Equity", _fmt_ratio),
            ("returnOnAssets", "Return on Assets", _fmt_ratio),
        ]),
        ("Financial Health", [
            ("currentRatio", "Current Ratio", _fmt_multiple),
            ("quickRatio", "Quick Ratio", _fmt_multiple),
            ("debtToEquity", "Debt / Equity", _fmt_plain),
            ("totalDebt", "Total Debt", _fmt_number),
            ("totalCash", "Total Cash", _fmt_number),
        ]),
        ("Growth", [
            ("revenueGrowth", "Revenue Growth", _fmt_ratio),
            ("earningsGrowth", "Earnings Growth", _fmt_ratio),
            ("earningsQuarterlyGrowth", "Quarterly Earnings Growth", _fmt_ratio),
        ]),
        ("Dividends", [
            ("dividendYield", "Dividend Yield", _fmt_ratio),
            ("dividendRate", "Dividend Rate", _fmt_price),
            ("payoutRatio", "Payout Ratio", _fmt_ratio),
            ("fiveYearAvgDividendYield", "5Y Avg Dividend Yield", _fmt_ratio),
            ("exDividendDate", "Ex-Dividend Date", _fmt_date_ts),
        ]),
        ("Price & Trading", [
            ("currentPrice", "Current Price", _fmt_price),
            ("fiftyTwoWeekHigh", "52-Week High", _fmt_price),
            ("fiftyTwoWeekLow", "52-Week Low", _fmt_price),
            ("fiftyTwoWeekChange", "52-Week Change", _fmt_ratio),
            ("beta", "Beta", _fmt_plain),
            ("fiftyDayAverage", "50-Day Average", _fmt_price),
            ("twoHundredDayAverage", "200-Day Average", _fmt_price),
        ]),
    ]

    sections = []
    scorecard = []

    for title, keys in section_defs:
        score_id = _SECTION_SCORE_ID.get(title)
        grade = grades_by_id.get(score_id) if score_id else None

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


def get_stock_info(
    ticker_symbol: str,
    force_refresh: bool = False,
    api_explorer_url: str = "http://localhost:8000",
    stock_ranker_url: str = "http://localhost:8001",
) -> dict:
    """Fetch stock info from api-explorer and build analysis."""
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

    result = build_info_analysis(info, stock_ranker_url)
    set_cached(ticker_symbol, cache_key, json.dumps(result))
    return result
