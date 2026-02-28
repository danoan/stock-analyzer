from __future__ import annotations

import pathlib

import peewee
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
    get_analysis,
    get_available_metrics,
    get_collection_by_name,
    list_all_tickers,
    list_analyses,
    list_collections,
    lookup_tickers,
    realize_analysis,
    remove_ticker_from_collection,
    update_analysis,
)
from stock_ranker.core.model import (
    Analysis,
    Collection,
    LookupResult,
    RealizationResult,
    Ticker,
    init_db,
)

init_db()

_STATIC = pathlib.Path(__file__).parent / "static"

app = FastAPI(title="stock-ranker")
app.mount("/static", StaticFiles(directory=_STATIC), name="static")


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


if __name__ == "__main__":
    import uvicorn

    from stock_ranker.utils.config import settings

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
