import os

# Must be set before importing project modules so Settings picks them up.
os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("API_EXPLORER_URL", "http://test-api-explorer")

import pytest  # noqa: E402

from stock_ranker.core.model import (  # noqa: E402
    AnalysisDB,
    CollectionDB,
    RealizationDB,
    TickerCollectionDB,
    TickerDB,
    db,
)

_ALL_TABLES = [TickerDB, CollectionDB, TickerCollectionDB, AnalysisDB, RealizationDB]


@pytest.fixture(autouse=True)
def setup_db():
    """Fresh tables for every test."""
    db.connect(reuse_if_open=True)
    db.drop_tables(_ALL_TABLES, safe=True)
    db.create_tables(_ALL_TABLES, safe=True)
    yield
