from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from stock_ranker.cli.display import display_realization_table
from stock_ranker.cli.wizard import run_wizard
from stock_ranker.core.api import (
    create_analysis,
    delete_analysis,
    get_analysis,
    get_analysis_by_name,
    get_collection_by_name,
    list_analyses,
    realize_analysis,
)

app = typer.Typer(help="Manage and run analyses.")
console = Console()


def _resolve_analysis(name_or_id: str):
    """Resolve an analysis by name or integer id."""
    if name_or_id.isdigit():
        a = get_analysis(int(name_or_id))
    else:
        a = get_analysis_by_name(name_or_id)
    return a


@app.command("list")
def analysis_list() -> None:
    """List all analyses."""
    analyses = list_analyses()
    if not analyses:
        console.print("[dim]No analyses found.[/dim]")
        return
    for a in analyses:
        score_names = ", ".join(s.name for s in a.scores)
        console.print(f"[bold]{a.id}[/bold] {a.name}  [dim]({score_names})[/dim]")


@app.command("create")
def analysis_create() -> None:
    """Create a new analysis via the interactive wizard."""
    analysis = run_wizard()
    saved = create_analysis(analysis)
    console.print(f"[green]Analysis '{saved.name}' saved (id={saved.id}).[/green]")


@app.command("show")
def analysis_show(
    name_or_id: str = typer.Argument(..., help="Analysis name or id"),
) -> None:
    """Show details of an analysis."""
    a = _resolve_analysis(name_or_id)
    if a is None:
        console.print(f"[red]Analysis '{name_or_id}' not found.[/red]")
        raise typer.Exit(1)

    lines = [f"[bold]Name:[/bold] {a.name}", f"[bold]ID:[/bold] {a.id}", ""]
    for score in a.scores:
        label = "[green][normalized][/green] " if score.normalize else ""
        lines.append(f"  {label}score: [bold]{score.name}[/bold]")
        lines.append(f"    Expression: {score.expression}")
    console.print(Panel("\n".join(lines), title="Analysis", expand=False))


@app.command("delete")
def analysis_delete(
    name_or_id: str = typer.Argument(..., help="Analysis name or id"),
) -> None:
    """Delete an analysis."""
    a = _resolve_analysis(name_or_id)
    if a is None:
        console.print(f"[red]Analysis '{name_or_id}' not found.[/red]")
        raise typer.Exit(1)
    if not typer.confirm(f"Delete analysis '{a.name}'?"):
        raise typer.Abort()
    delete_analysis(a.id)  # type: ignore[arg-type]
    console.print(f"[green]Analysis '{a.name}' deleted.[/green]")


@app.command("realize")
def analysis_realize(
    name_or_id: str = typer.Argument(..., help="Analysis name or id"),
    collection: list[str] = typer.Option(
        [], "--collection", "-c", help="Collection name (can repeat)"
    ),
    ticker: list[str] = typer.Option(
        [], "--ticker", "-t", help="Ticker symbol (can repeat)"
    ),
    force_refresh: bool = typer.Option(False, "--force-refresh", help="Force cache refresh"),
) -> None:
    """Realize an analysis against tickers."""
    a = _resolve_analysis(name_or_id)
    if a is None:
        console.print(f"[red]Analysis '{name_or_id}' not found.[/red]")
        raise typer.Exit(1)

    # Gather tickers
    symbols: list[str] = list(ticker)
    for col_name in collection:
        col = get_collection_by_name(col_name)
        if col is None:
            console.print(f"[red]Collection '{col_name}' not found.[/red]")
            raise typer.Exit(1)
        symbols.extend(t.symbol for t in col.tickers)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_symbols: list[str] = []
    for s in symbols:
        su = s.upper()
        if su not in seen:
            seen.add(su)
            unique_symbols.append(su)

    if not unique_symbols:
        console.print("[red]No tickers specified. Use --collection or --ticker.[/red]")
        raise typer.Exit(1)

    console.print(f"Realizing '{a.name}' against {unique_symbols}…")

    try:
        results = realize_analysis(a, unique_symbols, force_refresh=force_refresh)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    display_realization_table(a, results)
