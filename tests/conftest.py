"""Shared fixtures for crunch tests."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 20
    df = pd.DataFrame(
        {
            "name": [
                "Alice", "Bob", "Carol", "Dave", "Eve",
                "Frank", "Grace", "Hank", "Ivy", "Jack",
                "Alice", "Bob", "Carol", "Dave", "Eve",
                "Frank", "Grace", "Hank", "Ivy", "Jack",
            ],
            "age": [25, 32, 29, 45, 22, 38, 31, 27, 34, 41,
                    28, 35, 30, 47, 23, 39, 33, 26, 36, 42],
            "score": rng.uniform(50, 100, n).round(2),
            "category": rng.choice(["A", "B", "C"], n).tolist(),
            "value": rng.normal(1000, 200, n).round(2),
        }
    )
    # Introduce a couple of NaN values
    df.loc[3, "score"] = np.nan
    df.loc[15, "value"] = np.nan
    return df


@pytest.fixture
def csv_file(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    p = tmp_path / "data.csv"
    sample_df.to_csv(p, index=False)
    return p


@pytest.fixture
def excel_file(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    p = tmp_path / "data.xlsx"
    sample_df.to_excel(p, index=False, engine="openpyxl")
    return p


def df_from_stdout(stdout: str) -> pd.DataFrame:
    """Parse a CSV string from captured stdout into a DataFrame."""
    return pd.read_csv(io.StringIO(stdout))
