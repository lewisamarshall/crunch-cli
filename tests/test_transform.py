"""Tests for crunch transform command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.main import app
from tests.conftest import df_from_stdout


def invoke_transform(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["transform"] + args, input=csv_in)


class TestTransform:
    def test_numeric_expression_overwrites(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, ["--column", "age", "--expr", "col * 2"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        # Original ages times 2
        orig_ages = sample_df["age"].tolist()
        new_ages = out["age"].tolist()
        assert all(abs(n - o * 2) < 1e-6 for n, o in zip(new_ages, orig_ages))

    def test_output_col_creates_new_column(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, [
            "--column", "age", "--expr", "col * 2", "--output-col", "double_age"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "double_age" in out.columns
        assert "age" not in out.columns  # source dropped by default

    def test_keep_original_preserves_source(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, [
            "--column", "age", "--expr", "col * 2", "--output-col", "double_age", "--keep-original"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "age" in out.columns
        assert "double_age" in out.columns

    def test_string_expression(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, ["--column", "name", "--expr", "col.str.upper()"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["name"].str.isupper().all()

    def test_numpy_available(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, [
            "--column", "value", "--expr", "np.abs(col)", "--output-col", "abs_value"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["abs_value"].dropna() >= 0).all()

    def test_output_same_row_count(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, ["--column", "age", "--expr", "col + 1"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert len(out) == len(sample_df)

    def test_invalid_expression_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, ["--column", "age", "--expr", "col ??? invalid"])
        assert r.exit_code != 0

    def test_missing_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_transform(runner, csv_in, ["--column", "nonexistent", "--expr", "col * 2"])
        assert r.exit_code != 0
