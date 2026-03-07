from __future__ import annotations

import json
from typing import Any

from peewee import (
    AutoField,
    CompositeKey,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)
from pydantic import BaseModel

from stock_ranker.utils.config import settings

db = SqliteDatabase(str(settings.db_path))


# ---------------------------------------------------------------------------
# Pydantic domain models
# ---------------------------------------------------------------------------


class Score(BaseModel):
    name: str
    expression: str
    normalize: bool = False


class Analysis(BaseModel):
    id: int | None = None
    name: str
    scores: list[Score]

    @classmethod
    def from_db(cls, record: AnalysisDB) -> Analysis:
        scores_raw: list[dict[str, Any]] = json.loads(record.scores_json)
        scores = [Score.model_validate(s) for s in scores_raw]
        return cls(id=record.id, name=record.name, scores=scores)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scores_json": json.dumps([s.model_dump() for s in self.scores]),
        }


class Ticker(BaseModel):
    symbol: str
    name: str = ""


class Collection(BaseModel):
    id: int | None = None
    name: str
    tickers: list[Ticker] = []


class LookupResult(BaseModel):
    symbol: str
    shortName: str
    exchange: str
    quoteType: str


class ScoreDetail(BaseModel):
    expression: str
    normalize: bool
    variables: dict[str, float | None]   # raw values of referenced vars
    raw_result: float | None              # expression result before normalization
    result: float | None                  # final result (normalized if normalize=True)


class RealizationResult(BaseModel):
    ticker_symbol: str
    name: str = ""
    sector: str = ""
    scores: dict[str, float | None] = {}
    score_details: dict[str, ScoreDetail] = {}
    error: str | None = None


# ---------------------------------------------------------------------------
# Peewee DB models
# ---------------------------------------------------------------------------


class TickerDB(Model):
    symbol = TextField(primary_key=True)
    name = TextField(default="")

    class Meta:
        database = db
        table_name = "ticker"


class CollectionDB(Model):
    id = AutoField()
    name = TextField(unique=True)

    class Meta:
        database = db
        table_name = "collection"


class TickerCollectionDB(Model):
    ticker = ForeignKeyField(TickerDB, backref="collections", column_name="ticker_symbol")
    collection = ForeignKeyField(CollectionDB, backref="tickers", column_name="collection_id")

    class Meta:
        database = db
        table_name = "ticker_collection"
        primary_key = CompositeKey("ticker", "collection")


class AnalysisDB(Model):
    id = AutoField()
    name = TextField(unique=True)
    scores_json = TextField()

    class Meta:
        database = db
        table_name = "analysis"


class RealizationDB(Model):
    id = AutoField()
    analysis = ForeignKeyField(AnalysisDB, backref="realizations", column_name="analysis_id")
    ticker_symbol = TextField()
    run_at = DateTimeField()
    results_json = TextField()
    error = TextField(null=True)

    class Meta:
        database = db
        table_name = "realization"


class SpecDB(Model):
    name = TextField(primary_key=True)
    content = TextField()  # raw YAML text

    class Meta:
        database = db
        table_name = "spec"


class ScoreLibraryDB(Model):
    name = TextField(primary_key=True)
    score_type = TextField()  # 'expression' | 'threshold'
    definition_json = TextField()
    description = TextField(default="")

    class Meta:
        database = db
        table_name = "score_library"


# For tests that need an integer PK placeholder
_REALIZATION_UNUSED_ID = IntegerField(null=True)


class LibraryScore(BaseModel):
    name: str
    score_type: str  # "expression" | "threshold"
    definition: dict[str, Any]
    description: str = ""

    @classmethod
    def from_db(cls, record: ScoreLibraryDB) -> LibraryScore:
        return cls(
            name=record.name,
            score_type=record.score_type,
            definition=json.loads(record.definition_json),
            description=record.description,
        )


def init_db() -> None:
    db.connect(reuse_if_open=True)
    db.create_tables(
        [TickerDB, CollectionDB, TickerCollectionDB, AnalysisDB, RealizationDB, SpecDB,
         ScoreLibraryDB],
        safe=True,
    )
