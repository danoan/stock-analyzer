from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from simpleeval import EvalWithCompoundTypes, NameNotDefined

from stock_ranker.core.model import (
    Analysis,
    AnalysisDB,
    Collection,
    CollectionDB,
    LookupResult,
    RealizationDB,
    RealizationResult,
    Score,
    ScoreDetail,
    Ticker,
    TickerCollectionDB,
    TickerDB,
)
from stock_ranker.utils.config import settings

# ---------------------------------------------------------------------------
# HTTP client helpers
# ---------------------------------------------------------------------------


def fetch_info(ticker: str, force_refresh: bool = False) -> dict[str, Any]:
    """Fetch stock info from api-explorer. Returns the data dict."""
    url = f"{settings.api_explorer_url}/api/data/json"
    payload = {"ticker": ticker, "method": "info", "force_refresh": force_refresh}
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
    body = resp.json()
    data = body.get("data", {})
    if data.get("type") != "dict":
        raise ValueError(
            f"Unexpected data type for {ticker}: {data.get('type')} — {data.get('message', '')}"
        )
    return data["data"]


def lookup_tickers(query: str, count: int = 8) -> list[LookupResult]:
    """Search for tickers via api-explorer /api/lookup."""
    url = f"{settings.api_explorer_url}/api/lookup"
    payload = {"query": query, "count": count}
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
    body = resp.json()
    results = body.get("results", [])
    return [LookupResult(**r) for r in results]


def get_available_metrics(sample_ticker: str = "AAPL") -> list[str]:
    """Return sorted list of numeric field names from the info endpoint."""
    info = fetch_info(sample_ticker)
    return sorted(k for k, v in info.items() if isinstance(v, (int, float)) and v is not None)


# ---------------------------------------------------------------------------
# Expression evaluation
# ---------------------------------------------------------------------------

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "log": math.log,
    "sqrt": math.sqrt,
    "exp": math.exp,
}


def _extract_identifiers(expression: str) -> set[str]:
    """Return variable names referenced in an expression, excluding known function names."""
    reserved = set(_ALLOWED_FUNCTIONS.keys()) | {"True", "False", "None"}
    return {m for m in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", expression) if m not in reserved}


def evaluate_expression(expression: str, variables: dict[str, float | None]) -> float | None:
    """Evaluate a mathematical expression with the given variables.

    Returns None if any variable is None/NaN/Inf, or on any evaluation error.
    """
    for v in variables.values():
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None

    evaluator = EvalWithCompoundTypes(
        names=variables,
        functions=_ALLOWED_FUNCTIONS,
    )
    try:
        result = evaluator.eval(expression)
    except (NameNotDefined, Exception):
        return None

    if not isinstance(result, (int, float)):
        return None
    result = float(result)
    if math.isnan(result) or math.isinf(result):
        return None
    return result


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------


def _to_numeric(value: Any) -> float | None:
    """Convert a value to float, returning None for non-numeric types."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    return None


def _normalize_values(values: list[float | None]) -> list[float | None]:
    """Min-max normalize values to [0, 1].

    - None stays None.
    - If all values are None, returns all None.
    - If span == 0, all non-None values become 0.5.
    """
    numeric = [v for v in values if v is not None]
    if not numeric:
        return [None] * len(values)

    vmin = min(numeric)
    vmax = max(numeric)
    span = vmax - vmin

    result: list[float | None] = []
    for v in values:
        if v is None:
            result.append(None)
        elif span == 0:
            result.append(0.5)
        else:
            result.append((v - vmin) / span)
    return result


def compute_score(
    score: Score, info_data: dict[str, Any]
) -> tuple[float | None, ScoreDetail]:
    """Compute a score for one ticker given its info data.

    Returns (raw_result, detail). The 'result' in detail equals raw_result here;
    normalization across tickers is applied later in realize_analysis if score.normalize=True.
    """
    all_variables: dict[str, float | None] = {k: _to_numeric(v) for k, v in info_data.items()}
    referenced = _extract_identifiers(score.expression)
    expr_variables = {name: all_variables.get(name) for name in referenced}
    raw_result = evaluate_expression(score.expression, expr_variables)
    detail = ScoreDetail(
        expression=score.expression,
        normalize=score.normalize,
        variables={name: all_variables.get(name) for name in sorted(referenced)},
        raw_result=raw_result,
        result=raw_result,
    )
    return raw_result, detail


# ---------------------------------------------------------------------------
# Realization
# ---------------------------------------------------------------------------


def realize_analysis(
    analysis: Analysis,
    tickers: list[str],
    force_refresh: bool = False,
) -> list[RealizationResult]:
    """Run all scores in an analysis against the given tickers.

    Fetches info for each ticker (errors are captured per-ticker).
    Persists results to RealizationDB.
    Returns list of RealizationResult.
    """
    # 1. Fetch info for each ticker
    ticker_info: dict[str, dict[str, Any]] = {}
    ticker_errors: dict[str, str] = {}

    for symbol in tickers:
        try:
            ticker_info[symbol] = fetch_info(symbol, force_refresh=force_refresh)
        except Exception as e:
            ticker_errors[symbol] = str(e)

    # 2. Compute raw scores per ticker
    # scores_dict[symbol][score_name] = raw_result
    # details_dict[symbol][score_name] = ScoreDetail
    scores_dict: dict[str, dict[str, float | None]] = {t: {} for t in tickers}
    details_dict: dict[str, dict[str, ScoreDetail]] = {t: {} for t in tickers}

    for score in analysis.scores:
        # Collect raw results for all tickers that have info
        raw_results: dict[str, float | None] = {}
        raw_details: dict[str, ScoreDetail] = {}
        for symbol, info in ticker_info.items():
            raw_val, detail = compute_score(score, info)
            raw_results[symbol] = raw_val
            raw_details[symbol] = detail

        if score.normalize and raw_results:
            # Normalize across all tickers (including those with errors → treat as None)
            all_raw = [raw_results.get(sym) for sym in tickers]
            normalized = _normalize_values(all_raw)
            for i, symbol in enumerate(tickers):
                if symbol in raw_details:
                    norm_val = normalized[i]
                    detail = raw_details[symbol]
                    # Replace result with normalized value
                    raw_details[symbol] = ScoreDetail(
                        expression=detail.expression,
                        normalize=detail.normalize,
                        variables=detail.variables,
                        raw_result=detail.raw_result,
                        result=norm_val,
                    )
                    raw_results[symbol] = norm_val

        for symbol in ticker_info:
            scores_dict[symbol][score.name] = raw_results[symbol]
            details_dict[symbol][score.name] = raw_details[symbol]

    # 3. Build and persist results
    now = datetime.now(UTC)
    db_analysis = AnalysisDB.get_by_id(analysis.id)
    realization_results: list[RealizationResult] = []

    for symbol in tickers:
        error = ticker_errors.get(symbol)
        final_scores: dict[str, float | None] = {}
        final_details: dict[str, ScoreDetail] = {}
        if error is None:
            final_scores.update(scores_dict.get(symbol, {}))
            final_details.update(details_dict.get(symbol, {}))

        result = RealizationResult(
            ticker_symbol=symbol,
            scores=final_scores,
            score_details=final_details,
            error=error,
        )
        realization_results.append(result)

        RealizationDB.create(
            analysis=db_analysis,
            ticker_symbol=symbol,
            run_at=now,
            results_json=json.dumps(final_scores),
            error=error,
        )

    return realization_results


# ---------------------------------------------------------------------------
# CRUD — Analysis
# ---------------------------------------------------------------------------


def list_analyses() -> list[Analysis]:
    return [Analysis.from_db(a) for a in AnalysisDB.select()]


def get_analysis(analysis_id: int) -> Analysis | None:
    try:
        return Analysis.from_db(AnalysisDB.get_by_id(analysis_id))
    except AnalysisDB.DoesNotExist:
        return None


def get_analysis_by_name(name: str) -> Analysis | None:
    try:
        return Analysis.from_db(AnalysisDB.get(AnalysisDB.name == name))
    except AnalysisDB.DoesNotExist:
        return None


def create_analysis(analysis: Analysis) -> Analysis:
    record = AnalysisDB.create(**analysis.to_db_dict())
    return Analysis.from_db(record)


def update_analysis(analysis: Analysis) -> Analysis:
    AnalysisDB.update(**analysis.to_db_dict()).where(AnalysisDB.id == analysis.id).execute()
    return get_analysis(analysis.id)  # type: ignore[arg-type]


def delete_analysis(analysis_id: int) -> bool:
    count = AnalysisDB.delete().where(AnalysisDB.id == analysis_id).execute()
    return count > 0


# ---------------------------------------------------------------------------
# CRUD — Collections & Tickers
# ---------------------------------------------------------------------------


def list_collections() -> list[Collection]:
    collections = []
    for col in CollectionDB.select():
        tickers = []
        for tc in TickerCollectionDB.select().where(TickerCollectionDB.collection == col):
            tickers.append(Ticker(symbol=tc.ticker.symbol, name=tc.ticker.name))
        collections.append(Collection(id=col.id, name=col.name, tickers=tickers))
    return collections


def get_collection_by_name(name: str) -> Collection | None:
    try:
        col = CollectionDB.get(CollectionDB.name == name)
    except CollectionDB.DoesNotExist:
        return None
    tickers = []
    for tc in TickerCollectionDB.select().where(TickerCollectionDB.collection == col):
        tickers.append(Ticker(symbol=tc.ticker.symbol, name=tc.ticker.name))
    return Collection(id=col.id, name=col.name, tickers=tickers)


def create_collection(name: str) -> Collection:
    col = CollectionDB.create(name=name)
    return Collection(id=col.id, name=col.name, tickers=[])


def delete_collection(name: str) -> bool:
    try:
        col = CollectionDB.get(CollectionDB.name == name)
    except CollectionDB.DoesNotExist:
        return False
    TickerCollectionDB.delete().where(TickerCollectionDB.collection == col).execute()
    col.delete_instance()
    return True


def add_ticker_to_collection(
    symbol: str,
    collection_name: str,
    ticker_name: str = "",
) -> bool:
    """Add a ticker to a collection. Creates the ticker if it doesn't exist."""
    try:
        col = CollectionDB.get(CollectionDB.name == collection_name)
    except CollectionDB.DoesNotExist:
        return False

    ticker, _ = TickerDB.get_or_create(symbol=symbol.upper(), defaults={"name": ticker_name})
    if ticker_name and ticker.name != ticker_name:
        ticker.name = ticker_name
        ticker.save()

    TickerCollectionDB.get_or_create(ticker=ticker, collection=col)
    return True


def remove_ticker_from_collection(symbol: str, collection_name: str) -> bool:
    try:
        col = CollectionDB.get(CollectionDB.name == collection_name)
        ticker = TickerDB.get(TickerDB.symbol == symbol.upper())
    except (CollectionDB.DoesNotExist, TickerDB.DoesNotExist):
        return False
    count = (
        TickerCollectionDB.delete()
        .where(
            (TickerCollectionDB.ticker == ticker)
            & (TickerCollectionDB.collection == col)
        )
        .execute()
    )
    return count > 0


def list_all_tickers() -> list[Ticker]:
    return [Ticker(symbol=t.symbol, name=t.name) for t in TickerDB.select()]
