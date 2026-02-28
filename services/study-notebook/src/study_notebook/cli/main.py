import typer

from study_notebook.cli.analysis_cmd import app as analysis_app
from study_notebook.cli.collection_cmd import app as collection_app
from study_notebook.cli.metrics_cmd import app as metrics_app
from study_notebook.cli.ticker_cmd import app as ticker_app
from study_notebook.core.model import init_db

app = typer.Typer(
    name="study-notebook",
    help="Financial study tool for analyzing public companies.",
    no_args_is_help=True,
)

app.add_typer(collection_app, name="collection")
app.add_typer(ticker_app, name="ticker")
app.add_typer(analysis_app, name="analysis")
app.add_typer(metrics_app, name="metrics")


@app.callback()
def main() -> None:
    """Initialize the database on every invocation."""
    init_db()


if __name__ == "__main__":
    app()
