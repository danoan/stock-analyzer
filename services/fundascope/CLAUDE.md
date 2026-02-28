# fundascope

Tool for analysing and comparing financial fundamentals of stocks (income statement,
balance sheet, cash flow, stock info). Data is fetched via `../api-explorer` which
acts as a caching proxy for yfinance.

## Features

- **Stock lookup** — lazy search across major world markets via api-explorer
- **Statement analysis** — income statement, balance sheet, cash flow (annual & quarterly)
  with YoY growth indicators and key metric highlighting
- **Stock info analysis** — graded scorecard covering valuation, profitability,
  financial health, growth, and dividends
- **Health scorecard** — server-computed grades (A–F) for revenue growth, profit trend,
  margin health, earnings quality, and dividend safety
- **Glossary** — enriched definitions for every financial metric with tooltips
- **AI chat** — streaming financial education assistant powered by OpenAI

## Technical Description

FastAPI web server with vanilla HTML/JS/CSS frontend. No frontend build step.

## Stack

- python 3.12
- tox
    - ruff (lint)
    - pyright (type check)
    - pytest
- pydantic / pydantic-settings
- python-dotenv
- uvicorn
- fastapi
- peewee (SQLite cache)
- yfinance
- openai

## Structure

- src/
    - fundascope/
        - core/
            - model.py        ← metric definitions and KEY_METRICS lookup
            - api.py          ← statement fetching, formatting, scoring
            - info_api.py     ← stock info fetching, grading, formatting
            - cache.py        ← SQLite cache via Peewee
        - utils/
            - config.py       ← Pydantic Settings (reads .env)
            - glossary.py     ← enriched GLOSSARY dict
        - server/
            - app.py          ← FastAPI routes
            - templates/      ← index.html, glossary.html
- test/
- tox.ini
- pyproject.toml
- .env          ← local config (not committed)
- .env.example

## Guidelines

- Configuration variables go in `.env`; load them via the `Config` pydantic-settings class in `utils/config.py`.
- `core` modules must not import from `utils` or `server`. They are self-contained.
- `utils` modules may import from `core`.
- `server` modules may import from both `core` and `utils`.
- Always run the full tox suite (`tox`) before considering a change done.
