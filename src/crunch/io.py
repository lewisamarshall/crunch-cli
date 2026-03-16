"""Central I/O contract for crunch commands.

All commands must use read_input() and write_output() exclusively.
No command module should import sys, open, or pd.read_csv directly.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

_READ_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".txt": "tsv",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".parquet": "parquet",
    ".pq": "parquet",
    ".json": "json",
}

_WRITE_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".txt": "tsv",
    ".xlsx": "xlsx",
    ".json": "json",
    ".parquet": "parquet",
    ".pq": "parquet",
    ".md": "md",
    ".markdown": "md",
}

_BINARY_WRITE_FORMATS = {"xlsx", "parquet"}


def detect_read_format(path: str) -> str:
    ext = Path(path).suffix.lower()
    fmt = _READ_EXTENSIONS.get(ext)
    if fmt is None:
        raise typer.BadParameter(
            f"Unrecognized file extension '{ext}' for input '{path}'. "
            f"Supported: {', '.join(_READ_EXTENSIONS)}"
        )
    return fmt


def detect_write_format(path: str) -> str:
    ext = Path(path).suffix.lower()
    fmt = _WRITE_EXTENSIONS.get(ext)
    if fmt is None:
        raise typer.BadParameter(
            f"Unrecognized file extension '{ext}' for output '{path}'. "
            f"Supported: {', '.join(_WRITE_EXTENSIONS)}"
        )
    return fmt


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def read_input(source: str) -> pd.DataFrame:
    """Read tabular data from a file path or '-' for stdin.

    File format is detected from the extension. Excel files cannot be
    read from stdin (they require a seekable binary stream).
    """
    source = source or "-"

    if source == "-":
        try:
            return pd.read_csv(sys.stdin)
        except pd.errors.EmptyDataError:
            raise typer.BadParameter("No data received on stdin.")
        except pd.errors.ParserError as e:
            raise typer.BadParameter(f"Failed to parse stdin as CSV: {e}")

    path = Path(source)
    if not path.exists():
        raise typer.BadParameter(f"Input file not found: '{source}'")

    fmt = detect_read_format(source)

    if fmt in ("xlsx", "xls"):
        engine = "openpyxl" if fmt == "xlsx" else "xlrd"
        try:
            return pd.read_excel(path, engine=engine)
        except Exception as e:
            raise typer.BadParameter(f"Failed to read Excel file '{source}': {e}")

    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            raise typer.BadParameter(
                "Parquet support requires pyarrow. Install with: pip install pyarrow"
            )
        try:
            return pd.read_parquet(path)
        except Exception as e:
            raise typer.BadParameter(f"Failed to read Parquet file '{source}': {e}")

    if fmt == "json":
        try:
            return pd.read_json(path)
        except Exception as e:
            raise typer.BadParameter(f"Failed to read JSON file '{source}': {e}")

    # csv / tsv
    sep = "\t" if fmt == "tsv" else ","
    try:
        return pd.read_csv(path, sep=sep)
    except pd.errors.EmptyDataError:
        raise typer.BadParameter(f"Input file is empty: '{source}'")
    except pd.errors.ParserError as e:
        raise typer.BadParameter(f"Failed to parse '{source}': {e}")


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def write_output(df: pd.DataFrame, dest: str, fmt: Optional[str] = None) -> None:
    """Write a DataFrame to a file path or '-' for stdout.

    Format resolution order:
      1. Explicit fmt argument (from --output-format flag)
      2. Inferred from file extension
      3. Default: 'csv'

    Binary formats (xlsx, parquet) cannot be written to stdout.
    """
    dest = dest or "-"

    # Resolve format
    if fmt is None:
        if dest == "-":
            fmt = "csv"
        else:
            fmt = detect_write_format(dest)

    fmt = fmt.lower()

    if dest == "-" and fmt in _BINARY_WRITE_FORMATS:
        raise typer.BadParameter(
            f"Format '{fmt}' is binary and cannot be written to stdout. "
            "Specify an output file path with -o."
        )

    if fmt == "csv":
        if dest == "-":
            df.to_csv(sys.stdout, index=False)
        else:
            df.to_csv(dest, index=False)

    elif fmt == "tsv":
        if dest == "-":
            df.to_csv(sys.stdout, sep="\t", index=False)
        else:
            df.to_csv(dest, sep="\t", index=False)

    elif fmt == "xlsx":
        df.to_excel(dest, engine="openpyxl", index=False)

    elif fmt == "json":
        json_str = df.to_json(orient="records", indent=2)
        if dest == "-":
            sys.stdout.write(json_str)
            sys.stdout.write("\n")
        else:
            Path(dest).write_text(json_str, encoding="utf-8")

    elif fmt == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            raise typer.BadParameter(
                "Parquet support requires pyarrow. Install with: pip install pyarrow"
            )
        df.to_parquet(dest, index=False)

    elif fmt in ("md", "markdown"):
        md_str = df.to_markdown(index=False)
        if dest == "-":
            sys.stdout.write(md_str)
            sys.stdout.write("\n")
        else:
            Path(dest).write_text(md_str, encoding="utf-8")  # type: ignore[arg-type]

    else:
        valid = "csv, tsv, xlsx, json, parquet, md"
        raise typer.BadParameter(f"Unknown output format '{fmt}'. Valid: {valid}")
