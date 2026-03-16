"""Tests for crunch melt command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.main import app
from tests.conftest import df_from_stdout


def invoke_melt(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["melt"] + args, input=csv_in)


class TestMelt:
    def test_basic_melt(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_melt(runner, csv_in, [
            "--id-vars", "name", "--id-vars", "category",
            "--value-vars", "age", "--value-vars", "score"
        ])
        assert r.exit_code == 0, r.stderr
        out = df_from_stdout(r.stdout)
        assert "variable" in out.columns
        assert "value" in out.columns
        assert "name" in out.columns
        assert "category" in out.columns

    def test_row_count(self, runner, sample_df):
        n_id = 2  # name, category
        n_val = 2  # age, score
        csv_in = sample_df.to_csv(index=False)
        r = invoke_melt(runner, csv_in, [
            "--id-vars", "name", "--id-vars", "category",
            "--value-vars", "age", "--value-vars", "score"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert len(out) == len(sample_df) * n_val

    def test_custom_var_and_value_names(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_melt(runner, csv_in, [
            "--id-vars", "name",
            "--value-vars", "age",
            "--var-name", "metric",
            "--value-name", "measurement",
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "metric" in out.columns
        assert "measurement" in out.columns

    def test_no_id_vars_melts_all(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_melt(runner, csv_in, [])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "variable" in out.columns
        assert len(out) == len(sample_df) * len(sample_df.columns)

    def test_unknown_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_melt(runner, csv_in, ["--id-vars", "nonexistent"])
        assert r.exit_code != 0
