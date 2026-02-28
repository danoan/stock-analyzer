import typer
from rich.console import Console
from rich.panel import Panel

from study_notebook.core.api import get_available_metrics

app = typer.Typer(help="Explore available metrics from api-explorer.")
console = Console()


@app.command("list")
def metrics_list(
    ticker: str = typer.Option("AAPL", "--ticker", help="Sample ticker to fetch metrics from"),
) -> None:
    """List numeric metrics available from the info endpoint."""
    try:
        metrics = get_available_metrics(sample_ticker=ticker)
    except Exception as e:
        console.print(f"[red]Error fetching metrics: {e}[/red]")
        raise typer.Exit(1)

    if not metrics:
        console.print("[dim]No numeric metrics found.[/dim]")
        return

    console.print(Panel(", ".join(metrics), title=f"Numeric metrics ({ticker})", expand=False))
    console.print(f"[dim]{len(metrics)} metrics available.[/dim]")
