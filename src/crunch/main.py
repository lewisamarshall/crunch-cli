"""crunch — entry point and Typer app registration."""

import typer

from crunch.commands import filter as filter_cmd
from crunch.commands import melt as melt_cmd
from crunch.commands import pivot as pivot_cmd
from crunch.commands import plot as plot_cmd
from crunch.commands import regression as regression_cmd
from crunch.commands import sort as sort_cmd
from crunch.commands import transform as transform_cmd

app = typer.Typer(
    name="crunch",
    help="[bold]crunch[/bold] — pipe-friendly CLI for tabular data transformations.\n\n"
    "All commands read from [cyan]stdin[/cyan] by default ([bold]-i -[/bold]) and write "
    "[cyan]CSV[/cyan] to [cyan]stdout[/cyan] by default ([bold]-o -[/bold]), "
    "making them chainable with [bold]|[/bold].",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)

app.command("filter")(filter_cmd.main)
app.command("sort")(sort_cmd.main)
app.command("transform")(transform_cmd.main)
app.command("regression")(regression_cmd.main)
app.command("pivot")(pivot_cmd.main)
app.command("melt")(melt_cmd.main)
app.command("plot")(plot_cmd.main)

if __name__ == "__main__":
    app()
