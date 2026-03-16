"""crunch filter — filter rows by column condition or pandas query expression."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input, write_output

# Operators that don't require a --value argument
_NO_VALUE_OPS = {"isnull", "notnull"}


def _apply_filter(
    df: pd.DataFrame,
    *,
    column: Optional[str],
    op: Optional[str],
    value: Optional[str],
    query: Optional[str],
    case_sensitive: bool,
) -> pd.DataFrame:
    if query is not None:
        try:
            return df.query(query)
        except Exception as e:
            raise typer.BadParameter(f"Invalid query expression: {e}", param_hint="--query")

    # column/op/value mode
    if column not in df.columns:
        raise typer.BadParameter(
            f"Column '{column}' not found. Available: {list(df.columns)}",
            param_hint="--column",
        )

    col = df[column]

    # Coerce value to column dtype for numeric comparisons
    def _coerce(v: str) -> object:
        try:
            if pd.api.types.is_integer_dtype(col):
                return int(v)
            if pd.api.types.is_float_dtype(col):
                return float(v)
        except (ValueError, TypeError):
            pass
        return v

    if op == "eq":
        mask = col == _coerce(value)  # type: ignore[arg-type]
    elif op == "ne":
        mask = col != _coerce(value)  # type: ignore[arg-type]
    elif op == "gt":
        mask = col > _coerce(value)  # type: ignore[arg-type]
    elif op == "ge":
        mask = col >= _coerce(value)  # type: ignore[arg-type]
    elif op == "lt":
        mask = col < _coerce(value)  # type: ignore[arg-type]
    elif op == "le":
        mask = col <= _coerce(value)  # type: ignore[arg-type]
    elif op == "contains":
        mask = col.astype(str).str.contains(str(value), case=case_sensitive, na=False, regex=False)
    elif op == "startswith":
        mask = col.astype(str).str.startswith(str(value))
        if not case_sensitive:
            mask = col.astype(str).str.lower().str.startswith(str(value).lower())
    elif op == "endswith":
        mask = col.astype(str).str.endswith(str(value))
        if not case_sensitive:
            mask = col.astype(str).str.lower().str.endswith(str(value).lower())
    elif op == "isnull":
        mask = col.isna()
    elif op == "notnull":
        mask = col.notna()
    else:
        raise typer.BadParameter(f"Unknown operator '{op}'.", param_hint="--op")

    return df[mask]


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    column: Annotated[
        Optional[str], typer.Option("--column", "-c", help="Column to filter on")
    ] = None,
    op: Annotated[
        Optional[str],
        typer.Option(
            "--op",
            help="Operator: eq ne gt ge lt le contains startswith endswith isnull notnull",
        ),
    ] = None,
    value: Annotated[
        Optional[str], typer.Option("--value", "-v", help="Value to compare against")
    ] = None,
    query: Annotated[
        Optional[str],
        typer.Option("--query", "-q", help="Pandas .query() expression (mutually exclusive with --column/--op/--value)"),
    ] = None,
    case_sensitive: Annotated[
        bool,
        typer.Option("--case-sensitive/--no-case-sensitive", help="Case sensitivity for string operators"),
    ] = True,
) -> None:
    """Filter rows by a column condition or a pandas query expression.

    \b
    Examples:
      crunch filter -i data.csv --column age --op gt --value 30
      crunch filter -i data.csv --query "age > 30 and score < 80"
      crunch filter -i data.csv --column name --op contains --value alice --no-case-sensitive
    """
    # Mutual exclusion check
    if query is not None and any(x is not None for x in (column, op, value)):
        raise typer.BadParameter(
            "--query is mutually exclusive with --column / --op / --value."
        )

    if query is None:
        if column is None:
            raise typer.BadParameter("Provide --column and --op (or use --query).")
        if op is None:
            raise typer.BadParameter("--op is required when using --column.")
        if op not in _NO_VALUE_OPS and value is None:
            raise typer.BadParameter(f"--value is required for operator '{op}'.")

    df = read_input(input)
    result = _apply_filter(df, column=column, op=op, value=value, query=query, case_sensitive=case_sensitive)
    write_output(result, output, output_format)
