"""crunch transform — apply a Python expression to a column."""

from __future__ import annotations

from typing import Annotated, Optional

import numpy as np
import pandas as pd
import typer

from crunch.io import read_input, write_output


def _apply_transform(
    df: pd.DataFrame,
    *,
    column: str,
    expr: str,
    output_col: Optional[str],
    keep_original: bool,
) -> pd.DataFrame:
    if column not in df.columns:
        raise typer.BadParameter(
            f"Column '{column}' not found. Available: {list(df.columns)}",
            param_hint="--column",
        )

    col = df[column]  # noqa: F841 — available in eval scope
    try:
        result = eval(expr, {"col": col, "np": np, "pd": pd})  # noqa: S307
    except Exception as e:
        raise typer.BadParameter(f"Expression error: {e}", param_hint="--expr")

    df = df.copy()

    if output_col is None or output_col == column:
        # Overwrite in place
        df[column] = result
    else:
        df[output_col] = result
        if not keep_original:
            df = df.drop(columns=[column])

    return df


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    column: Annotated[
        str, typer.Option("--column", "-c", help="Source column name (available as `col` in the expression)")
    ] = ...,  # type: ignore[assignment]
    expr: Annotated[
        str,
        typer.Option(
            "--expr", "-e",
            help="Python expression. Column is bound to `col`. Numpy as `np`, pandas as `pd`.",
        ),
    ] = ...,  # type: ignore[assignment]
    output_col: Annotated[
        Optional[str],
        typer.Option("--output-col", help="Name for the result column. Omit to overwrite source column."),
    ] = None,
    keep_original: Annotated[
        bool,
        typer.Option(
            "--keep-original/--no-keep-original",
            help="Keep the source column when --output-col creates a new column.",
        ),
    ] = False,
) -> None:
    """Apply a Python expression to a column.

    \b
    The source column is available as `col` in the expression.
    numpy is available as `np`, pandas as `pd`.

    \b
    Security: --expr is evaluated with Python's eval(). Only pass expressions
    you trust. Never pipe untrusted user input directly into --expr.

    \b
    Examples:
      crunch transform -i data.csv --column salary --expr "col * 1.1"
      crunch transform -i data.csv --column name --expr "col.str.upper()"
      crunch transform -i data.csv --column score --expr "np.log(col)" --output-col log_score
    """
    df = read_input(input)
    result = _apply_transform(df, column=column, expr=expr, output_col=output_col, keep_original=keep_original)
    write_output(result, output, output_format)
