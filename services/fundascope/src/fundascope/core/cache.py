from datetime import datetime, timezone
from pathlib import Path

from peewee import (
    CompositeKey,
    DateTimeField,
    Model,
    SqliteDatabase,
    TextField,
)

DB_PATH = Path(__file__).parent.parent.parent.parent / "cache.db"
db = SqliteDatabase(str(DB_PATH))


class CacheEntry(Model):
    ticker = TextField()
    data_type = TextField()
    data = TextField()
    cached_at = DateTimeField()

    class Meta:
        database = db
        primary_key = CompositeKey("ticker", "data_type")


db.connect()
db.create_tables([CacheEntry])


def get_cached(ticker: str, data_type: str) -> CacheEntry | None:
    try:
        return CacheEntry.get(
            (CacheEntry.ticker == ticker) & (CacheEntry.data_type == data_type)
        )
    except CacheEntry.DoesNotExist:
        return None


def set_cached(ticker: str, data_type: str, data: str) -> CacheEntry:
    now = datetime.now(timezone.utc)
    entry, created = CacheEntry.get_or_create(
        ticker=ticker,
        data_type=data_type,
        defaults={"data": data, "cached_at": now},
    )
    if not created:
        entry.data = data
        entry.cached_at = now
        entry.save()
    return entry
