import typer
from rich.console import Console
from rich.table import Table

from stock_ranker.core.api import list_all_tickers, lookup_tickers

app = typer.Typer(help="Ticker utilities.")
console = Console()


@app.command("list")
def ticker_list() -> None:
    """List all tickers across all collections."""
    tickers = list_all_tickers()
    if not tickers:
        console.print("[dim]No tickers found.[/dim]")
        return
    table = Table(title="All Tickers")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name")
    for t in tickers:
        table.add_row(t.symbol, t.name)
    console.print(table)


@app.command("lookup")
def ticker_lookup(
    query: str = typer.Argument(..., help="Search query"),
    count: int = typer.Option(8, "--count", "-n", help="Number of results"),
) -> None:
    """Look up tickers via api-explorer."""
    try:
        results = lookup_tickers(query, count=count)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    table = Table(title=f"Lookup: {query}")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name")
    table.add_column("Exchange")
    table.add_column("Type")
    for r in results:
        table.add_row(r.symbol, r.shortName, r.exchange, r.quoteType)
    console.print(table)
