"""crunch load — read a file and stream it to stdout."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from crunch.io import read_input, write_output


def main(
    input: Annotated[str, typer.Argument(help="Input file path (csv, tsv, xlsx, parquet, …)")],
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, json, md (default: csv)"),
    ] = None,
) -> None:
    """Read a file and write it to stdout, optionally converting format.

    \b
    Examples:
      crunch load data/penguins.csv | crunch filter --column species --op eq --value Adelie
      crunch load data/wide.xlsx -f csv | crunch melt --id-vars id
      crunch load data/data.parquet -f tsv
    """
    df = read_input(input)
    write_output(df, "-", output_format)
