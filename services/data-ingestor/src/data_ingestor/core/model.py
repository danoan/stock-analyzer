from pydantic import BaseModel

METHODS: list[str] = [
    # Financials
    "income_stmt",
    "quarterly_income_stmt",
    "balance_sheet",
    "quarterly_balance_sheet",
    "cashflow",
    "quarterly_cashflow",
    "earnings",
    "earnings_dates",
    "calendar",
    "sec_filings",
    # Analysis & Holdings
    "recommendations",
    "recommendations_summary",
    "upgrades_downgrades",
    "sustainability",
    "analyst_price_targets",
    "earnings_estimate",
    "revenue_estimate",
    "earnings_history",
    "eps_trend",
    "eps_revisions",
    "growth_estimates",
    "insider_purchases",
    "insider_transactions",
    "insider_roster_holders",
    "major_holders",
    "institutional_holders",
    "mutualfund_holders",
    # Stock
    "history",
    "dividends",
    "splits",
    "actions",
    "capital_gains",
    "info",
    "fast_info",
    "isin",
    "news",
    "history_metadata",
]


class DataRequest(BaseModel):
    ticker: str
    method: str
    force_refresh: bool = False
    period: str | None = None


class ApiPayload(BaseModel):
    type: str
    data: list | dict | None = None
    columns: list[str] | None = None
    index: list[str] | None = None
    message: str | None = None


class JobConfig(BaseModel):
    tickers: list[str]
    collections: list[str] = []
    method: str
    period: str | None = None
    table_name: str
    api_url: str
    melt: bool = False
    truncate: bool = False
    col_map: dict[str, str] = {}
    col_types: dict[str, str] = {}
    conflict_cols: list[str] = []
