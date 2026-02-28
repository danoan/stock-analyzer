from datetime import datetime, timezone
from typing import Any

import psycopg2
import psycopg2.extras

_META_TYPES: dict[str, str] = {"ticker": "TEXT", "method": "TEXT", "ingested_at": "TIMESTAMP"}


def _infer_type(values: list[str]) -> str:
    non_empty = [v for v in values if v != ""]
    if not non_empty:
        return "TEXT"
    bool_vals = {"true", "false", "yes", "no", "t", "f", "1", "0"}
    if all(v.lower() in bool_vals for v in non_empty):
        return "BOOLEAN"
    try:
        [int(v) for v in non_empty]
        return "INTEGER"
    except ValueError:
        pass
    try:
        [float(v) for v in non_empty]
        return "NUMERIC"
    except ValueError:
        pass
    try:
        for v in non_empty:
            datetime.fromisoformat(v)
        if any(" " in v or "T" in v for v in non_empty):
            return "TIMESTAMP"
        return "DATE"
    except ValueError:
        pass
    return "TEXT"


def infer_col_types(
    cols: list[str], rows: list[list[str]], sample_size: int = 100
) -> list[str]:
    sample = rows[:sample_size]
    result = []
    for i, col in enumerate(cols):
        if col in _META_TYPES:
            result.append(_META_TYPES[col])
        else:
            values = [row[i] for row in sample if i < len(row)]
            result.append(_infer_type(values))
    return result


def _cast_value(v: str, pg_type: str) -> Any:
    if v == "":
        return None
    if pg_type == "INTEGER":
        return int(float(v))
    if pg_type == "NUMERIC":
        return float(v)
    if pg_type in ("TIMESTAMP", "DATE"):
        return datetime.fromisoformat(v)
    if pg_type == "BOOLEAN":
        return v.lower() in {"true", "yes", "t", "1"}
    return v


def extract_rows(
    payload: dict, ticker: str, method: str, melt: bool = False
) -> tuple[list[str], list[list]]:
    """Normalise any payload type into (column_names, rows).

    Meta columns ticker, method, ingested_at are always appended.
    All values are cast to str.
    When melt=True and type is 'dataframe', returns long format with columns
    (item, period, value) instead of wide format.
    """
    ptype = payload.get("type", "")
    meta = [ticker, method, datetime.now(timezone.utc).isoformat()]
    meta_cols = ["ticker", "method", "ingested_at"]

    if ptype == "dataframe":
        columns: list[str] = payload.get("columns", [])
        index: list[str] = payload.get("index", [])
        data: list = payload.get("data", [])
        if melt:
            cols = ["item", "period", "value"] + meta_cols
            rows = []
            for idx, row in zip(index, data):
                for col_name, cell in zip(columns, row):
                    rows.append([
                        str(idx),
                        str(col_name),
                        str(cell) if cell is not None else "",
                    ] + meta)
            return cols, rows
        cols = ["index"] + columns + meta_cols
        rows = [[str(idx)] + [str(v) if v is not None else "" for v in row] + meta for idx, row in zip(index, data)]
        return cols, rows

    if ptype == "series":
        index = payload.get("index", [])
        data = payload.get("data", [])
        cols = ["index", "value"] + meta_cols
        rows = [[str(idx), str(v) if v is not None else ""] + meta for idx, v in zip(index, data)]
        return cols, rows

    if ptype == "dict":
        data_dict: dict = payload.get("data", {})
        cols = ["key", "value"] + meta_cols
        rows = [[str(k), str(v) if v is not None else ""] + meta for k, v in data_dict.items()]
        return cols, rows

    if ptype == "list":
        items: list[dict] = payload.get("data", [])
        if not items:
            return meta_cols, [meta]
        all_keys: list[str] = list(dict.fromkeys(k for row in items for k in row))
        cols = all_keys + meta_cols
        rows = [[str(row.get(k, "")) if row.get(k) is not None else "" for k in all_keys] + meta for row in items]
        return cols, rows

    # fallback / error / empty — single row with message or data
    value = payload.get("message") or payload.get("data") or ""
    cols = ["value"] + meta_cols
    rows = [[str(value)] + meta]
    return cols, rows


def ingest(
    payload: dict,
    ticker: str,
    method: str,
    table_name: str,
    col_map: dict[str, str],
    dsn: str,
    truncate: bool = False,
    melt: bool = False,
    col_types: dict[str, str] | None = None,
    conflict_cols: list[str] | None = None,
) -> int:
    """Create table if needed, optionally truncate, then bulk-insert rows.

    col_map maps source column name -> target column name (only included cols).
    col_types maps source column name -> Postgres type (e.g. "NUMERIC").
    conflict_cols is a list of source column names that form the natural key;
    when provided a UNIQUE index is created and duplicate rows are silently skipped
    (INSERT … ON CONFLICT DO NOTHING).
    Returns number of rows inserted.
    """
    src_cols, all_rows = extract_rows(payload, ticker, method, melt=melt)

    # Filter to included columns only
    included_src = [c for c in src_cols if c in col_map]
    included_tgt = [col_map[c] for c in included_src]
    src_indices = [src_cols.index(c) for c in included_src]
    included_types = [col_types.get(c, "TEXT") if col_types else "TEXT" for c in included_src]

    rows_to_insert = [
        [_cast_value(row[i], included_types[j]) for j, i in enumerate(src_indices)]
        for row in all_rows
    ]

    # Sanitise table and column names (allow only alphanumeric + underscore)
    safe_table = _safe_ident(table_name)
    safe_cols = [_safe_ident(c) for c in included_tgt]

    col_defs = ", ".join(
        f"{safe_col} {pg_type}"
        for safe_col, pg_type in zip(safe_cols, included_types)
    )
    create_sql = f'CREATE TABLE IF NOT EXISTS {safe_table} ({col_defs})'
    truncate_sql = f'TRUNCATE TABLE {safe_table}'

    # Resolve conflict columns to target names and build ON CONFLICT clause
    uq_sql: str | None = None
    if conflict_cols:
        missing = [c for c in conflict_cols if c not in col_map]
        if missing:
            raise ValueError(f"conflict_cols not present in col_map: {missing}")
        safe_conflict = [_safe_ident(col_map[c]) for c in conflict_cols]
        conflict_list = ", ".join(safe_conflict)
        index_name = f'"uq_{_safe_ident(table_name)[1:-1]}"'
        uq_sql = f'CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {safe_table} ({conflict_list})'
        insert_sql = f'INSERT INTO {safe_table} ({", ".join(safe_cols)}) VALUES %s ON CONFLICT ({conflict_list}) DO NOTHING'
    else:
        insert_sql = f'INSERT INTO {safe_table} ({", ".join(safe_cols)}) VALUES %s'

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
            if truncate:
                cur.execute(truncate_sql)
            if uq_sql:
                cur.execute(uq_sql)
            psycopg2.extras.execute_values(cur, insert_sql, rows_to_insert)
            inserted = cur.rowcount
            conn.commit()

    return inserted


def _safe_ident(name: str) -> str:
    """Return a quoted identifier safe for use in SQL."""
    # Replace anything that isn't alphanumeric or underscore with underscore
    clean = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    if not clean or clean[0].isdigit():
        clean = f"col_{clean}"
    return f'"{clean}"'
