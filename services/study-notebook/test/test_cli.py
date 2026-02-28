"""CLI integration tests using typer's CliRunner."""
from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from study_notebook.cli.main import app
from study_notebook.core.model import LookupResult, RealizationResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# Collection commands
# ---------------------------------------------------------------------------


def test_collection_create():
    result = runner.invoke(app, ["collection", "create", "Tech"])
    assert result.exit_code == 0
    assert "Tech" in result.output


def test_collection_list_empty():
    result = runner.invoke(app, ["collection", "list"])
    assert result.exit_code == 0


def test_collection_list_shows_entry():
    runner.invoke(app, ["collection", "create", "Tech2"])
    result = runner.invoke(app, ["collection", "list"])
    assert "Tech2" in result.output


def test_collection_add_ticker():
    runner.invoke(app, ["collection", "create", "Tech3"])
    result = runner.invoke(app, ["collection", "add-ticker", "Tech3", "AAPL"])
    assert result.exit_code == 0
    assert "AAPL" in result.output


def test_collection_remove_ticker():
    runner.invoke(app, ["collection", "create", "Tech4"])
    runner.invoke(app, ["collection", "add-ticker", "Tech4", "AAPL"])
    result = runner.invoke(app, ["collection", "remove-ticker", "Tech4", "AAPL"])
    assert result.exit_code == 0
    assert "AAPL" in result.output


def test_collection_show():
    runner.invoke(app, ["collection", "create", "ShowMe"])
    runner.invoke(app, ["collection", "add-ticker", "ShowMe", "GOOG"])
    result = runner.invoke(app, ["collection", "show", "ShowMe"])
    assert result.exit_code == 0
    assert "GOOG" in result.output


# ---------------------------------------------------------------------------
# Ticker commands
# ---------------------------------------------------------------------------


def test_ticker_lookup_mocked():
    mock_results = [
        LookupResult(symbol="AAPL", shortName="Apple Inc.", exchange="NASDAQ", quoteType="EQUITY")
    ]
    with patch("study_notebook.cli.ticker_cmd.lookup_tickers", return_value=mock_results):
        result = runner.invoke(app, ["ticker", "lookup", "apple"])
    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "Apple" in result.output


def test_ticker_lookup_error():
    with patch(
        "study_notebook.cli.ticker_cmd.lookup_tickers",
        side_effect=Exception("connection refused"),
    ):
        result = runner.invoke(app, ["ticker", "lookup", "apple"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_ticker_list_empty():
    result = runner.invoke(app, ["ticker", "list"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Analysis commands
# ---------------------------------------------------------------------------


def test_analysis_list_empty():
    result = runner.invoke(app, ["analysis", "list"])
    assert result.exit_code == 0


def test_analysis_realize_mocked():
    from study_notebook.core.api import create_analysis
    from study_notebook.core.model import Analysis, Score

    analysis = Analysis(name="Test Analysis", scores=[Score(name="PE", expression="pe")])
    saved = create_analysis(analysis)

    mock_results = [
        RealizationResult(ticker_symbol="AAPL", scores={"PE": 25.0}, error=None),
    ]
    with patch("study_notebook.cli.analysis_cmd.realize_analysis", return_value=mock_results):
        result = runner.invoke(app, ["analysis", "realize", str(saved.id), "--ticker", "AAPL"])

    assert result.exit_code == 0
    assert "AAPL" in result.output


def test_analysis_realize_not_found():
    result = runner.invoke(app, ["analysis", "realize", "9999", "--ticker", "AAPL"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


# ---------------------------------------------------------------------------
# Metrics commands
# ---------------------------------------------------------------------------


def test_metrics_list_mocked():
    mock_metrics = ["eps", "pe", "revenue"]
    with patch(
        "study_notebook.cli.metrics_cmd.get_available_metrics", return_value=mock_metrics
    ):
        result = runner.invoke(app, ["metrics", "list"])
    assert result.exit_code == 0
    assert "eps" in result.output
    assert "pe" in result.output


def test_metrics_list_error():
    with patch(
        "study_notebook.cli.metrics_cmd.get_available_metrics",
        side_effect=Exception("no api"),
    ):
        result = runner.invoke(app, ["metrics", "list"])
    assert result.exit_code != 0
    assert "Error" in result.output
