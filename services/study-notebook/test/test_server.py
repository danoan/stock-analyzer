"""Server-layer tests using httpx.AsyncClient + ASGITransport.

Using async tests (anyio) so the ASGI app runs in the same thread as the
Peewee thread-local :memory: connection set up by the fixture.
"""
from __future__ import annotations

# Must be set before importing project modules so Settings picks them up.
import os

os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("API_EXPLORER_URL", "http://test-api-explorer")

from unittest.mock import patch

import httpx
import pytest

from study_notebook.core.model import (
    AnalysisDB,
    CollectionDB,
    RealizationDB,
    TickerCollectionDB,
    TickerDB,
    db,
)
from study_notebook.server.app import app

_ALL_TABLES = [TickerDB, CollectionDB, TickerCollectionDB, AnalysisDB, RealizationDB]

# Run all async tests with asyncio backend.
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def setup_db():
    """Fresh tables for every test (mirrors conftest.py)."""
    db.connect(reuse_if_open=True)
    db.drop_tables(_ALL_TABLES, safe=True)
    db.create_tables(_ALL_TABLES, safe=True)
    yield


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MATH_SCORE = {"type": "math", "name": "pe_score", "expression": "trailingPE"}
_ANALYSIS_PAYLOAD = {"name": "Test Analysis", "scores": [_MATH_SCORE]}


async def _create_analysis(client: httpx.AsyncClient, name: str = "Test Analysis") -> dict:
    payload = {"name": name, "scores": [_MATH_SCORE]}
    r = await client.post("/analyses", json=payload)
    assert r.status_code == 201
    return r.json()


async def _create_collection(client: httpx.AsyncClient, name: str = "tech") -> dict:
    r = await client.post("/collections", json={"name": name})
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health(client: httpx.AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------


async def test_analysis_create_and_list(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    assert a["id"] is not None
    assert a["name"] == "Test Analysis"

    r = await client.get("/analyses")
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert a["id"] in ids


async def test_analysis_get(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    r = await client.get(f"/analyses/{a['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Analysis"


async def test_analysis_get_not_found(client: httpx.AsyncClient):
    r = await client.get("/analyses/9999")
    assert r.status_code == 404


async def test_analysis_update(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    updated_payload = {**_ANALYSIS_PAYLOAD, "name": "Updated"}
    r = await client.put(f"/analyses/{a['id']}", json=updated_payload)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"


async def test_analysis_update_not_found(client: httpx.AsyncClient):
    r = await client.put("/analyses/9999", json=_ANALYSIS_PAYLOAD)
    assert r.status_code == 404


async def test_analysis_delete(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    r = await client.delete(f"/analyses/{a['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/analyses/{a['id']}")
    assert r2.status_code == 404


async def test_analysis_delete_not_found(client: httpx.AsyncClient):
    r = await client.delete("/analyses/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Realize
# ---------------------------------------------------------------------------


async def test_realize_with_tickers(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    fake_results = [{"ticker_symbol": "AAPL", "scores": {"pe_score": 1.5}, "error": None}]
    with patch("study_notebook.server.app.realize_analysis", return_value=fake_results) as mock:
        r = await client.post(
            f"/analyses/{a['id']}/realize",
            json={"tickers": ["aapl"], "collections": [], "force_refresh": False},
        )
    assert r.status_code == 200
    mock.assert_called_once()
    # verify the symbol was uppercased
    assert "AAPL" in mock.call_args.args[1]


async def test_realize_with_collections(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    await _create_collection(client, "myportfolio")
    # add a ticker to the collection directly via DB
    ticker, _ = TickerDB.get_or_create(symbol="GOOG", defaults={"name": "Alphabet"})
    col_db = CollectionDB.get(CollectionDB.name == "myportfolio")
    TickerCollectionDB.create(ticker=ticker, collection=col_db)

    fake_results = [{"ticker_symbol": "GOOG", "scores": {}, "error": None}]
    with patch("study_notebook.server.app.realize_analysis", return_value=fake_results) as mock:
        r = await client.post(
            f"/analyses/{a['id']}/realize",
            json={"tickers": [], "collections": ["myportfolio"], "force_refresh": False},
        )
    assert r.status_code == 200
    assert "GOOG" in mock.call_args.args[1]


async def test_realize_empty_input_422(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    r = await client.post(
        f"/analyses/{a['id']}/realize",
        json={"tickers": [], "collections": [], "force_refresh": False},
    )
    assert r.status_code == 422
    assert "ticker" in r.json()["detail"].lower()


async def test_realize_unknown_collection_404(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    r = await client.post(
        f"/analyses/{a['id']}/realize",
        json={"tickers": [], "collections": ["nonexistent"], "force_refresh": False},
    )
    assert r.status_code == 404


async def test_realize_analysis_not_found_404(client: httpx.AsyncClient):
    r = await client.post(
        "/analyses/9999/realize",
        json={"tickers": ["AAPL"], "collections": [], "force_refresh": False},
    )
    assert r.status_code == 404


async def test_realize_upstream_error_502(client: httpx.AsyncClient):
    a = await _create_analysis(client)
    with patch(
        "study_notebook.server.app.realize_analysis", side_effect=RuntimeError("upstream down")
    ):
        r = await client.post(
            f"/analyses/{a['id']}/realize",
            json={"tickers": ["AAPL"], "collections": [], "force_refresh": False},
        )
    assert r.status_code == 502
    assert "upstream" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


async def test_collection_list_empty(client: httpx.AsyncClient):
    r = await client.get("/collections")
    assert r.status_code == 200
    assert r.json() == []


async def test_collection_create(client: httpx.AsyncClient):
    col = await _create_collection(client, "growth")
    assert col["name"] == "growth"
    assert col["id"] is not None


async def test_collection_duplicate_409(client: httpx.AsyncClient):
    await _create_collection(client, "value")
    r = await client.post("/collections", json={"name": "value"})
    assert r.status_code == 409


async def test_collection_get(client: httpx.AsyncClient):
    await _create_collection(client, "dividend")
    r = await client.get("/collections/dividend")
    assert r.status_code == 200
    assert r.json()["name"] == "dividend"


async def test_collection_get_not_found(client: httpx.AsyncClient):
    r = await client.get("/collections/nonexistent")
    assert r.status_code == 404


async def test_collection_delete(client: httpx.AsyncClient):
    await _create_collection(client, "temp")
    r = await client.delete("/collections/temp")
    assert r.status_code == 204
    r2 = await client.get("/collections/temp")
    assert r2.status_code == 404


async def test_collection_delete_not_found(client: httpx.AsyncClient):
    r = await client.delete("/collections/nonexistent")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tickers in collections
# ---------------------------------------------------------------------------


async def test_add_ticker_to_collection(client: httpx.AsyncClient):
    await _create_collection(client, "tech")
    r = await client.post("/collections/tech/tickers", json={"symbol": "MSFT", "name": "Microsoft"})
    assert r.status_code == 200
    body = r.json()
    symbols = [t["symbol"] for t in body["tickers"]]
    assert "MSFT" in symbols


async def test_add_ticker_to_unknown_collection_404(client: httpx.AsyncClient):
    r = await client.post("/collections/unknown/tickers", json={"symbol": "MSFT", "name": ""})
    assert r.status_code == 404


async def test_remove_ticker_from_collection(client: httpx.AsyncClient):
    await _create_collection(client, "tech")
    await client.post("/collections/tech/tickers", json={"symbol": "AAPL", "name": "Apple"})
    r = await client.delete("/collections/tech/tickers/AAPL")
    assert r.status_code == 204
    col = (await client.get("/collections/tech")).json()
    symbols = [t["symbol"] for t in col["tickers"]]
    assert "AAPL" not in symbols


async def test_remove_ticker_not_in_collection_404(client: httpx.AsyncClient):
    await _create_collection(client, "tech")
    r = await client.delete("/collections/tech/tickers/NONEXISTENT")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tickers
# ---------------------------------------------------------------------------


async def test_list_tickers_empty(client: httpx.AsyncClient):
    r = await client.get("/tickers")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_tickers_after_add(client: httpx.AsyncClient):
    await _create_collection(client, "tech")
    await client.post("/collections/tech/tickers", json={"symbol": "NVDA", "name": "Nvidia"})
    r = await client.get("/tickers")
    assert r.status_code == 200
    symbols = [t["symbol"] for t in r.json()]
    assert "NVDA" in symbols


async def test_tickers_lookup_success(client: httpx.AsyncClient):
    fake = [
        {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "exchange": "NMS",
            "quoteType": "EQUITY",
        }
    ]
    with patch("study_notebook.server.app.lookup_tickers", return_value=fake) as mock:
        r = await client.get("/tickers/lookup", params={"q": "apple", "count": 1})
    assert r.status_code == 200
    mock.assert_called_once_with("apple", 1)
    assert r.json()[0]["symbol"] == "AAPL"


async def test_tickers_lookup_upstream_error_502(client: httpx.AsyncClient):
    with patch(
        "study_notebook.server.app.lookup_tickers", side_effect=RuntimeError("network error")
    ):
        r = await client.get("/tickers/lookup", params={"q": "apple"})
    assert r.status_code == 502


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


async def test_metrics_success(client: httpx.AsyncClient):
    fake_metrics = ["earningsGrowth", "trailingPE"]
    _target = "study_notebook.server.app.get_available_metrics"
    with patch(_target, return_value=fake_metrics) as mock:
        r = await client.get("/metrics", params={"ticker": "TSLA"})
    assert r.status_code == 200
    mock.assert_called_once_with("TSLA")
    assert r.json() == fake_metrics


async def test_metrics_default_ticker(client: httpx.AsyncClient):
    fake_metrics = ["trailingPE"]
    _target = "study_notebook.server.app.get_available_metrics"
    with patch(_target, return_value=fake_metrics) as mock:
        r = await client.get("/metrics")
    assert r.status_code == 200
    mock.assert_called_once_with("AAPL")


async def test_metrics_upstream_error_502(client: httpx.AsyncClient):
    with patch(
        "study_notebook.server.app.get_available_metrics",
        side_effect=RuntimeError("api down"),
    ):
        r = await client.get("/metrics")
    assert r.status_code == 502
