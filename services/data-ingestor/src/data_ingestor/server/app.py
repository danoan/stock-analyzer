import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from data_ingestor.core import api_client, db, jobs
from data_ingestor.core.config import settings
from data_ingestor.core.model import METHODS, JobConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    jobs.ensure_jobs_table(settings.db_dsn)
    jobs.ensure_collections_table(settings.db_dsn)
    yield


app = FastAPI(title="Data Ingestor", lifespan=lifespan)

_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "api_url": settings.api_explorer_url,
            "methods": METHODS,
        },
    )


@app.post("/preview", response_class=HTMLResponse)
async def preview(
    request: Request,
    api_url: Annotated[str, Form()],
    ticker: Annotated[str, Form()],
    method: Annotated[str, Form()],
    force_refresh: Annotated[str | None, Form()] = None,
    melt: Annotated[str | None, Form()] = None,
    payload_json: Annotated[str | None, Form()] = None,
    period: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    refresh = force_refresh is not None
    melt_flag = melt is not None
    error: str | None = None
    columns: list[str] = []
    preview_rows: list[list] = []
    col_types: list[str] = []
    payload: dict = {}

    try:
        if payload_json:
            payload = json.loads(payload_json)
        else:
            payload = api_client.fetch_data(api_url, ticker, method, refresh, period=period)
        columns, all_rows = db.extract_rows(payload, ticker, method, melt=melt_flag)
        preview_rows = all_rows[:10]
        col_types: list[str] = db.infer_col_types(columns, all_rows) if columns else []
    except Exception as exc:
        error = str(exc)

    table_name = method.lower()
    payload_json_out = json.dumps(payload)

    ptype = payload.get("type", "")
    if melt_flag and ptype == "dataframe":
        default_conflict_cols = {"ticker", "item", "period"}
    elif ptype in ("dataframe", "series"):
        default_conflict_cols = {"ticker", "index"}
    elif ptype == "dict":
        default_conflict_cols = {"ticker", "key"}
    else:
        default_conflict_cols = set()

    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "api_url": api_url,
            "ticker": ticker,
            "method": method,
            "period": period,
            "force_refresh": refresh,
            "melt": melt_flag,
            "error": error,
            "columns": columns,
            "preview_rows": preview_rows,
            "table_name": table_name,
            "payload_json": payload_json_out,
            "col_types": col_types,
            "meta_cols": {"ticker", "method", "ingested_at"},
            "default_conflict_cols": default_conflict_cols,
        },
    )


@app.post("/ingest", response_class=HTMLResponse)
async def ingest(
    request: Request,
    api_url: Annotated[str, Form()],
    ticker: Annotated[str, Form()],
    method: Annotated[str, Form()],
    payload_json: Annotated[str, Form()],
    table_name: Annotated[str, Form()],
    truncate: Annotated[str | None, Form()] = None,
    melt: Annotated[str | None, Form()] = None,
    period: Annotated[str | None, Form()] = None,
    col_source: Annotated[list[str] | None, Form()] = None,
    col_include: Annotated[list[str] | None, Form()] = None,
    col_target: Annotated[list[str] | None, Form()] = None,
    col_type: Annotated[list[str] | None, Form()] = None,
    conflict_col: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    error: str | None = None
    row_count = 0

    truncate_flag = truncate is not None
    melt_flag = melt is not None

    try:
        payload = json.loads(payload_json)
        sources = col_source or []
        targets = col_target or []
        included_indices = set(col_include or [])

        col_map: dict[str, str] = {
            sources[i]: targets[i]
            for i in range(len(sources))
            if str(i) in included_indices
        }

        types = col_type or []
        type_map: dict[str, str] = {
            sources[i]: types[i]
            for i in range(min(len(sources), len(types)))
        }

        row_count = db.ingest(
            payload=payload,
            ticker=ticker,
            method=method,
            table_name=table_name,
            col_map=col_map,
            dsn=settings.db_dsn,
            truncate=truncate_flag,
            melt=melt_flag,
            col_types=type_map,
            conflict_cols=conflict_col or None,
        )
    except Exception as exc:
        error = str(exc)
        col_map = {}
        type_map = {}

    config_json = json.dumps({
        "method": method,
        "period": period or None,
        "table_name": table_name,
        "api_url": api_url,
        "melt": melt_flag,
        "truncate": truncate_flag,
        "col_map": col_map,
        "col_types": type_map,
        "conflict_cols": conflict_col or [],
    })

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "error": error,
            "row_count": row_count,
            "table_name": table_name,
            "ticker": ticker,
            "method": method,
            "config_json": config_json,
        },
    )


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def _load_collections() -> tuple[list[dict], dict[str, list[str]]]:
    all_collections = jobs.list_collections(settings.db_dsn)
    by_name: dict[str, list[str]] = {c["name"]: c["tickers"] for c in all_collections}
    return all_collections, by_name


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_list(request: Request) -> HTMLResponse:
    all_jobs = jobs.list_jobs(settings.db_dsn)
    all_collections, collections_by_name = _load_collections()
    for job in all_jobs:
        job["effective_tickers"] = jobs.resolve_job_tickers(job["config"], collections_by_name)
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": all_jobs,
            "collections": all_collections,
            "collections_by_name": collections_by_name,
        },
    )


@app.post("/jobs", response_class=RedirectResponse)
async def jobs_create(
    job_name: Annotated[str, Form()],
    tickers: Annotated[str, Form()],
    config_json: Annotated[str, Form()],
) -> RedirectResponse:
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    base_config = json.loads(config_json)
    cfg = JobConfig(tickers=ticker_list, **base_config)
    jobs.save_job(job_name, cfg.model_dump(), settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/tickers", response_class=RedirectResponse)
async def jobs_add_tickers(
    job_id: int,
    tickers: Annotated[str, Form()],
) -> RedirectResponse:
    new_tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    jobs.add_tickers(job_id, new_tickers, settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/tickers/remove", response_class=RedirectResponse)
async def jobs_remove_ticker(
    job_id: int,
    ticker: Annotated[str, Form()],
) -> RedirectResponse:
    jobs.remove_ticker(job_id, ticker, settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/collections", response_class=RedirectResponse)
async def jobs_assign_collection(
    job_id: int,
    collection_name: Annotated[str, Form()],
) -> RedirectResponse:
    jobs.assign_collection_to_job(job_id, collection_name, settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/collections/remove", response_class=RedirectResponse)
async def jobs_remove_collection(
    job_id: int,
    collection_name: Annotated[str, Form()],
) -> RedirectResponse:
    jobs.remove_collection_from_job(job_id, collection_name, settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/run", response_class=HTMLResponse)
async def jobs_run(
    request: Request,
    job_id: int,
    selected_tickers: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    job = jobs.get_job(job_id, settings.db_dsn)
    cfg = JobConfig(**job["config"])
    _, collections_by_name = _load_collections()
    effective_tickers = jobs.resolve_job_tickers(job["config"], collections_by_name)
    run_tickers = selected_tickers if selected_tickers else effective_tickers

    results: list[dict] = []
    for ticker in run_tickers:
        try:
            payload_dict = api_client.fetch_data(cfg.api_url, ticker, cfg.method, force_refresh=True, period=cfg.period)
            rows = db.ingest(
                payload=payload_dict,
                ticker=ticker,
                method=cfg.method,
                table_name=cfg.table_name,
                col_map=cfg.col_map,
                dsn=settings.db_dsn,
                truncate=cfg.truncate,
                melt=cfg.melt,
                col_types=cfg.col_types or None,
                conflict_cols=cfg.conflict_cols or None,
            )
            results.append({"ticker": ticker, "rows": rows, "error": None})
        except Exception as exc:
            results.append({"ticker": ticker, "rows": 0, "error": str(exc)})

    errors = [r for r in results if r["error"] is not None]
    if len(errors) == len(results):
        status = "error"
    elif errors:
        status = "partial"
    else:
        status = "ok"

    total_rows = sum(r["rows"] for r in results)
    jobs.update_job_run(job_id, status, total_rows, settings.db_dsn)

    return templates.TemplateResponse(
        "job_run_result.html",
        {
            "request": request,
            "job": job,
            "results": results,
            "status": status,
            "total_rows": total_rows,
        },
    )


@app.post("/jobs/{job_id}/rename", response_class=RedirectResponse)
async def jobs_rename(
    job_id: int,
    name: Annotated[str, Form()],
) -> RedirectResponse:
    jobs.rename_job(job_id, name.strip(), settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


@app.post("/jobs/{job_id}/delete", response_class=RedirectResponse)
async def jobs_delete(job_id: int) -> RedirectResponse:
    jobs.delete_job(job_id, settings.db_dsn)
    return RedirectResponse(url="/jobs", status_code=303)


# ---------------------------------------------------------------------------
# Ticker Collections
# ---------------------------------------------------------------------------

@app.get("/collections", response_class=HTMLResponse)
async def collections_list(request: Request) -> HTMLResponse:
    all_collections = jobs.list_collections(settings.db_dsn)
    return templates.TemplateResponse(
        "collections.html",
        {"request": request, "collections": all_collections},
    )


@app.post("/collections", response_class=RedirectResponse)
async def collections_create(
    name: Annotated[str, Form()],
    tickers: Annotated[str, Form()],
) -> RedirectResponse:
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    jobs.save_collection(name.strip(), ticker_list, settings.db_dsn)
    return RedirectResponse(url="/collections", status_code=303)


@app.post("/collections/{collection_id}/tickers", response_class=RedirectResponse)
async def collections_add_tickers(
    collection_id: int,
    tickers: Annotated[str, Form()],
) -> RedirectResponse:
    new_tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    jobs.add_tickers_to_collection(collection_id, new_tickers, settings.db_dsn)
    return RedirectResponse(url="/collections", status_code=303)


@app.post("/collections/{collection_id}/delete", response_class=RedirectResponse)
async def collections_delete(collection_id: int) -> RedirectResponse:
    jobs.delete_collection(collection_id, settings.db_dsn)
    return RedirectResponse(url="/collections", status_code=303)


def main() -> None:
    uvicorn.run("data_ingestor.server.app:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    main()
