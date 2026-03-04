from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import httpx

from stock_ranker.core.model import (
    Analysis,
    AnalysisDB,
    Collection,
    CollectionDB,
    LibraryScore,
    LookupResult,
    RealizationDB,
    RealizationResult,
    Score,
    ScoreDetail,
    ScoreLibraryDB,
    SpecDB,
    Ticker,
    TickerCollectionDB,
    TickerDB,
)
from stock_ranker.core.score_engine import (
    _extract_identifiers,
    _extract_weight_and_base,
    _normalize_values,
    _split_additive_terms,
    _to_numeric,
    evaluate_expression,
    evaluate_spec,
    evaluate_threshold_score,
    load_spec_from_str,
    score_metric,
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
# Score computation
# ---------------------------------------------------------------------------


def compute_score(
    score: Score,
    info_data: dict[str, Any],
    score_vars: dict[str, float | None] | None = None,
) -> tuple[float | None, ScoreDetail]:
    """Compute a score for one ticker given its info data.

    Returns (raw_result, detail). The 'result' in detail equals raw_result here;
    normalization across tickers is applied later in realize_analysis if score.normalize=True.
    score_vars, if provided, injects previous scores' raw values so an expression
    score can reference an earlier score by name.
    """
    all_variables: dict[str, float | None] = {k: _to_numeric(v) for k, v in info_data.items()}
    if score_vars:
        all_variables.update(score_vars)
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

    # Pre-compute threshold scores from all specs so expression scores can reference them.
    spec_score_vars: dict[str, dict[str, float | None]] = {}  # symbol -> {score_id: value}
    for spec_name in list_specs():
        content = get_spec(spec_name)
        if not content:
            continue
        try:
            spec = load_spec_from_str(content)
        except Exception:
            continue
        for symbol, info in ticker_info.items():
            try:
                spec_result = evaluate_spec(info, spec)
            except Exception:
                continue
            for r in spec_result.get("results", []):
                if r.get("type") == "threshold":
                    spec_score_vars.setdefault(symbol, {})[r["id"]] = r["numeric_score"]

    # prev_raw[score_name][symbol] = raw value before normalization
    prev_raw: dict[str, dict[str, float | None]] = {}

    for score in analysis.scores:
        # Collect raw results for all tickers that have info
        raw_results: dict[str, float | None] = {}
        raw_details: dict[str, ScoreDetail] = {}
        for symbol, info in ticker_info.items():
            ticker_score_vars: dict[str, float | None] = {}
            ticker_score_vars.update(spec_score_vars.get(symbol, {}))
            ticker_score_vars.update(
                {name: prev_raw[name].get(symbol) for name in prev_raw}
            )
            raw_val, detail = compute_score(score, info, ticker_score_vars or None)
            raw_results[symbol] = raw_val
            raw_details[symbol] = detail

        prev_raw[score.name] = dict(raw_results)

        if score.normalize and raw_results:
            terms = _split_additive_terms(score.expression)

            # Evaluate and normalize each additive term independently
            term_norm_cols: list[list[float | None]] = []
            for term_expr in terms:
                weight, base_expr = _extract_weight_and_base(term_expr)
                term_ids = _extract_identifiers(base_expr)
                term_vals: list[float | None] = []
                for sym in tickers:
                    if sym in raw_details:
                        term_vars = {k: raw_details[sym].variables.get(k) for k in term_ids}
                        val = evaluate_expression(base_expr, term_vars)
                    else:
                        val = None
                    term_vals.append(val)
                normalized = _normalize_values(term_vals)
                term_norm_cols.append(
                    [None if v is None else weight * v for v in normalized]
                )

            for i, symbol in enumerate(tickers):
                if symbol in raw_details:
                    parts = [col[i] for col in term_norm_cols]
                    norm_result = None if any(p is None for p in parts) else sum(parts)  # type: ignore[arg-type]
                    detail = raw_details[symbol]
                    raw_details[symbol] = ScoreDetail(
                        expression=detail.expression,
                        normalize=detail.normalize,
                        variables=detail.variables,
                        raw_result=detail.raw_result,
                        result=norm_result,
                    )
                    raw_results[symbol] = norm_result

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


# ---------------------------------------------------------------------------
# CRUD — Specs
# ---------------------------------------------------------------------------


def list_specs() -> list[str]:
    """Return all stored spec names."""
    return [s.name for s in SpecDB.select()]


def get_spec(name: str) -> str | None:
    """Return raw YAML content for a named spec, or None if not found."""
    try:
        return str(SpecDB.get_by_id(name).content)
    except SpecDB.DoesNotExist:
        return None


def upsert_spec(name: str, content: str) -> None:
    """Store or replace a named spec."""
    SpecDB.insert(name=name, content=content).on_conflict_replace().execute()


def delete_spec(name: str) -> bool:
    count = SpecDB.delete().where(SpecDB.name == name).execute()
    return count > 0


# ---------------------------------------------------------------------------
# CRUD — Score Library
# ---------------------------------------------------------------------------


def list_library_scores() -> list[LibraryScore]:
    return [LibraryScore.from_db(s) for s in ScoreLibraryDB.select()]


def get_library_score(name: str) -> LibraryScore | None:
    try:
        return LibraryScore.from_db(ScoreLibraryDB.get_by_id(name))
    except ScoreLibraryDB.DoesNotExist:
        return None


def upsert_library_score(score: LibraryScore) -> LibraryScore:
    ScoreLibraryDB.insert(
        name=score.name,
        score_type=score.score_type,
        definition_json=json.dumps(score.definition),
        description=score.description,
    ).on_conflict_replace().execute()
    return get_library_score(score.name)  # type: ignore[return-value]


def delete_library_score(name: str) -> bool:
    count = ScoreLibraryDB.delete().where(ScoreLibraryDB.name == name).execute()
    return count > 0


def run_score_test(name: str, ticker: str) -> dict[str, Any]:
    """Fetch ticker info and evaluate a library score against it."""
    score = get_library_score(name)
    if score is None:
        raise ValueError(f"Library score '{name}' not found")

    info = fetch_info(ticker)

    if score.score_type == "expression":
        defn = score.definition
        expr = defn.get("expression", "")
        normalize = defn.get("normalize", False)

        # Pre-load spec threshold vars so expressions can reference them
        spec_vars: dict[str, float | None] = {}
        for spec_name in list_specs():
            content = get_spec(spec_name)
            if not content:
                continue
            try:
                spec = load_spec_from_str(content)
            except Exception:
                continue
            try:
                spec_result = evaluate_spec(info, spec)
            except Exception:
                continue
            for r in spec_result.get("results", []):
                if r.get("type") == "threshold":
                    spec_vars[r["id"]] = r["numeric_score"]

        s_obj = Score(name=name, expression=expr, normalize=normalize)
        raw_val, detail = compute_score(s_obj, info, spec_vars or None)
        return {
            "type": "expression",
            "score": raw_val,
            "variables": detail.variables,
            "error": None,
        }

    else:  # threshold
        defn = score.definition
        score_def = {
            "id": name,
            "metrics": defn.get("metrics", []),
            "aggregate": defn.get("aggregate", "mean"),
        }
        if "condition" in defn:
            score_def["condition"] = defn["condition"]
        metrics_list = defn.get("metrics", [])
        metric_scores = []
        for m in metrics_list:
            key = m.get("key", "")
            value = _to_numeric(info.get(key))
            rule_score = score_metric(info.get(key), m.get("rules", []))
            metric_scores.append({"key": key, "value": value, "rule_score": rule_score})

        result = evaluate_threshold_score(info, score_def, {})
        aggregate = result["numeric_score"] if result else None
        return {
            "type": "threshold",
            "score": aggregate,
            "metric_scores": metric_scores,
            "error": None,
        }


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def seed_library_from_spec(spec_name: str) -> int:
    """Import threshold scores from a named spec into the score library.

    Only creates scores that do not already exist (non-destructive).
    Returns the number of scores created.
    """
    content = get_spec(spec_name)
    if content is None:
        return 0
    spec = load_spec_from_str(content)
    created = 0
    for score_def in spec.get("scores", []):
        if score_def.get("type") != "threshold":
            continue
        score_id = score_def.get("id")
        if not score_id:
            continue
        if get_library_score(score_id) is not None:
            continue
        definition: dict[str, Any] = {
            "metrics": score_def.get("metrics", []),
            "aggregate": score_def.get("aggregate", "mean"),
        }
        if "condition" in score_def:
            definition["condition"] = score_def["condition"]
        score = LibraryScore(
            name=score_id,
            score_type="threshold",
            definition=definition,
            description=score_def.get("label", ""),
        )
        upsert_library_score(score)
        created += 1
    return created
