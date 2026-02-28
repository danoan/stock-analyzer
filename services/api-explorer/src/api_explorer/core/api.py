import json
import math
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from api_explorer.core.model import CacheEntry, LookupCache

_ticker_cache: dict[str, yf.Ticker] = {}


def get_ticker(symbol: str) -> yf.Ticker:
    symbol = symbol.upper().strip()
    if symbol not in _ticker_cache:
        _ticker_cache[symbol] = yf.Ticker(symbol)
    return _ticker_cache[symbol]


def get_cached(ticker: str, method: str, period: str = "1mo") -> CacheEntry | None:
    try:
        return CacheEntry.get(
            (CacheEntry.ticker == ticker)
            & (CacheEntry.method == method)
            & (CacheEntry.period == period)
        )
    except CacheEntry.DoesNotExist:
        return None


def set_cached(ticker: str, method: str, period: str, data_json: str) -> CacheEntry:
    now = datetime.now(timezone.utc)
    entry, created = CacheEntry.get_or_create(
        ticker=ticker,
        method=method,
        period=period,
        defaults={"data_json": data_json, "cached_at": now},
    )
    if not created:
        entry.data_json = data_json
        entry.cached_at = now
        entry.save()
    return entry


METHOD_REGISTRY = {
    # Financials
    "income_stmt": "Financials",
    "quarterly_income_stmt": "Financials",
    "balance_sheet": "Financials",
    "quarterly_balance_sheet": "Financials",
    "cashflow": "Financials",
    "quarterly_cashflow": "Financials",
    "earnings": "Financials",
    "earnings_dates": "Financials",
    "calendar": "Financials",
    "sec_filings": "Financials",
    # Analysis & Holdings
    "recommendations": "Analysis & Holdings",
    "recommendations_summary": "Analysis & Holdings",
    "upgrades_downgrades": "Analysis & Holdings",
    "sustainability": "Analysis & Holdings",
    "analyst_price_targets": "Analysis & Holdings",
    "earnings_estimate": "Analysis & Holdings",
    "revenue_estimate": "Analysis & Holdings",
    "earnings_history": "Analysis & Holdings",
    "eps_trend": "Analysis & Holdings",
    "eps_revisions": "Analysis & Holdings",
    "growth_estimates": "Analysis & Holdings",
    "insider_purchases": "Analysis & Holdings",
    "insider_transactions": "Analysis & Holdings",
    "insider_roster_holders": "Analysis & Holdings",
    "major_holders": "Analysis & Holdings",
    "institutional_holders": "Analysis & Holdings",
    "mutualfund_holders": "Analysis & Holdings",
    # Stock
    "history": "Stock",
    "dividends": "Stock",
    "splits": "Stock",
    "actions": "Stock",
    "capital_gains": "Stock",
    "info": "Stock",
    "fast_info": "Stock",
    "isin": "Stock",
    "news": "Stock",
    "history_metadata": "Stock",
}

CATEGORIES: dict[str, list[str]] = {}
for _method, _cat in METHOD_REGISTRY.items():
    CATEGORIES.setdefault(_cat, []).append(_method)


def _sanitize(obj):
    """Recursively replace non-JSON-compliant floats (nan, inf) with None."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def fetch_raw_data(ticker_symbol: str, method_name: str, period: str = "1mo") -> dict:
    """Fetch data from yfinance and return a JSON-serializable intermediate payload."""
    if method_name not in METHOD_REGISTRY:
        return {"type": "error", "message": f"Unknown method: {method_name}"}

    ticker = get_ticker(ticker_symbol)

    try:
        if method_name == "history":
            result = ticker.history(period=period)
        elif method_name == "fast_info":
            result = dict(ticker.fast_info)
        else:
            result = getattr(ticker, method_name)
    except Exception as e:
        return {"type": "error", "message": f"Error fetching {method_name}: {e}"}

    if result is None:
        return {"type": "empty", "message": f"No data returned for {method_name}"}

    # DataFrame — use pandas JSON serialization so NaN/Inf become null
    if isinstance(result, pd.DataFrame):
        if result.empty:
            return {"type": "empty", "message": f"No data available for {method_name}"}
        df = result.copy()
        df.index = df.index.astype(str)
        df.columns = df.columns.astype(str)
        parsed = json.loads(df.to_json(orient="split"))
        return {
            "type": "dataframe",
            "columns": parsed["columns"],
            "index": parsed["index"],
            "data": parsed["data"],
        }

    # Series — same approach
    if isinstance(result, pd.Series):
        if result.empty:
            return {"type": "empty", "message": f"No data available for {method_name}"}
        result.index = result.index.astype(str)
        parsed = json.loads(result.to_json(orient="split"))
        return {
            "type": "series",
            "index": parsed["index"],
            "data": parsed["data"],
        }

    # Dict
    if isinstance(result, dict):
        if not result:
            return {"type": "empty", "message": f"No data available for {method_name}"}
        return {"type": "dict", "data": _sanitize({str(k): v for k, v in result.items()})}

    # List (e.g. sec_filings, news)
    if isinstance(result, list):
        if not result:
            return {"type": "empty", "message": f"No data available for {method_name}"}
        if isinstance(result[0], dict):
            if method_name == "news":
                rows = []
                for item in result:
                    c = item.get("content", {})
                    rows.append(
                        {
                            "title": c.get("title", ""),
                            "summary": c.get("summary", ""),
                            "pubDate": c.get("pubDate", ""),
                            "contentType": c.get("contentType", ""),
                        }
                    )
                return {"type": "list", "data": rows}
            return {"type": "list", "data": _sanitize(result)}
        return {"type": "fallback", "data": str(result)}

    # Fallback
    return {"type": "fallback", "data": str(result)}


def render_html(payload: dict) -> str:
    """Convert an intermediate JSON payload to an HTML string."""
    ptype = payload.get("type")

    if ptype == "error":
        return f"<p class='error'>{payload['message']}</p>"

    if ptype == "empty":
        return f"<p class='empty'>{payload['message']}</p>"

    if ptype == "dataframe":
        df = pd.DataFrame(payload["data"], columns=payload["columns"], index=payload["index"])
        return df.to_html(classes="data-table", border=0, na_rep="—")

    if ptype == "series":
        series = pd.Series(payload["data"], index=payload["index"])
        return series.to_frame(name="Value").to_html(classes="data-table", border=0, na_rep="—")

    if ptype == "dict":
        rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in payload["data"].items())
        return (
            f'<table class="data-table"><thead><tr><th>Key</th><th>Value</th></tr>'
            f"</thead><tbody>{rows}</tbody></table>"
        )

    if ptype == "list":
        df = pd.DataFrame(payload["data"])
        return df.to_html(classes="data-table", border=0, na_rep="—", index=False)

    if ptype == "fallback":
        return f"<pre>{payload['data']}</pre>"

    return f"<p class='error'>Unknown payload type: {ptype}</p>"


def get_data(
    ticker: str, method: str, force_refresh: bool = False, period: str = "1mo"
) -> tuple[dict, bool, datetime | str | None]:
    """Orchestrate cache check, raw data fetch, and persistence.

    Returns (payload, from_cache, cached_at).
    """
    if not force_refresh:
        cached = get_cached(ticker, method, period)
        if cached:
            payload = json.loads(cached.data_json)
            return payload, True, cached.cached_at

    payload = fetch_raw_data(ticker, method, period)
    entry = set_cached(ticker, method, period, json.dumps(payload, default=str))
    return payload, False, entry.cached_at


def lookup(query: str, count: int = 8, cache_only: bool = False) -> dict:
    """Look up ticker symbols matching a query. Returns dict with results and from_cache."""
    q = query.strip()
    if not q:
        return {"results": [], "from_cache": False}

    cache_key = q.lower()

    # Check cache
    try:
        cached = LookupCache.get(LookupCache.query == cache_key)
        return {
            "results": json.loads(cached.results_json),
            "from_cache": True,
        }
    except LookupCache.DoesNotExist:
        pass

    if cache_only:
        return {"results": [], "from_cache": False}

    try:
        df = yf.Lookup(q).get_all(count=count)
        if df is None or df.empty:
            results: list[dict] = []
        else:
            df = df.reset_index()[["symbol", "shortName", "exchange", "quoteType"]].fillna("")
            results = df.to_dict(orient="records")
    except Exception:
        results = []

    now = datetime.now(timezone.utc)
    LookupCache.insert(
        query=cache_key,
        results_json=json.dumps(results),
        cached_at=now,
    ).on_conflict(
        conflict_target=[LookupCache.query],
        update={
            LookupCache.results_json: json.dumps(results),
            LookupCache.cached_at: now,
        },
    ).execute()

    return {"results": results, "from_cache": False}
