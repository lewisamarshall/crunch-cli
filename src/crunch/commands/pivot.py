"""crunch pivot — pivot table aggregation."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input, write_output

_AGGFUNCS = {"mean", "sum", "count", "min", "max", "median", "first", "last", "std"}


def _apply_pivot(
    df: pd.DataFrame,
    *,
    index: list[str],
    columns: list[str],
    values: Optional[list[str]],
    aggfunc: str,
    fill_value: Optional[str],
    flatten_cols: bool,
) -> pd.DataFrame:
    missing = [c for c in index + columns + (values or []) if c not in df.columns]
    if missing:
        raise typer.BadParameter(
            f"Column(s) not found: {missing}. Available: {list(df.columns)}"
        )

    # Coerce fill_value
    fv: object = None
    if fill_value is not None:
        try:
            fv = float(fill_value)
        except ValueError:
            fv = fill_value

    kwargs: dict = dict(
        index=index if len(index) > 1 else index[0],
        columns=columns if len(columns) > 1 else columns[0],
        aggfunc=aggfunc,
    )
    if values:
        kwargs["values"] = values if len(values) > 1 else values[0]
    if fv is not None:
        kwargs["fill_value"] = fv

    try:
        result = pd.pivot_table(df, **kwargs)
    except Exception as e:
        raise typer.BadParameter(f"Pivot failed: {e}")

    if flatten_cols and isinstance(result.columns, pd.MultiIndex):
        result.columns = ["_".join(str(s) for s in col).strip("_") for col in result.columns]

    return result.reset_index()


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    index: Annotated[
        Optional[list[str]],
        typer.Option("--index", help="Column(s) to use as the pivot index. Repeatable."),
    ] = None,
    columns: Annotated[
        Optional[list[str]],
        typer.Option("--columns", help="Column(s) whose unique values become new headers. Repeatable."),
    ] = None,
    values: Annotated[
        Optional[list[str]],
        typer.Option("--values", help="Column(s) to aggregate. Defaults to all remaining columns."),
    ] = None,
    aggfunc: Annotated[
        str,
        typer.Option("--aggfunc", "-a", help="Aggregation function: mean sum count min max median first last std"),
    ] = "mean",
    fill_value: Annotated[
        Optional[str],
        typer.Option("--fill-value", help="Value to replace NaN in the result."),
    ] = None,
    flatten_cols: Annotated[
        bool,
        typer.Option("--flatten-cols/--no-flatten-cols", help="Flatten MultiIndex columns to strings."),
    ] = True,
) -> None:
    """Aggregate data into a pivot table.

    \b
    Examples:
      crunch pivot -i data.csv --index region --columns category --values revenue --aggfunc sum
      crunch pivot -i data.csv --index year --columns product --aggfunc count --fill-value 0
    """
    if not index:
        raise typer.BadParameter("At least one --index column is required.")
    if not columns:
        raise typer.BadParameter("At least one --columns column is required.")
    if aggfunc not in _AGGFUNCS:
        raise typer.BadParameter(f"--aggfunc must be one of: {', '.join(sorted(_AGGFUNCS))}")

    df = read_input(input)
    result = _apply_pivot(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        fill_value=fill_value,
        flatten_cols=flatten_cols,
    )
    write_output(result, output, output_format)
