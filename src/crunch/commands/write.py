"""crunch write — write stdin to a file in a specified format."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from crunch.io import read_input, write_output


def main(
    output: Annotated[str, typer.Argument(help="Output file path (.csv, .tsv, .xlsx, .parquet, .json, .md)")],
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md (overrides extension)"),
    ] = None,
) -> None:
    """Write stdin (or a file) to a specified output file, converting format as needed.

    \b
    Examples:
      crunch load data/penguins.csv | crunch filter --column species --op eq --value Adelie | crunch write adelie.csv
      crunch load data/data.csv | crunch write data.parquet
      crunch load data/data.csv | crunch write report.md -f md
    """
    df = read_input(input)
    write_output(df, output, output_format)
    typer.echo(f"Written to {output}", err=True)
