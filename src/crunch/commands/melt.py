"""crunch melt — unpivot (melt) from wide to long format."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input, write_output


def _apply_melt(
    df: pd.DataFrame,
    *,
    id_vars: Optional[list[str]],
    value_vars: Optional[list[str]],
    var_name: str,
    value_name: str,
) -> pd.DataFrame:
    all_mentioned = (id_vars or []) + (value_vars or [])
    missing = [c for c in all_mentioned if c not in df.columns]
    if missing:
        raise typer.BadParameter(
            f"Column(s) not found: {missing}. Available: {list(df.columns)}"
        )

    # pandas 2.x raises if value_name/var_name collides with any input column.
    # Rename conflicting columns that aren't part of the melt before proceeding.
    kept = set(id_vars or []) | set(value_vars or [])
    rename_map = {}
    existing = set(df.columns)
    for col in df.columns:
        if col in kept:
            continue
        if col == value_name or col == var_name:
            # Find a safe temporary name that doesn't collide with any existing column
            candidate = f"__{col}__"
            while candidate in existing:
                candidate = f"_{candidate}_"
            rename_map[col] = candidate
            existing.add(candidate)
    if rename_map:
        df = df.rename(columns=rename_map)

    return df.melt(
        id_vars=id_vars or None,
        value_vars=value_vars or None,
        var_name=var_name,
        value_name=value_name,
    )


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    id_vars: Annotated[
        Optional[list[str]],
        typer.Option("--id-vars", help="Columns to keep as identifier variables. Repeatable."),
    ] = None,
    value_vars: Annotated[
        Optional[list[str]],
        typer.Option("--value-vars", help="Columns to unpivot. Defaults to all non-id columns."),
    ] = None,
    var_name: Annotated[
        str, typer.Option("--var-name", help="Name for the new variable column.")
    ] = "variable",
    value_name: Annotated[
        str, typer.Option("--value-name", help="Name for the new values column.")
    ] = "value",
) -> None:
    """Unpivot (melt) a DataFrame from wide to long format.

    \b
    Examples:
      crunch melt -i wide.csv --id-vars id name --value-vars q1 q2 q3
      crunch melt -i data.csv --id-vars id --var-name metric --value-name score
    """
    df = read_input(input)
    result = _apply_melt(df, id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)
    write_output(result, output, output_format)
