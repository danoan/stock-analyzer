from __future__ import annotations

import pathlib
from typing import Any

import peewee
import yaml
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from stock_ranker.core.api import (
    add_ticker_to_collection,
    create_analysis,
    create_collection,
    delete_analysis,
    delete_collection,
    delete_spec,
    get_analysis,
    get_available_metrics,
    get_collection_by_name,
    get_spec,
    list_all_tickers,
    list_analyses,
    list_collections,
    list_specs,
    lookup_tickers,
    realize_analysis,
    remove_ticker_from_collection,
    update_analysis,
    upsert_spec,
)
from stock_ranker.core.model import (
    Analysis,
    Collection,
    LookupResult,
    RealizationResult,
    Ticker,
    init_db,
)
from stock_ranker.core.score_engine import (
    evaluate_spec,
    load_spec_from_str,
    normalize_expression_results,
)

init_db()

_STATIC = pathlib.Path(__file__).parent / "static"
_SPECS_DIR = pathlib.Path(__file__).parent.parent / "core" / "specs"

app = FastAPI(title="stock-ranker")
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


def _seed_bundled_specs() -> None:
    """Seed YAML spec files bundled with the package into the DB at startup."""
    if not _SPECS_DIR.exists():
        return
    for yaml_file in _SPECS_DIR.glob("*.yaml"):
        name = yaml_file.stem
        content = yaml_file.read_text()
        upsert_spec(name, content)


_seed_bundled_specs()


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateCollectionRequest(BaseModel):
    name: str


class BulkAddTickersRequest(BaseModel):
    symbols: list[str]


class RealizeRequest(BaseModel):
    tickers: list[str] = []
    collections: list[str] = []
    force_refresh: bool = False


class SpecUpsertRequest(BaseModel):
    name: str
    content: str  # raw YAML text


class EvaluateRequest(BaseModel):
    spec_name: str | None = None
    spec: dict[str, Any] | None = None  # inline parsed spec
    info: dict[str, Any]


class EvaluateCollectionRequest(BaseModel):
    spec_name: str | None = None
    spec: dict[str, Any] | None = None
    tickers_info: dict[str, dict[str, Any]]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------


@app.get("/analyses", response_model=list[Analysis])
async def get_analyses() -> list[Analysis]:
    return list_analyses()


@app.post("/analyses", response_model=Analysis, status_code=201)
async def post_analysis(analysis: Analysis) -> Analysis:
    return create_analysis(analysis)


@app.get("/analyses/{analysis_id}", response_model=Analysis)
async def get_analysis_by_id(analysis_id: int) -> Analysis:
    a = get_analysis(analysis_id)
    if a is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    return a


@app.put("/analyses/{analysis_id}", response_model=Analysis)
async def put_analysis(analysis_id: int, analysis: Analysis) -> Analysis:
    existing = get_analysis(analysis_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    analysis.id = analysis_id
    return update_analysis(analysis)


@app.delete("/analyses/{analysis_id}", status_code=204)
async def delete_analysis_by_id(analysis_id: int) -> Response:
    if not delete_analysis(analysis_id):
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    return Response(status_code=204)


@app.post("/analyses/{analysis_id}/realize", response_model=list[RealizationResult])
async def post_realize(analysis_id: int, req: RealizeRequest) -> list[RealizationResult]:
    analysis = get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    symbols: list[str] = [t.upper() for t in req.tickers]
    for col_name in req.collections:
        col = get_collection_by_name(col_name)
        if col is None:
            raise HTTPException(status_code=404, detail=f"Collection '{col_name}' not found")
        symbols.extend(t.symbol for t in col.tickers)

    seen: set[str] = set()
    unique_symbols: list[str] = []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            unique_symbols.append(s)

    if not unique_symbols:
        raise HTTPException(
            status_code=422, detail="Specify at least one ticker or collection"
        )

    try:
        return realize_analysis(analysis, unique_symbols, req.force_refresh)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@app.get("/collections", response_model=list[Collection])
async def get_collections() -> list[Collection]:
    return list_collections()


@app.post("/collections", response_model=Collection, status_code=201)
async def post_collection(req: CreateCollectionRequest) -> Collection:
    try:
        return create_collection(req.name)
    except peewee.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Collection '{req.name}' already exists")


@app.get("/collections/{name}", response_model=Collection)
async def get_collection(name: str) -> Collection:
    col = get_collection_by_name(name)
    if col is None:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    return col


@app.delete("/collections/{name}", status_code=204)
async def delete_collection_by_name(name: str) -> Response:
    if not delete_collection(name):
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    return Response(status_code=204)


@app.post("/collections/{name}/tickers", response_model=Collection)
async def post_ticker_to_collection(name: str, ticker: Ticker) -> Collection:
    ok = add_ticker_to_collection(ticker.symbol, name, ticker.name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    return get_collection_by_name(name)  # type: ignore[return-value]


@app.post("/collections/{name}/tickers/bulk", response_model=Collection)
async def post_tickers_bulk_to_collection(name: str, req: BulkAddTickersRequest) -> Collection:
    if get_collection_by_name(name) is None:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    for symbol in req.symbols:
        add_ticker_to_collection(symbol.upper(), name)
    return get_collection_by_name(name)  # type: ignore[return-value]


@app.delete("/collections/{name}/tickers/{symbol}", status_code=204)
async def delete_ticker_from_collection(name: str, symbol: str) -> Response:
    if get_collection_by_name(name) is None:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    if not remove_ticker_from_collection(symbol, name):
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{symbol}' not found in collection '{name}'",
        )
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Tickers
# ---------------------------------------------------------------------------


@app.get("/tickers", response_model=list[Ticker])
async def get_tickers() -> list[Ticker]:
    return list_all_tickers()


@app.get("/tickers/lookup", response_model=list[LookupResult])
async def get_tickers_lookup(q: str, count: int = 8) -> list[LookupResult]:
    try:
        return lookup_tickers(q, count)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@app.get("/metrics", response_model=list[str])
async def get_metrics(ticker: str = "AAPL") -> list[str]:
    try:
        return get_available_metrics(ticker)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")


# ---------------------------------------------------------------------------
# Specs
# ---------------------------------------------------------------------------


@app.get("/specs", response_model=list[str])
async def get_specs() -> list[str]:
    return list_specs()


@app.get("/specs/{name}")
async def get_spec_by_name(name: str) -> Response:
    content = get_spec(name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")
    return Response(content=content, media_type="text/plain; charset=utf-8")


@app.post("/specs", status_code=201)
async def post_spec(req: SpecUpsertRequest) -> dict[str, str]:
    try:
        load_spec_from_str(req.content)  # validate before storing
    except (ValueError, yaml.YAMLError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid spec: {e}")
    upsert_spec(req.name, req.content)
    return {"name": req.name}


@app.put("/specs/{name}")
async def put_spec(name: str, req: SpecUpsertRequest) -> dict[str, str]:
    try:
        load_spec_from_str(req.content)
    except (ValueError, yaml.YAMLError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid spec: {e}")
    upsert_spec(name, req.content)
    return {"name": name}


@app.delete("/specs/{name}", status_code=204)
async def delete_spec_by_name(name: str) -> Response:
    if not delete_spec(name):
        raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Score evaluation
# ---------------------------------------------------------------------------


def _resolve_spec(
    spec_name: str | None, inline_spec: dict[str, Any] | None
) -> dict[str, Any]:
    """Resolve a spec from name or inline dict; raise HTTPException on failure."""
    if inline_spec is not None:
        return inline_spec
    if spec_name is not None:
        content = get_spec(spec_name)
        if content is None:
            raise HTTPException(status_code=404, detail=f"Spec '{spec_name}' not found")
        try:
            return load_spec_from_str(content)
        except (ValueError, yaml.YAMLError) as e:
            raise HTTPException(status_code=422, detail=f"Invalid spec: {e}")
    raise HTTPException(status_code=422, detail="Provide either 'spec_name' or 'spec'")


@app.post("/scores/evaluate")
async def post_evaluate(req: EvaluateRequest) -> dict[str, Any]:
    """Evaluate a scoring spec against a single ticker's info dict."""
    spec = _resolve_spec(req.spec_name, req.spec)
    return evaluate_spec(req.info, spec)


@app.post("/scores/evaluate-collection")
async def post_evaluate_collection(req: EvaluateCollectionRequest) -> dict[str, Any]:
    """Evaluate a scoring spec across a collection of tickers, with normalization."""
    spec = _resolve_spec(req.spec_name, req.spec)

    # Evaluate each ticker
    results_by_ticker: dict[str, Any] = {}
    for ticker, info in req.tickers_info.items():
        results_by_ticker[ticker] = evaluate_spec(info, spec)

    # Apply normalization for expression scores that have normalize=True
    for score_def in spec.get("scores", []):
        if score_def.get("type") == "expression" and score_def.get("normalize"):
            results_by_ticker = normalize_expression_results(
                results_by_ticker, score_def["id"], score_def["expression"]
            )

    return results_by_ticker


if __name__ == "__main__":
    import uvicorn

    from stock_ranker.utils.config import settings

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
