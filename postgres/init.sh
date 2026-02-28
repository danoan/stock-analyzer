#!/bin/bash
set -e

# Creates least-privilege roles and per-service login users.
# Runs automatically on first Postgres startup (empty data directory).
# Re-running against an existing cluster requires manual execution.
#
# Required env vars (passed via docker-compose):
#   INGESTOR_DB_USER, INGESTOR_DB_PASSWORD
#   METABASE_DB_USER,  METABASE_DB_PASSWORD

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Read-only role: for Metabase and any future analytics consumers
    CREATE ROLE reader NOLOGIN;
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO reader;
    GRANT USAGE ON SCHEMA public TO reader;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reader;

    -- Write role: for data-ingestor — can create tables and insert rows,
    -- but cannot DROP tables or TRUNCATE tables it does not own.
    CREATE ROLE ingestor NOLOGIN;
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO ingestor;
    GRANT USAGE, CREATE ON SCHEMA public TO ingestor;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT INSERT, SELECT ON TABLES TO ingestor;

    -- Per-service login users
    CREATE USER "$INGESTOR_DB_USER" WITH PASSWORD '$INGESTOR_DB_PASSWORD' IN ROLE ingestor;
    CREATE USER "$METABASE_DB_USER"  WITH PASSWORD '$METABASE_DB_PASSWORD'  IN ROLE reader;
EOSQL
