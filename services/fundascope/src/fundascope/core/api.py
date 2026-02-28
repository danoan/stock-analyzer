"""Financial statement analysis: formatting, growth, margins, dividend safety, scorecard."""

import json
import math

import numpy as np
import pandas as pd
import yfinance as yf

from fundascope.core.cache import get_cached, set_cached
from fundascope.core.model import KEY_METRICS, METRIC_DEFINITIONS

# Maps statement_type values to yfinance Ticker attribute names
STATEMENT_ATTR: dict[str, str] = {
    "income_stmt": "income_stmt",
    "quarterly_income_stmt": "quarterly_income_stmt",
    "balance_sheet": "balance_sheet",
    "quarterly_balance_sheet": "quarterly_balance_sheet",
    "cashflow": "cashflow",
    "quarterly_cashflow": "quarterly_cashflow",
}

# Which base type each statement maps to (for KEY_METRICS lookup)
_BASE_TYPE: dict[str, str] = {
    "income_stmt": "income_stmt",
    "quarterly_income_stmt": "income_stmt",
    "balance_sheet": "balance_sheet",
    "quarterly_balance_sheet": "balance_sheet",
    "cashflow": "cashflow",
    "quarterly_cashflow": "cashflow",
}

_INCOME_TYPES = {"income_stmt", "quarterly_income_stmt"}


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------

def format_number(value, metric_key: str = "", statement_type: str = "income_stmt") -> str:
    """Format a raw number into human-readable form."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "---"

    is_income = statement_type in _INCOME_TYPES

    # EPS metrics: show as dollar amount with 2 decimals (income statement only)
    if is_income and "EPS" in metric_key:
        return f"${value:.2f}"

    # Share counts: show with B/M suffix, no dollar sign (income statement only)
    if is_income and ("Shares" in metric_key or "Average Shares" in metric_key):
        return _abbreviate(value, prefix="")

    # Tax rate: show as percentage (income statement only)
    if is_income and metric_key == "Tax Rate For Calcs":
        return f"{value * 100:.1f}%"

    # Share/count metrics on balance sheet
    if metric_key in ("Ordinary Shares Number", "Share Issued", "Treasury Shares Number"):
        return _abbreviate(value, prefix="")

    # Everything else: dollar abbreviation
    return _abbreviate(value, prefix="$")


def _abbreviate(value, prefix: str = "$") -> str:
    """Convert large numbers to abbreviated form like $73.8B."""
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


# ---------------------------------------------------------------------------
# YoY growth
# ---------------------------------------------------------------------------

def compute_yoy_growth(current, previous) -> dict | None:
    """Compute year-over-year growth between two values."""
    if current is None or previous is None:
        return None
    if isinstance(current, float) and (math.isnan(current) or math.isinf(current)):
        return None
    if isinstance(previous, float) and (math.isnan(previous) or math.isinf(previous)):
        return None
    if previous == 0:
        return None

    growth = (current - previous) / abs(previous)
    abs_growth = abs(growth)

    if abs_growth < 0.01:
        trend = "flat"
    elif growth > 0:
        trend = "up"
    else:
        trend = "down"

    sign = "+" if growth >= 0 else ""
    formatted = f"{sign}{growth * 100:.1f}%"

    return {"raw": growth, "formatted": formatted, "trend": trend}


# ---------------------------------------------------------------------------
# Margins
# ---------------------------------------------------------------------------

def compute_margins(stmt: pd.DataFrame) -> dict:
    """Compute key margin ratios per year."""
    margins = {}
    for col in stmt.columns:
        year_key = str(col.date()) if hasattr(col, "date") else str(col)
        revenue = _get_value(stmt, "Total Revenue", col)
        if not revenue or revenue == 0:
            continue

        margins[year_key] = {}
        for label, metric in [
            ("gross", "Gross Profit"),
            ("operating", "Operating Income"),
            ("net", "Net Income"),
            ("ebitda", "EBITDA"),
        ]:
            val = _get_value(stmt, metric, col)
            if val is not None:
                ratio = val / revenue
                margins[year_key][label] = ratio
                margins[year_key][f"{label}_formatted"] = f"{ratio * 100:.1f}%"
            else:
                margins[year_key][label] = None
                margins[year_key][f"{label}_formatted"] = "---"

    return margins


# ---------------------------------------------------------------------------
# Dividend safety
# ---------------------------------------------------------------------------

def compute_dividend_safety(ticker: yf.Ticker, stmt: pd.DataFrame) -> dict:
    """Compute a weighted dividend safety score (1-5 scale)."""
    info = ticker.info or {}

    payout_ratio = info.get("payoutRatio")
    dividend_yield = info.get("dividendYield")
    trailing_dividend = info.get("trailingAnnualDividendRate", 0)

    # No dividend?
    if not trailing_dividend and not dividend_yield:
        return {
            "pays_dividend": False,
            "label": "No Dividend",
            "safety_score": None,
            "payout_ratio": None,
            "payout_ratio_formatted": "---",
            "components": {},
        }

    # Extract net income series for trend analysis
    net_incomes = _get_metric_series(stmt, "Net Income")
    operating_margins = _get_margin_series(stmt, "Operating Income", "Total Revenue")
    revenues = _get_metric_series(stmt, "Total Revenue")

    # 1. Payout ratio score (30%)
    payout_score = _score_payout_ratio(payout_ratio)

    # 2. Net income trend (25%)
    income_trend_score = _score_trend(net_incomes)

    # 3. Earnings stability (20%)
    stability_score = _score_stability(net_incomes)

    # 4. Operating margin level (15%)
    margin_score = _score_margin_level(operating_margins)

    # 5. Revenue growth trend (10%)
    revenue_trend_score = _score_trend(revenues)

    # Weighted total
    weighted = (
        payout_score * 0.30
        + income_trend_score * 0.25
        + stability_score * 0.20
        + margin_score * 0.15
        + revenue_trend_score * 0.10
    )
    safety_score = max(1, min(5, round(weighted)))

    labels = {5: "Very Safe", 4: "Safe", 3: "Borderline", 2: "Unsafe", 1: "Dangerous"}

    return {
        "pays_dividend": True,
        "safety_score": safety_score,
        "label": labels[safety_score],
        "payout_ratio": payout_ratio,
        "payout_ratio_formatted": f"{payout_ratio * 100:.0f}%" if payout_ratio else "---",
        "components": {
            "payout_ratio_score": payout_score,
            "income_trend_score": income_trend_score,
            "stability_score": stability_score,
            "margin_score": margin_score,
            "revenue_trend_score": revenue_trend_score,
        },
    }


def _score_payout_ratio(ratio) -> float:
    if ratio is None:
        return 3.0
    if ratio < 0:
        return 1.0
    if ratio <= 0.3:
        return 5.0
    if ratio <= 0.5:
        return 4.0
    if ratio <= 0.7:
        return 3.0
    if ratio <= 0.9:
        return 2.0
    return 1.0


def _score_trend(values: list[float]) -> float:
    """Score based on whether values are generally increasing."""
    if len(values) < 2:
        return 3.0
    increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
    ratio = increases / (len(values) - 1)
    if ratio >= 0.75:
        return 5.0
    if ratio >= 0.5:
        return 4.0
    if ratio >= 0.25:
        return 2.0
    return 1.0


def _score_stability(values: list[float]) -> float:
    """Score based on coefficient of variation (lower = more stable)."""
    if len(values) < 2:
        return 3.0
    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    if mean == 0:
        return 3.0
    cv = np.std(arr) / abs(mean)
    if cv < 0.1:
        return 5.0
    if cv < 0.2:
        return 4.0
    if cv < 0.4:
        return 3.0
    if cv < 0.6:
        return 2.0
    return 1.0


def _score_margin_level(margins: list[float]) -> float:
    """Score based on average operating margin."""
    if not margins:
        return 3.0
    avg = np.mean(margins)
    if avg > 0.20:
        return 5.0
    if avg > 0.12:
        return 4.0
    if avg > 0.05:
        return 3.0
    if avg > 0:
        return 2.0
    return 1.0


# ---------------------------------------------------------------------------
# Health scorecard
# ---------------------------------------------------------------------------

def compute_health_scorecard(
    stmt: pd.DataFrame, margins: dict, dividend_safety: dict
) -> dict:
    """Compute the top-level health scorecard with 6 cards."""
    revenues = _get_metric_series(stmt, "Total Revenue")
    net_incomes = _get_metric_series(stmt, "Net Income")
    operating_incomes = _get_metric_series(stmt, "Operating Income")

    # Revenue growth
    rev_growth = _compute_cagr(revenues) if len(revenues) >= 2 else None
    rev_growth_fmt = f"{rev_growth * 100:+.1f}%" if rev_growth is not None else "---"

    # Profit trend
    profit_direction = _trend_direction(net_incomes)

    # Margin health
    margin_vals = [m.get("operating") for m in margins.values() if m.get("operating") is not None]
    margin_health = _margin_health_label(margin_vals)

    # Earnings quality
    earnings_quality = _earnings_quality(net_incomes, operating_incomes)

    # Dividend safety label
    div_label = dividend_safety.get("label", "N/A")

    # Overall grade
    scores = []
    if rev_growth is not None:
        scores.append(_grade_to_num(_grade_revenue_growth(rev_growth)))
    scores.append(_grade_to_num(_grade_profit_trend(profit_direction)))
    scores.append(_grade_to_num(_grade_margin_health(margin_health)))
    scores.append(_grade_to_num(_grade_earnings_quality(earnings_quality)))
    if dividend_safety.get("safety_score"):
        scores.append(_grade_to_num(_grade_dividend_safety(dividend_safety["safety_score"])))

    avg_score = np.mean(scores) if scores else 3
    overall_grade = _num_to_grade(avg_score)

    return {
        "overall_grade": overall_grade,
        "revenue_growth": rev_growth_fmt,
        "revenue_growth_grade": _grade_revenue_growth(rev_growth) if rev_growth is not None else "C",
        "profit_trend": profit_direction,
        "profit_trend_grade": _grade_profit_trend(profit_direction),
        "margin_health": margin_health,
        "margin_health_grade": _grade_margin_health(margin_health),
        "earnings_quality": earnings_quality,
        "earnings_quality_grade": _grade_earnings_quality(earnings_quality),
        "dividend_safety": div_label,
        "dividend_safety_grade": _grade_dividend_safety(dividend_safety.get("safety_score")) if dividend_safety.get("safety_score") else "C",
    }


def _compute_cagr(values: list[float]) -> float | None:
    if len(values) < 2 or values[0] <= 0:
        return None
    n = len(values) - 1
    end, start = values[-1], values[0]
    if start <= 0 or end <= 0:
        return None
    return (end / start) ** (1 / n) - 1


def _trend_direction(values: list[float]) -> str:
    if len(values) < 2:
        return "Stable"
    increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
    ratio = increases / (len(values) - 1)
    if ratio >= 0.66:
        return "Improving"
    if ratio >= 0.33:
        return "Mixed"
    return "Declining"


def _margin_health_label(margins: list[float]) -> str:
    if not margins:
        return "Unknown"
    avg = np.mean(margins)
    if avg > 0.15:
        return "Strong"
    if avg > 0.08:
        return "Moderate"
    if avg > 0:
        return "Weak"
    return "Negative"


def _earnings_quality(net_incomes: list[float], operating_incomes: list[float]) -> str:
    if not net_incomes or not operating_incomes:
        return "Unknown"
    # Check if net income tracks operating income (less manipulation)
    if len(net_incomes) < 2:
        return "Unknown"
    ni_stable = _score_stability(net_incomes) >= 3
    if all(n > 0 for n in net_incomes) and ni_stable:
        return "High"
    if all(n > 0 for n in net_incomes):
        return "Moderate"
    return "Low"


def _grade_revenue_growth(growth: float) -> str:
    if growth > 0.10:
        return "A"
    if growth > 0.05:
        return "B"
    if growth > 0:
        return "C"
    if growth > -0.05:
        return "D"
    return "F"


def _grade_profit_trend(direction: str) -> str:
    return {"Improving": "A", "Mixed": "C", "Declining": "F", "Stable": "B"}.get(direction, "C")


def _grade_margin_health(label: str) -> str:
    return {"Strong": "A", "Moderate": "B", "Weak": "D", "Negative": "F"}.get(label, "C")


def _grade_earnings_quality(label: str) -> str:
    return {"High": "A", "Moderate": "B", "Low": "D"}.get(label, "C")


def _grade_dividend_safety(score: int | None) -> str:
    if score is None:
        return "C"
    return {5: "A", 4: "B", 3: "C", 2: "D", 1: "F"}.get(score, "C")


def _grade_to_num(grade: str) -> float:
    return {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}.get(grade, 3)


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_value(stmt: pd.DataFrame, metric: str, col):
    """Safely get a value from the DataFrame."""
    if metric not in stmt.index:
        return None
    val = stmt.loc[metric, col]
    if pd.isna(val):
        return None
    return float(val)


def _get_metric_series(stmt: pd.DataFrame, metric: str) -> list[float]:
    """Get values for a metric across years, oldest first."""
    if metric not in stmt.index:
        return []
    row = stmt.loc[metric]
    values = []
    for col in reversed(stmt.columns):
        val = row[col]
        if pd.notna(val):
            values.append(float(val))
    return values


def _get_margin_series(stmt: pd.DataFrame, numerator: str, denominator: str) -> list[float]:
    """Get margin ratios across years, oldest first."""
    if numerator not in stmt.index or denominator not in stmt.index:
        return []
    margins = []
    for col in reversed(stmt.columns):
        num = _get_value(stmt, numerator, col)
        den = _get_value(stmt, denominator, col)
        if num is not None and den and den != 0:
            margins.append(num / den)
    return margins


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_analysis(
    ticker_symbol: str,
    force_refresh: bool = False,
    statement_type: str = "income_stmt",
) -> dict:
    """Build the full analysis response for a ticker and statement type."""
    ticker_symbol = ticker_symbol.strip().upper()

    if statement_type not in STATEMENT_ATTR:
        raise ValueError(f"Unknown statement type: {statement_type}")

    cache_key = f"{statement_type}_analysis"

    # Check cache
    if not force_refresh:
        cached = get_cached(ticker_symbol, cache_key)
        if cached:
            return json.loads(cached.data)

    ticker = yf.Ticker(ticker_symbol)
    attr_name = STATEMENT_ATTR[statement_type]
    stmt = getattr(ticker, attr_name, None)

    if stmt is None or stmt.empty:
        label = statement_type.replace("_", " ").title()
        raise ValueError(f"No {label} data found for {ticker_symbol}")

    base_type = _BASE_TYPE[statement_type]
    key_metrics = KEY_METRICS.get(base_type, set())
    is_income = statement_type in _INCOME_TYPES

    # Year columns (most recent first)
    years = [str(col.date()) if hasattr(col, "date") else str(col) for col in stmt.columns]

    # Build rows
    rows = []
    for metric in stmt.index.tolist():
        definition = METRIC_DEFINITIONS.get(metric, "")
        is_key = metric in key_metrics
        values = {}

        for i, col in enumerate(stmt.columns):
            year_key = years[i]
            raw = _get_value(stmt, metric, col)
            formatted = format_number(raw, metric, statement_type)

            yoy = None
            if i + 1 < len(stmt.columns):
                prev = _get_value(stmt, metric, stmt.columns[i + 1])
                yoy = compute_yoy_growth(raw, prev)

            values[year_key] = {
                "raw": raw,
                "formatted": formatted,
                "yoy_growth": yoy["raw"] if yoy else None,
                "yoy_formatted": yoy["formatted"] if yoy else None,
                "trend": yoy["trend"] if yoy else None,
            }

        rows.append({
            "key": metric.replace(" ", ""),
            "label": metric,
            "definition": definition,
            "is_key_metric": is_key,
            "values": values,
        })

    # Income-statement-specific panels
    if is_income:
        margins = compute_margins(stmt)
        dividend_safety = compute_dividend_safety(ticker, stmt)
        scorecard = compute_health_scorecard(stmt, margins, dividend_safety)
    else:
        margins = None
        dividend_safety = None
        scorecard = None

    result = {
        "ticker": ticker_symbol,
        "statement_type": statement_type,
        "years": years,
        "scorecard": scorecard,
        "margins": margins,
        "dividend_safety": dividend_safety,
        "rows": rows,
    }

    # Cache the result
    set_cached(ticker_symbol, cache_key, json.dumps(result))

    return result
