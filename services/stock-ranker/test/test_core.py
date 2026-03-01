"""Tests for core business logic: evaluate_expression, normalization, score computation, CRUD."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from stock_ranker.core.api import (
    _normalize_values,
    _split_additive_terms,
    _to_numeric,
    add_ticker_to_collection,
    compute_score,
    create_analysis,
    create_collection,
    delete_analysis,
    delete_collection,
    evaluate_expression,
    fetch_info,
    get_analysis,
    get_analysis_by_name,
    get_available_metrics,
    get_collection_by_name,
    list_all_tickers,
    list_analyses,
    list_collections,
    lookup_tickers,
    realize_analysis,
    remove_ticker_from_collection,
    update_analysis,
)
from stock_ranker.core.model import (
    Analysis,
    LookupResult,
    Score,
)

# ---------------------------------------------------------------------------
# evaluate_expression
# ---------------------------------------------------------------------------


def test_evaluate_expression_basic():
    result = evaluate_expression("a + b", {"a": 1.0, "b": 2.0})
    assert result == pytest.approx(3.0)


def test_evaluate_expression_none_propagation():
    result = evaluate_expression("a + b", {"a": None, "b": 2.0})
    assert result is None


def test_evaluate_expression_nan_guard():
    result = evaluate_expression("a", {"a": float("nan")})
    assert result is None


def test_evaluate_expression_inf_guard():
    result = evaluate_expression("a", {"a": float("inf")})
    assert result is None


def test_evaluate_expression_invalid_returns_none():
    result = evaluate_expression("undefined_var + 1", {"a": 1.0})
    assert result is None


def test_evaluate_expression_division_by_zero_returns_none():
    result = evaluate_expression("a / b", {"a": 1.0, "b": 0.0})
    assert result is None


def test_evaluate_expression_allowed_functions():
    result = evaluate_expression("sqrt(a)", {"a": 4.0})
    assert result == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# _normalize_values
# ---------------------------------------------------------------------------


def test_normalize_basic():
    values = [0.0, 5.0, 10.0]
    result = _normalize_values(values)
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(1.0)


def test_normalize_all_same_returns_half():
    values = [5.0, 5.0, 5.0]
    result = _normalize_values(values)
    assert result == [0.5, 0.5, 0.5]


def test_normalize_with_none():
    values = [None, 0.0, 10.0]
    result = _normalize_values(values)
    assert result[0] is None
    assert result[1] == pytest.approx(0.0)
    assert result[2] == pytest.approx(1.0)


def test_normalize_all_none():
    values: list[float | None] = [None, None]
    result = _normalize_values(values)
    assert result == [None, None]


# ---------------------------------------------------------------------------
# compute_score
# ---------------------------------------------------------------------------


def test_compute_score_basic():
    score = Score(name="test", expression="pe + eps")
    info = {"pe": 10.0, "eps": 2.0}
    result, detail = compute_score(score, info)
    assert result == pytest.approx(12.0)
    assert detail.variables == {"eps": 2.0, "pe": 10.0}
    assert detail.raw_result == pytest.approx(12.0)
    assert detail.result == pytest.approx(12.0)


def test_compute_score_missing_field_returns_none():
    score = Score(name="test", expression="missing_field + 1")
    info = {"pe": 10.0}
    result, detail = compute_score(score, info)
    assert result is None
    assert detail.variables == {"missing_field": None}


def test_compute_score_non_numeric_returns_none():
    score = Score(name="test", expression="name + 1")
    info = {"name": "Apple Inc.", "pe": 10.0}
    result, detail = compute_score(score, info)
    assert result is None


def test_compute_score_with_extra_null_fields():
    score = Score(name="test", expression="pe + eps")
    info = {"pe": 10.0, "eps": 2.0, "companyName": "Apple Inc.", "sector": None, "beta": None}
    result, detail = compute_score(score, info)
    assert result == pytest.approx(12.0)
    assert detail.variables == {"eps": 2.0, "pe": 10.0}


# ---------------------------------------------------------------------------
# Analysis CRUD
# ---------------------------------------------------------------------------


def test_create_and_list_analyses():
    analysis = Analysis(
        name="My Analysis",
        scores=[Score(name="PE Score", expression="pe")],
    )
    saved = create_analysis(analysis)
    assert saved.id is not None
    assert saved.name == "My Analysis"

    all_analyses = list_analyses()
    assert any(a.name == "My Analysis" for a in all_analyses)


def test_get_analysis_by_name():
    analysis = Analysis(
        name="Findable Analysis",
        scores=[Score(name="s", expression="x")],
    )
    create_analysis(analysis)
    found = get_analysis_by_name("Findable Analysis")
    assert found is not None
    assert found.name == "Findable Analysis"


def test_get_analysis_by_name_not_found():
    result = get_analysis_by_name("Nonexistent")
    assert result is None


def test_delete_analysis():
    analysis = Analysis(
        name="To Delete",
        scores=[Score(name="s", expression="x")],
    )
    saved = create_analysis(analysis)
    ok = delete_analysis(saved.id)  # type: ignore[arg-type]
    assert ok is True
    assert get_analysis_by_name("To Delete") is None


# ---------------------------------------------------------------------------
# Collection CRUD
# ---------------------------------------------------------------------------


def test_create_and_list_collections():
    col = create_collection("Tech")
    assert col.name == "Tech"
    cols = list_collections()
    assert any(c.name == "Tech" for c in cols)


def test_add_remove_ticker():
    create_collection("Tech")
    ok = add_ticker_to_collection("AAPL", "Tech", ticker_name="Apple Inc.")
    assert ok is True

    col = get_collection_by_name("Tech")
    assert col is not None
    assert any(t.symbol == "AAPL" for t in col.tickers)

    ok2 = remove_ticker_from_collection("AAPL", "Tech")
    assert ok2 is True

    col2 = get_collection_by_name("Tech")
    assert col2 is not None
    assert not any(t.symbol == "AAPL" for t in col2.tickers)


def test_delete_collection():
    create_collection("ToDelete")
    ok = delete_collection("ToDelete")
    assert ok is True
    assert get_collection_by_name("ToDelete") is None


def test_add_ticker_to_nonexistent_collection():
    ok = add_ticker_to_collection("AAPL", "NonExistent")
    assert ok is False


def test_remove_ticker_from_nonexistent_collection():
    ok = remove_ticker_from_collection("AAPL", "NonExistent")
    assert ok is False


def test_remove_nonexistent_ticker_from_collection():
    create_collection("Tech")
    ok = remove_ticker_from_collection("ZZZZZ", "Tech")
    assert ok is False


def test_delete_nonexistent_collection():
    ok = delete_collection("DoesNotExist")
    assert ok is False


# ---------------------------------------------------------------------------
# _to_numeric
# ---------------------------------------------------------------------------


def test_to_numeric_int():
    assert _to_numeric(5) == 5.0


def test_to_numeric_float():
    assert _to_numeric(3.14) == pytest.approx(3.14)


def test_to_numeric_none():
    assert _to_numeric(None) is None


def test_to_numeric_bool():
    assert _to_numeric(True) is None


def test_to_numeric_string():
    assert _to_numeric("hello") is None


def test_to_numeric_nan():
    assert _to_numeric(float("nan")) is None


def test_to_numeric_inf():
    assert _to_numeric(float("inf")) is None


# ---------------------------------------------------------------------------
# fetch_info
# ---------------------------------------------------------------------------

_INFO_RESPONSE = {"data": {"type": "dict", "data": {"pe": 25.0, "eps": 1.5}}}


def _mock_http(json_body: dict) -> MagicMock:
    """Build a patched httpx.Client whose .post() returns json_body."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = json_body
    mock_resp.raise_for_status.return_value = None
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_resp
    return mock_client_cls


def test_fetch_info_success():
    with patch("stock_ranker.core.api.httpx.Client", _mock_http(_INFO_RESPONSE)):
        result = fetch_info("AAPL")
    assert result == {"pe": 25.0, "eps": 1.5}


def test_fetch_info_wrong_type_raises():
    body = {"data": {"type": "error", "message": "not found"}}
    with patch("stock_ranker.core.api.httpx.Client", _mock_http(body)):
        with pytest.raises(ValueError, match="Unexpected data type"):
            fetch_info("AAPL")


def test_fetch_info_http_error_propagates():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("HTTP 500")
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_resp
    with patch("stock_ranker.core.api.httpx.Client", mock_client_cls):
        with pytest.raises(Exception, match="HTTP 500"):
            fetch_info("AAPL")


# ---------------------------------------------------------------------------
# lookup_tickers
# ---------------------------------------------------------------------------

_LOOKUP_RESPONSE = {
    "results": [
        {"symbol": "AAPL", "shortName": "Apple Inc.", "exchange": "NASDAQ", "quoteType": "EQUITY"}
    ]
}


def test_lookup_tickers_success():
    with patch("stock_ranker.core.api.httpx.Client", _mock_http(_LOOKUP_RESPONSE)):
        results = lookup_tickers("apple")
    assert len(results) == 1
    assert isinstance(results[0], LookupResult)
    assert results[0].symbol == "AAPL"


def test_lookup_tickers_empty_results():
    with patch("stock_ranker.core.api.httpx.Client", _mock_http({"results": []})):
        results = lookup_tickers("xyzzy")
    assert results == []


# ---------------------------------------------------------------------------
# get_available_metrics
# ---------------------------------------------------------------------------


def test_get_available_metrics_returns_sorted_numeric_keys():
    info = {"pe": 25.0, "eps": 1.5, "name": "Apple Inc.", "marketCap": 3e12}
    with patch("stock_ranker.core.api.fetch_info", return_value=info):
        metrics = get_available_metrics("AAPL")
    assert metrics == ["eps", "marketCap", "pe"]


def test_get_available_metrics_excludes_non_numeric():
    info = {"name": "Apple", "sector": "Tech", "pe": 30.0}
    with patch("stock_ranker.core.api.fetch_info", return_value=info):
        metrics = get_available_metrics("AAPL")
    assert metrics == ["pe"]


# ---------------------------------------------------------------------------
# get_analysis (by id)
# ---------------------------------------------------------------------------


def test_get_analysis_by_id_found():
    saved = create_analysis(Analysis(name="ById", scores=[Score(name="s", expression="x")]))
    found = get_analysis(saved.id)  # type: ignore[arg-type]
    assert found is not None
    assert found.name == "ById"
    assert found.id == saved.id


def test_get_analysis_by_id_not_found():
    result = get_analysis(99999)
    assert result is None


# ---------------------------------------------------------------------------
# update_analysis
# ---------------------------------------------------------------------------


def test_update_analysis():
    saved = create_analysis(
        Analysis(name="Original", scores=[Score(name="s", expression="x")])
    )
    saved.name = "Updated"
    saved.scores = [Score(name="new_score", expression="pe + eps")]
    updated = update_analysis(saved)
    assert updated.name == "Updated"
    assert updated.scores[0].name == "new_score"

    # Verify persistence
    reloaded = get_analysis(saved.id)  # type: ignore[arg-type]
    assert reloaded is not None
    assert reloaded.name == "Updated"


# ---------------------------------------------------------------------------
# list_all_tickers
# ---------------------------------------------------------------------------


def test_list_all_tickers_empty():
    assert list_all_tickers() == []


def test_list_all_tickers_returns_added_tickers():
    create_collection("Tech")
    add_ticker_to_collection("AAPL", "Tech", ticker_name="Apple Inc.")
    add_ticker_to_collection("MSFT", "Tech", ticker_name="Microsoft")

    tickers = list_all_tickers()
    symbols = {t.symbol for t in tickers}
    assert "AAPL" in symbols
    assert "MSFT" in symbols


def test_list_all_tickers_ticker_in_multiple_collections_appears_once():
    create_collection("Tech")
    create_collection("SP500")
    add_ticker_to_collection("AAPL", "Tech")
    add_ticker_to_collection("AAPL", "SP500")

    tickers = list_all_tickers()
    assert sum(1 for t in tickers if t.symbol == "AAPL") == 1


# ---------------------------------------------------------------------------
# realize_analysis
# ---------------------------------------------------------------------------


def test_realize_analysis_score():
    analysis = create_analysis(
        Analysis(name="Realize", scores=[Score(name="PE", expression="pe")])
    )
    info = {"pe": 25.0, "eps": 1.5}
    with patch("stock_ranker.core.api.fetch_info", return_value=info):
        results = realize_analysis(analysis, ["AAPL"])

    assert len(results) == 1
    assert results[0].ticker_symbol == "AAPL"
    assert results[0].error is None
    assert results[0].scores["PE"] == pytest.approx(25.0)


def test_realize_analysis_normalize_score():
    score = Score(name="NormPE", expression="pe", normalize=True)
    analysis = create_analysis(Analysis(name="RealizeNorm", scores=[score]))
    ticker_data = {"AAPL": {"pe": 0.0}, "MSFT": {"pe": 10.0}}

    def mock_fetch(symbol, force_refresh=False):
        return ticker_data[symbol]

    with patch("stock_ranker.core.api.fetch_info", side_effect=mock_fetch):
        results = realize_analysis(analysis, ["AAPL", "MSFT"])

    by_symbol = {r.ticker_symbol: r for r in results}
    # min-max [0,1]: AAPL=0.0, MSFT=1.0
    assert by_symbol["AAPL"].scores["NormPE"] == pytest.approx(0.0)
    assert by_symbol["MSFT"].scores["NormPE"] == pytest.approx(1.0)
    # raw_result is preserved in detail
    assert by_symbol["AAPL"].score_details["NormPE"].raw_result == pytest.approx(0.0)
    assert by_symbol["MSFT"].score_details["NormPE"].raw_result == pytest.approx(10.0)


def test_realize_analysis_normalize_per_metric():
    # Two metrics: pe and pb, each normalized independently before evaluating pe + pb.
    # pe:  AAPL=0,  MSFT=10  → normalized: AAPL=0.0, MSFT=1.0
    # pb:  AAPL=10, MSFT=20  → normalized: AAPL=0.0, MSFT=1.0
    # result: AAPL=0.0+0.0=0.0, MSFT=1.0+1.0=2.0
    score = Score(name="S", expression="pe + pb", normalize=True)
    analysis = create_analysis(Analysis(name="NormPerMetric", scores=[score]))
    ticker_data = {"AAPL": {"pe": 0.0, "pb": 10.0}, "MSFT": {"pe": 10.0, "pb": 20.0}}

    def mock_fetch(symbol, force_refresh=False):
        return ticker_data[symbol]

    with patch("stock_ranker.core.api.fetch_info", side_effect=mock_fetch):
        results = realize_analysis(analysis, ["AAPL", "MSFT"])

    by_symbol = {r.ticker_symbol: r for r in results}
    assert by_symbol["AAPL"].scores["S"] == pytest.approx(0.0)
    assert by_symbol["MSFT"].scores["S"] == pytest.approx(2.0)
    # raw values preserved
    assert by_symbol["AAPL"].score_details["S"].raw_result == pytest.approx(10.0)
    assert by_symbol["MSFT"].score_details["S"].raw_result == pytest.approx(30.0)
    assert by_symbol["AAPL"].score_details["S"].variables["pe"] == pytest.approx(0.0)
    assert by_symbol["AAPL"].score_details["S"].variables["pb"] == pytest.approx(10.0)


def test_realize_analysis_normalize_single_term_transform():
    # 5/priceToBook is one term — it should be evaluated first, then normalized.
    # AAPL ptb=5 → 5/5=1.0  MSFT ptb=1 → 5/1=5.0
    # Normalized [1.0, 5.0] → AAPL=0.0, MSFT=1.0
    score = Score(name="S", expression="5/priceToBook", normalize=True)
    analysis = create_analysis(Analysis(name="NormTransform", scores=[score]))
    ticker_data = {"AAPL": {"priceToBook": 5.0}, "MSFT": {"priceToBook": 1.0}}

    def mock_fetch(symbol, force_refresh=False):
        return ticker_data[symbol]

    with patch("stock_ranker.core.api.fetch_info", side_effect=mock_fetch):
        results = realize_analysis(analysis, ["AAPL", "MSFT"])

    by_symbol = {r.ticker_symbol: r for r in results}
    assert by_symbol["AAPL"].scores["S"] == pytest.approx(0.0)
    assert by_symbol["MSFT"].scores["S"] == pytest.approx(1.0)
    assert by_symbol["AAPL"].score_details["S"].raw_result == pytest.approx(1.0)
    assert by_symbol["MSFT"].score_details["S"].raw_result == pytest.approx(5.0)


def test_split_additive_terms():
    assert _split_additive_terms("pe") == ["pe"]
    assert _split_additive_terms("pe + pb") == ["pe", "+ pb"]
    assert _split_additive_terms("pe - pb") == ["pe", "- pb"]
    assert _split_additive_terms("-pe + pb") == ["-pe", "+ pb"]
    assert _split_additive_terms("5*pe + 3/pb") == ["5*pe", "+ 3/pb"]
    assert _split_additive_terms("5*(pe + pb)") == ["5*(pe + pb)"]


def test_realize_analysis_fetch_error_captured():
    analysis = create_analysis(
        Analysis(name="RealizeErr", scores=[Score(name="PE", expression="pe")])
    )
    with patch("stock_ranker.core.api.fetch_info", side_effect=Exception("timeout")):
        results = realize_analysis(analysis, ["AAPL"])

    assert len(results) == 1
    assert results[0].error == "timeout"
    assert results[0].scores == {}
