import typer
from rich.console import Console
from rich.table import Table

from study_notebook.core.api import (
    add_ticker_to_collection,
    create_collection,
    delete_collection,
    get_collection_by_name,
    list_collections,
    remove_ticker_from_collection,
)

app = typer.Typer(help="Manage ticker collections.")
console = Console()


@app.command("list")
def collection_list() -> None:
    """List all collections with ticker counts."""
    collections = list_collections()
    if not collections:
        console.print("[dim]No collections found.[/dim]")
        return
    table = Table(title="Collections")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Tickers", justify="right")
    for col in collections:
        table.add_row(str(col.id), col.name, str(len(col.tickers)))
    console.print(table)


@app.command("create")
def collection_create(name: str = typer.Argument(..., help="Collection name")) -> None:
    """Create a new collection."""
    col = create_collection(name)
    console.print(f"[green]Collection '{col.name}' created (id={col.id}).[/green]")


@app.command("delete")
def collection_delete(name: str = typer.Argument(..., help="Collection name")) -> None:
    """Delete a collection."""
    if not typer.confirm(f"Delete collection '{name}'?"):
        raise typer.Abort()
    ok = delete_collection(name)
    if ok:
        console.print(f"[green]Collection '{name}' deleted.[/green]")
    else:
        console.print(f"[red]Collection '{name}' not found.[/red]")
        raise typer.Exit(1)


@app.command("add-ticker")
def collection_add_ticker(
    collection: str = typer.Argument(..., help="Collection name"),
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    name: str = typer.Option("", "--name", help="Ticker display name"),
) -> None:
    """Add a ticker to a collection."""
    ok = add_ticker_to_collection(symbol, collection, ticker_name=name)
    if ok:
        console.print(f"[green]Ticker '{symbol.upper()}' added to '{collection}'.[/green]")
    else:
        console.print(f"[red]Collection '{collection}' not found.[/red]")
        raise typer.Exit(1)


@app.command("remove-ticker")
def collection_remove_ticker(
    collection: str = typer.Argument(..., help="Collection name"),
    symbol: str = typer.Argument(..., help="Ticker symbol"),
) -> None:
    """Remove a ticker from a collection."""
    ok = remove_ticker_from_collection(symbol, collection)
    if ok:
        console.print(f"[green]Ticker '{symbol.upper()}' removed from '{collection}'.[/green]")
    else:
        console.print(f"[red]Ticker '{symbol.upper()}' not found in '{collection}'.[/red]")
        raise typer.Exit(1)


@app.command("show")
def collection_show(name: str = typer.Argument(..., help="Collection name")) -> None:
    """Show all tickers in a collection."""
    col = get_collection_by_name(name)
    if col is None:
        console.print(f"[red]Collection '{name}' not found.[/red]")
        raise typer.Exit(1)
    if not col.tickers:
        console.print(f"[dim]Collection '{name}' is empty.[/dim]")
        return
    table = Table(title=f"Collection: {col.name}")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name")
    for ticker in col.tickers:
        table.add_row(ticker.symbol, ticker.name)
    console.print(table)
