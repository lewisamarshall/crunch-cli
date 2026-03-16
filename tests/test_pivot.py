"""Tests for crunch pivot command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.__main__ import app
from tests.conftest import df_from_stdout


def invoke_pivot(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["pivot"] + args, input=csv_in)


class TestPivot:
    def test_basic_mean(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, [
            "--index", "category", "--columns", "name", "--values", "age", "--aggfunc", "mean"
        ])
        assert r.exit_code == 0, r.stderr
        out = df_from_stdout(r.stdout)
        assert "category" in out.columns

    def test_aggfunc_sum(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, [
            "--index", "category", "--columns", "name", "--values", "age", "--aggfunc", "sum"
        ])
        assert r.exit_code == 0

    def test_aggfunc_count(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, [
            "--index", "category", "--columns", "name", "--values", "age", "--aggfunc", "count"
        ])
        assert r.exit_code == 0

    def test_fill_value(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, [
            "--index", "category", "--columns", "name", "--values", "value",
            "--aggfunc", "mean", "--fill-value", "0"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        # No NaN in data columns
        data_cols = [c for c in out.columns if c != "category"]
        assert not out[data_cols].isna().any().any()

    def test_missing_index_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, ["--columns", "category", "--values", "age"])
        assert r.exit_code != 0

    def test_missing_columns_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, ["--index", "category", "--values", "age"])
        assert r.exit_code != 0

    def test_unknown_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_pivot(runner, csv_in, [
            "--index", "nonexistent", "--columns", "category", "--values", "age"
        ])
        assert r.exit_code != 0
