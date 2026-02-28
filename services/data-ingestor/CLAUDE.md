# Project Description

Data ingestor is a project that ingests data compliant
with the api-explorer json intermediate format into
Postgres tables.

# Stack

- python3.12
- tox
    - ruff
    - pyright
    - pytest
- uvicorn
- fastapi
- pydantic / pydantic-settings
- httpx
- psycopg2

# Structure

- src/
    - data_ingestor/
        - core/
            - api.py          # HTTP client → api-explorer service
            - config.py       # Pydantic-settings config (reads .env)
            - db.py           # Schema inference + Postgres ingestion
            - jobs.py         # Job & collection CRUD (Postgres-backed)
            - model.py        # Pydantic models + supported methods list
        - server/
            - app.py          # FastAPI app + all routes
            - static/         # CSS assets
            - templates/      # Jinja2 HTML templates
- test/
- utils/                      # Standalone helper scripts (not part of the package)
- pyproject.toml
- tox.ini
- .env.example

## Guidelines

- Configuration variables are specified in the `.env` file.
- Use the `Settings` class in `core/config.py` (pydantic-settings) to access config — never read env vars directly.
- Modules in `core` must not import from `server` or any other project module outside `core`.
- Modules in `server` may only import from `core`.
- Scripts in `utils/` are standalone — they must not import from the `data_ingestor` package.
