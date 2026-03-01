import json
from typing import Any

import psycopg2
import psycopg2.extras

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS _da_jobs (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    config          JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_run_at     TIMESTAMPTZ,
    last_run_status TEXT,
    last_run_rows   INTEGER
)"""

_SELECT_COLS = "id, name, config, created_at, last_run_at, last_run_status, last_run_rows"


def ensure_jobs_table(dsn: str) -> None:
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_TABLE)
        conn.commit()


def save_job(name: str, config_dict: dict, dsn: str) -> int:
    sql = "INSERT INTO _da_jobs (name, config) VALUES (%s, %s) RETURNING id"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name, json.dumps(config_dict)))
            row = cur.fetchone()
        conn.commit()
    assert row is not None
    return int(row[0])


def list_jobs(dsn: str) -> list[dict]:
    sql = f"SELECT {_SELECT_COLS} FROM _da_jobs ORDER BY name"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_job(job_id: int, dsn: str) -> dict:
    sql = f"SELECT {_SELECT_COLS} FROM _da_jobs WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (job_id,))
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"Job {job_id} not found")
    return dict(row)


def rename_job(job_id: int, new_name: str, dsn: str) -> None:
    sql = "UPDATE _da_jobs SET name = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (new_name, job_id))
        conn.commit()


def delete_job(job_id: int, dsn: str) -> None:
    sql = "DELETE FROM _da_jobs WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (job_id,))
        conn.commit()


def add_tickers(job_id: int, new_tickers: list[str], dsn: str) -> None:
    job = get_job(job_id, dsn)
    config = job["config"]
    existing: list[str] = config.get("tickers", [])
    existing_set = set(existing)
    config["tickers"] = existing + [t for t in new_tickers if t not in existing_set]
    sql = "UPDATE _da_jobs SET config = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(config), job_id))
        conn.commit()


def update_job_run(job_id: int, status: str, rows: int, dsn: str) -> None:
    sql = """
        UPDATE _da_jobs
        SET last_run_at = NOW(), last_run_status = %s, last_run_rows = %s
        WHERE id = %s
    """
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (status, rows, job_id))
        conn.commit()


def remove_ticker(job_id: int, ticker: str, dsn: str) -> None:
    job = get_job(job_id, dsn)
    config = job["config"]
    config["tickers"] = [t for t in config.get("tickers", []) if t != ticker]
    sql = "UPDATE _da_jobs SET config = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(config), job_id))
        conn.commit()


def assign_collection_to_job(job_id: int, collection_name: str, dsn: str) -> None:
    job = get_job(job_id, dsn)
    config = job["config"]
    existing: list[str] = config.get("collections", [])
    if collection_name not in existing:
        config["collections"] = existing + [collection_name]
    sql = "UPDATE _da_jobs SET config = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(config), job_id))
        conn.commit()


def remove_collection_from_job(job_id: int, collection_name: str, dsn: str) -> None:
    job = get_job(job_id, dsn)
    config = job["config"]
    config["collections"] = [c for c in config.get("collections", []) if c != collection_name]
    sql = "UPDATE _da_jobs SET config = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(config), job_id))
        conn.commit()


# ---------------------------------------------------------------------------
# Ticker Collections
# ---------------------------------------------------------------------------

_CREATE_COLLECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS _da_ticker_collections (
    id         SERIAL PRIMARY KEY,
    name       TEXT UNIQUE NOT NULL,
    tickers    JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
)"""

_COLL_SELECT_COLS = "id, name, tickers, created_at"


def ensure_collections_table(dsn: str) -> None:
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_COLLECTIONS_TABLE)
        conn.commit()


def save_collection(name: str, tickers: list[str], dsn: str) -> int:
    sql = "INSERT INTO _da_ticker_collections (name, tickers) VALUES (%s, %s) RETURNING id"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name, json.dumps(tickers)))
            row = cur.fetchone()
        conn.commit()
    assert row is not None
    return int(row[0])


def list_collections(dsn: str) -> list[dict[str, Any]]:
    sql = f"SELECT {_COLL_SELECT_COLS} FROM _da_ticker_collections ORDER BY name"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_collection(collection_id: int, dsn: str) -> dict[str, Any]:
    sql = f"SELECT {_COLL_SELECT_COLS} FROM _da_ticker_collections WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (collection_id,))
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"Collection {collection_id} not found")
    return dict(row)


def delete_collection(collection_id: int, dsn: str) -> None:
    sql = "DELETE FROM _da_ticker_collections WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (collection_id,))
        conn.commit()


def update_collection_tickers(collection_id: int, tickers: list[str], dsn: str) -> None:
    sql = "UPDATE _da_ticker_collections SET tickers = %s WHERE id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(tickers), collection_id))
        conn.commit()


def add_tickers_to_collection(collection_id: int, new_tickers: list[str], dsn: str) -> None:
    coll = get_collection(collection_id, dsn)
    existing: list[str] = coll["tickers"]
    existing_set = set(existing)
    merged = existing + [t for t in new_tickers if t not in existing_set]
    update_collection_tickers(collection_id, merged, dsn)


def resolve_job_tickers(config: dict[str, Any], collections_by_name: dict[str, list[str]]) -> list[str]:
    """Return deduplicated union of job's individual tickers and all referenced collection tickers."""
    seen: set[str] = set()
    result: list[str] = []
    for t in config.get("tickers", []):
        if t not in seen:
            seen.add(t)
            result.append(t)
    for cname in config.get("collections", []):
        for t in collections_by_name.get(cname, []):
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result
