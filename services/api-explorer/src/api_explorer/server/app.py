import traceback
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from api_explorer.core.api import CATEGORIES, get_data, lookup, render_html
from api_explorer.core.config import settings
from api_explorer.core.model import DataRequest, LookupRequest, init_db

init_db()

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": CATEGORIES,
        },
    )


def _format_cached_at(cached_at) -> str | None:
    if cached_at is None:
        return None
    if isinstance(cached_at, datetime):
        return cached_at.isoformat()
    return str(cached_at)  # Peewee may return the raw ISO string for tz-aware datetimes


@app.post("/api/data")
async def api_data(req: DataRequest):
    ticker = req.ticker.strip().upper()
    if not ticker:
        return JSONResponse({
            "html": "<p class='error'>Please enter a ticker symbol</p>",
            "from_cache": False,
            "cached_at": None,
        })

    try:
        payload, from_cache, cached_at = get_data(ticker, req.method, req.force_refresh, req.period)
    except Exception:
        payload = {
            "type": "error",
            "message": f"Unexpected error:\n<pre>{traceback.format_exc()}</pre>",
        }
        from_cache = False
        cached_at = None

    return JSONResponse({
        "html": render_html(payload),
        "from_cache": from_cache,
        "cached_at": _format_cached_at(cached_at),
    })


@app.post("/api/data/json")
async def api_data_json(req: DataRequest):
    ticker = req.ticker.strip().upper()
    if not ticker:
        return JSONResponse({
            "data": {"type": "error", "message": "Please enter a ticker symbol"},
            "from_cache": False,
            "cached_at": None,
        })

    try:
        payload, from_cache, cached_at = get_data(ticker, req.method, req.force_refresh, req.period)
    except Exception:
        payload = {
            "type": "error",
            "message": f"Unexpected error: {traceback.format_exc()}",
        }
        from_cache = False
        cached_at = None

    return JSONResponse({
        "data": payload,
        "from_cache": from_cache,
        "cached_at": _format_cached_at(cached_at),
    })


@app.post("/api/lookup")
async def api_lookup(req: LookupRequest):
    result = lookup(req.query, count=req.count, cache_only=req.cache_only)
    return JSONResponse(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
