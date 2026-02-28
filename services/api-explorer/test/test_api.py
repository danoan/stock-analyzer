from unittest.mock import MagicMock, patch

import pandas as pd

from api_explorer.core.api import (
    CATEGORIES,
    METHOD_REGISTRY,
    fetch_raw_data,
    render_html,
)


class TestMethodRegistry:
    def test_all_methods_have_categories(self):
        for method, category in METHOD_REGISTRY.items():
            assert isinstance(category, str)
            assert len(category) > 0

    def test_categories_built_from_registry(self):
        all_methods_in_categories = [m for methods in CATEGORIES.values() for m in methods]
        assert sorted(all_methods_in_categories) == sorted(METHOD_REGISTRY.keys())

    def test_expected_categories_exist(self):
        assert "Financials" in CATEGORIES
        assert "Analysis & Holdings" in CATEGORIES
        assert "Stock" in CATEGORIES


class TestFetchRawData:
    def test_unknown_method_returns_error_payload(self):
        payload = fetch_raw_data("AAPL", "nonexistent_method")
        assert payload["type"] == "error"
        assert "Unknown method" in payload["message"]

    @patch("api_explorer.core.api.get_ticker")
    def test_dataframe_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.balance_sheet = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "balance_sheet")
        assert payload["type"] == "dataframe"
        assert "columns" in payload
        assert "index" in payload
        assert "data" in payload

    @patch("api_explorer.core.api.get_ticker")
    def test_empty_dataframe_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.balance_sheet = pd.DataFrame()
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "balance_sheet")
        assert payload["type"] == "empty"
        assert "No data available" in payload["message"]

    @patch("api_explorer.core.api.get_ticker")
    def test_series_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.dividends = pd.Series([0.5, 0.6], index=["2024-01", "2024-02"])
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "dividends")
        assert payload["type"] == "series"
        assert "index" in payload
        assert "data" in payload

    @patch("api_explorer.core.api.get_ticker")
    def test_dict_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.fast_info = {"price": 150.0, "volume": 1000000}
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "fast_info")
        assert payload["type"] == "dict"
        assert "price" in payload["data"]

    @patch("api_explorer.core.api.get_ticker")
    def test_none_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.sustainability = None
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "sustainability")
        assert payload["type"] == "empty"
        assert "No data returned" in payload["message"]

    @patch("api_explorer.core.api.get_ticker")
    def test_list_of_dicts_result(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.sec_filings = [
            {"type": "10-K", "date": "2024-01-01"},
            {"type": "10-Q", "date": "2024-04-01"},
        ]
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "sec_filings")
        assert payload["type"] == "list"
        assert any(row.get("type") == "10-K" for row in payload["data"])

    @patch("api_explorer.core.api.get_ticker")
    def test_news_extracts_content_fields(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.news = [
            {"content": {"title": "Big news", "summary": "Summary", "pubDate": "2024-01-01", "contentType": "article"}},
        ]
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "news")
        assert payload["type"] == "list"
        assert payload["data"][0]["title"] == "Big news"
        assert "summary" in payload["data"][0]

    @patch("api_explorer.core.api.get_ticker")
    def test_exception_returns_error_payload(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        type(ticker).info = property(lambda self: (_ for _ in ()).throw(RuntimeError("API down")))
        mock_get_ticker.return_value = ticker

        payload = fetch_raw_data("AAPL", "info")
        assert payload["type"] == "error"
        assert "API down" in payload["message"]

    @patch("api_explorer.core.api.get_ticker")
    def test_history_uses_period(self, mock_get_ticker: MagicMock):
        ticker = MagicMock()
        ticker.history.return_value = pd.DataFrame({"Close": [150.0]})
        mock_get_ticker.return_value = ticker

        fetch_raw_data("AAPL", "history")
        ticker.history.assert_called_once_with(period="1mo")


class TestRenderHtml:
    def test_error_payload(self):
        html = render_html({"type": "error", "message": "Something went wrong"})
        assert "error" in html
        assert "Something went wrong" in html

    def test_empty_payload(self):
        html = render_html({"type": "empty", "message": "No data available"})
        assert "empty" in html
        assert "No data available" in html

    def test_dataframe_payload(self):
        payload = {
            "type": "dataframe",
            "columns": ["A", "B"],
            "index": ["0", "1"],
            "data": [[1, 2], [3, 4]],
        }
        html = render_html(payload)
        assert "data-table" in html
        assert "<table" in html

    def test_series_payload(self):
        payload = {
            "type": "series",
            "index": ["2024-01", "2024-02"],
            "data": [0.5, 0.6],
        }
        html = render_html(payload)
        assert "data-table" in html
        assert "Value" in html

    def test_dict_payload(self):
        payload = {"type": "dict", "data": {"price": 150.0, "volume": 1000000}}
        html = render_html(payload)
        assert "data-table" in html
        assert "price" in html
        assert "Key" in html
        assert "Value" in html

    def test_list_payload(self):
        payload = {
            "type": "list",
            "data": [{"type": "10-K", "date": "2024-01-01"}, {"type": "10-Q", "date": "2024-04-01"}],
        }
        html = render_html(payload)
        assert "data-table" in html
        assert "10-K" in html

    def test_fallback_payload(self):
        html = render_html({"type": "fallback", "data": "some raw text"})
        assert "<pre>" in html
        assert "some raw text" in html

    def test_unknown_type_returns_error(self):
        html = render_html({"type": "totally_unknown"})
        assert "error" in html
        assert "totally_unknown" in html
