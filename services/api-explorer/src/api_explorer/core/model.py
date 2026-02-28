from peewee import (
    CompositeKey,
    DateTimeField,
    Model,
    SqliteDatabase,
    TextField,
)
from pydantic import BaseModel, Field

from api_explorer.core.config import settings

db = SqliteDatabase(str(settings.db_path))


class CacheEntry(Model):
    ticker = TextField()
    method = TextField()
    period = TextField(default="1mo")
    data_json = TextField()
    cached_at = DateTimeField()

    class Meta:
        database = db
        primary_key = CompositeKey("ticker", "method", "period")


class LookupCache(Model):
    query = TextField(primary_key=True)
    results_json = TextField()
    cached_at = DateTimeField()

    class Meta:
        database = db


class DataRequest(BaseModel):
    ticker: str
    method: str
    force_refresh: bool = False
    period: str = "1mo"


class LookupRequest(BaseModel):
    query: str
    count: int = Field(default=8, ge=1, le=25)
    cache_only: bool = False


class JsonDataResponse(BaseModel):
    data: dict
    from_cache: bool
    cached_at: str | None


def init_db() -> None:
    db.connect()
    # Drop CacheEntry if the schema is outdated (missing html→removed, or missing period).
    cursor = db.execute_sql("PRAGMA table_info(cacheentry)")
    columns = [row[1] for row in cursor.fetchall()]
    if "html" in columns or (columns and "period" not in columns):
        db.drop_tables([CacheEntry])
    db.create_tables([CacheEntry, LookupCache], safe=True)
