# Project Description

api-explorer is a web server that serves WEB UI to explore the methods
of yfinance api (https://ranaroussi.github.io/yfinance/index.html).

# Stack

- python3.12
- tox
    - ruff
    - pyright
    - pytest
- Uvicorn
- fastapi
- yfinance
- peewee
- pydantic-settings
- jinja2
- pandas

# Structure

- src/
    - api_explorer/
        - core/
            - model.py      ← DB models (peewee) + Pydantic request/response types
            - config.py     ← Settings via pydantic-settings (.env)
            - api.py        ← METHOD_REGISTRY, fetch_raw_data, render_html, get_data, lookup
            - utils.py      ← (stub, empty)
        - cli/
            - utils.py      ← (stub, empty)
        - server/
            - app.py        ← FastAPI app, route handlers
            - templates/
                - index.html ← Single-page UI (CSS + HTML + JS inline)
- test/
    - conftest.py           ← sets DB_PATH=:memory:
    - test_api.py           ← tests for core/api.py
- pyproject.toml
- tox.ini
- .env.example

## Database / Cache

- SQLite database, path configured via `DB_PATH` env var (default `cache.db`).
- ORM: `peewee` with two models defined in `core/model.py`:
  - `CacheEntry(ticker, method, period, data_json, cached_at)` — stores raw API responses.
  - `LookupCache(query PK, results_json, cached_at)` — stores ticker symbol search results.
- `init_db()` initialises tables and handles schema migrations (e.g. adding the `period` column).
- Tests use `DB_PATH=:memory:` (set in `test/conftest.py`).

## API Endpoints

All endpoints are defined in `server/app.py`.

| Method | Path            | Description                                      |
|--------|-----------------|--------------------------------------------------|
| GET    | /               | Renders index.html with category/method data     |
| POST   | /api/data       | Returns HTML-rendered table for a ticker+method  |
| POST   | /api/data/json  | Returns raw JSON payload for a ticker+method     |
| POST   | /api/lookup     | Searches ticker symbols (autocomplete)           |

## Method Registry

`core/api.py` exposes `METHOD_REGISTRY`: 34 yfinance methods in 3 categories:
- **Financials** — income_stmt, balance_sheet, cashflow, earnings, earnings_dates, …
- **Analysis & Holdings** — recommendations, analyst_price_targets, insider_purchases, …
- **Stock** — history, dividends, splits, actions, info, news, options, …

## Guidelines

- Configuration variables are specified on the .env file.
- Settings are loaded via a `Settings` class using `pydantic-settings` in `core/config.py`.
- Modules in core are not allowed to import other project modules that are not in the core package.
- Modules in cli package are allowed to import from core package only.
- `core/utils.py` and `cli/utils.py` are intentionally empty stubs reserved for future helpers.
- The `visualization/` package and `cli_N.py` entry points are **not yet implemented**.
- To run the server: `python -m api_explorer.server.app` (uses `settings.host` / `settings.port`).

# API Method Discovery

All api methods are listed in this webpage https://ranaroussi.github.io/yfinance/reference/index.html.
