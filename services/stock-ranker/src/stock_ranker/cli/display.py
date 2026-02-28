from rich.console import Console
from rich.table import Table

from stock_ranker.core.model import Analysis, RealizationResult
from stock_ranker.utils.utils import fmt_float

console = Console()


def display_realization_table(analysis: Analysis, results: list[RealizationResult]) -> None:
    """Display realization results in a Rich table."""
    score_names = [s.name for s in analysis.scores]

    table = Table(title=f"Analysis: {analysis.name}", show_lines=True)
    table.add_column("Ticker", style="bold cyan", no_wrap=True)
    for name in score_names:
        table.add_column(name, justify="right")
    table.add_column("Error", style="red")

    for result in results:
        row: list[str] = [result.ticker_symbol]
        for name in score_names:
            val = result.scores.get(name)
            row.append(fmt_float(val))
        row.append(result.error or "")
        table.add_row(*row)

    console.print(table)
