import traceback
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from fundascope.core.api import build_analysis
from fundascope.core.info_api import get_stock_info
from fundascope.utils.config import config
from fundascope.utils.glossary import GLOSSARY

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class AnalyzeRequest(BaseModel):
    ticker: str
    force_refresh: bool = False
    statement_type: str = "income_stmt"


class StockInfoRequest(BaseModel):
    ticker: str
    force_refresh: bool = False


class LookupRequest(BaseModel):
    query: str
    count: int = Field(default=8, ge=1, le=25)
    cache_only: bool = False


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    ticker: Optional[str] = None
    statement_type: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/glossary", response_class=HTMLResponse)
async def glossary_page(request: Request):
    return templates.TemplateResponse("glossary.html", {"request": request})


@app.get("/api/glossary")
async def api_glossary(term: str | None = None):
    if term:
        entry = GLOSSARY.get(term)
        if entry is None:
            return JSONResponse({"error": f"Term '{term}' not found"}, status_code=404)
        return JSONResponse({term: entry})
    return JSONResponse(GLOSSARY)


@app.post("/api/lookup")
async def api_lookup(req: LookupRequest):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{config.api_explorer_url}/api/lookup",
                json={"query": req.query, "count": req.count, "cache_only": req.cache_only},
            )
            return JSONResponse(resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse(
            {"results": [], "from_cache": False, "error": "api-explorer unavailable"},
            status_code=503,
        )
    except Exception:
        return JSONResponse({"results": [], "from_cache": False}, status_code=500)


@app.post("/api/stock-info")
async def api_stock_info(req: StockInfoRequest):
    ticker = req.ticker.strip().upper()
    if not ticker:
        return JSONResponse(
            {"error": "Please enter a ticker symbol"}, status_code=400
        )

    try:
        result = get_stock_info(
            ticker,
            force_refresh=req.force_refresh,
            api_explorer_url=config.api_explorer_url,
            stock_ranker_url=config.stock_ranker_url,
        )
        return JSONResponse(result)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception:
        return JSONResponse(
            {"error": f"Unexpected error:\n{traceback.format_exc()}"},
            status_code=500,
        )


@app.post("/api/analyze")
async def api_analyze(req: AnalyzeRequest):
    ticker = req.ticker.strip().upper()
    if not ticker:
        return JSONResponse(
            {"error": "Please enter a ticker symbol"}, status_code=400
        )

    try:
        result = build_analysis(ticker, force_refresh=req.force_refresh, statement_type=req.statement_type)
        return JSONResponse(result)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception:
        return JSONResponse(
            {"error": f"Unexpected error:\n{traceback.format_exc()}"},
            status_code=500,
        )


CHAT_SYSTEM_PROMPT = (
    "You are an experienced financial consultant and educator. "
    "Your role is to explain financial terms, metrics, ratios, and concepts "
    "in plain language that anyone can understand. "
    "Keep responses under 300 words. Use plain text only — no markdown, "
    "no bullet points with asterisks, no headers. "
    "Be concise and educational. "
    "Never give specific investment advice or recommend buying/selling. "
    "If the user is looking at a specific stock or statement, use that context "
    "to make your explanations more relevant."
)


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    if not config.openai_api_key:
        return JSONResponse(
            {"error": "Chat is unavailable — no OpenAI API key configured."},
            status_code=503,
        )

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=config.openai_api_key)

    system_content = CHAT_SYSTEM_PROMPT
    if req.ticker:
        system_content += f"\n\nThe user is currently analyzing the stock: {req.ticker}."
    if req.statement_type:
        system_content += f" They are viewing the: {req.statement_type.replace('_', ' ')}."

    messages = [{"role": "system", "content": system_content}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    async def generate():
        stream = await client.chat.completions.create(
            model=config.openai_model,
            messages=messages,
            max_tokens=config.openai_max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield f"data: {delta.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def main():
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
