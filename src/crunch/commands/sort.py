"""crunch sort — sort rows by one or more columns."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input, write_output


def _apply_sort(
    df: pd.DataFrame,
    *,
    by: list[str],
    desc: bool,
    na_position: str,
) -> pd.DataFrame:
    missing = [c for c in by if c not in df.columns]
    if missing:
        raise typer.BadParameter(
            f"Column(s) not found: {missing}. Available: {list(df.columns)}",
            param_hint="--by",
        )
    ascending = not desc
    return df.sort_values(by=by, ascending=ascending, na_position=na_position)


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    by: Annotated[
        Optional[list[str]],
        typer.Option("--by", "-b", help="Column(s) to sort by. Repeatable: --by col1 --by col2"),
    ] = None,
    desc: Annotated[
        bool,
        typer.Option("--desc/--no-desc", "-d", help="Sort descending"),
    ] = False,
    na_position: Annotated[
        str,
        typer.Option("--na-position", help="Where to place NaN values: first or last"),
    ] = "last",
) -> None:
    """Sort rows by one or more columns.

    \b
    Examples:
      crunch sort -i data.csv --by name
      crunch sort -i data.csv --by age --desc
      crunch sort -i data.csv --by region --by revenue --desc
    """
    if not by:
        raise typer.BadParameter("At least one --by column is required.")

    if na_position not in ("first", "last"):
        raise typer.BadParameter("--na-position must be 'first' or 'last'.")

    df = read_input(input)
    result = _apply_sort(df, by=by, desc=desc, na_position=na_position)
    write_output(result, output, output_format)
