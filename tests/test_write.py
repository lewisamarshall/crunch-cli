"""Tests for crunch write command."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from crunch.__main__ import app


def invoke_write(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["write"] + args, input=csv_in)


class TestWrite:
    def test_writes_csv(self, runner, sample_df, tmp_path):
        dest = tmp_path / "out.csv"
        csv_in = sample_df.to_csv(index=False)
        r = invoke_write(runner, csv_in, [str(dest)])
        assert r.exit_code == 0
        assert dest.exists()
        out = pd.read_csv(dest)
        assert list(out.columns) == list(sample_df.columns)

    def test_writes_xlsx(self, runner, sample_df, tmp_path):
        dest = tmp_path / "out.xlsx"
        csv_in = sample_df.to_csv(index=False)
        r = invoke_write(runner, csv_in, [str(dest)])
        assert r.exit_code == 0
        assert dest.exists()
        out = pd.read_excel(dest)
        assert list(out.columns) == list(sample_df.columns)

    def test_writes_tsv(self, runner, sample_df, tmp_path):
        dest = tmp_path / "out.tsv"
        csv_in = sample_df.to_csv(index=False)
        r = invoke_write(runner, csv_in, [str(dest)])
        assert r.exit_code == 0
        assert dest.exists()

    def test_format_override(self, runner, sample_df, tmp_path):
        dest = tmp_path / "out.txt"
        csv_in = sample_df.to_csv(index=False)
        r = invoke_write(runner, csv_in, [str(dest), "-f", "csv"])
        assert r.exit_code == 0
        out = pd.read_csv(dest)
        assert len(out) == len(sample_df)

    def test_no_args_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_write(runner, csv_in, [])
        assert r.exit_code != 0
