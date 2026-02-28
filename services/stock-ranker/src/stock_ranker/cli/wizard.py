from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from stock_ranker.core.model import Analysis, Score

console = Console()


def _prompt_score() -> Score:
    """Interactively prompt for a Score definition."""
    name = typer.prompt("  Score name")
    show_metrics = typer.confirm("  Show available metrics first?", default=False)
    if show_metrics:
        _show_metrics()
    expression = typer.prompt("  Expression (use metric names as variables)")
    normalize = typer.confirm("  Normalize across tickers? [0-1]", default=False)
    return Score(name=name, expression=expression, normalize=normalize)


def _show_metrics() -> None:
    """Fetch and display available metrics from api-explorer."""
    try:
        from stock_ranker.core.api import get_available_metrics

        metrics = get_available_metrics()
        console.print(Panel(", ".join(metrics), title="Available numeric metrics", expand=False))
    except Exception as e:
        console.print(f"  [red]Could not fetch metrics: {e}[/red]")


def run_wizard() -> Analysis:
    """Run the interactive analysis creation wizard. Returns an unsaved Analysis."""
    console.print(Panel("[bold]Analysis Creation Wizard[/bold]", expand=False))

    name = typer.prompt("Analysis name")
    scores: list[Score] = []

    while True:
        choice = typer.prompt(
            "Add score? [yes/done]", default="done"
        ).lower().strip()

        if choice in ("done", "d", "no", "n", ""):
            break
        elif choice in ("yes", "y", "score", "s"):
            console.print("[bold]Score[/bold]")
            score = _prompt_score()
            scores.append(score)
            console.print(f"[green]Score '{score.name}' added.[/green]")
        else:
            console.print("[red]Unknown choice. Enter 'yes' or 'done'.[/red]")

    analysis = Analysis(name=name, scores=scores)

    console.print()
    console.print(Panel(
        f"Name: {analysis.name}\nScores: {[s.name for s in analysis.scores]}",
        title="Analysis summary",
        expand=False,
    ))

    if not typer.confirm("Save this analysis?", default=True):
        raise typer.Abort()

    return analysis
