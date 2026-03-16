"""Tests for crunch regression command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.main import app
from tests.conftest import df_from_stdout


def invoke_regression(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["regression"] + args, input=csv_in)


class TestRegressionPredict:
    def test_predict_appends_column(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--y", "value"])
        assert r.exit_code == 0, r.stderr
        out = df_from_stdout(r.stdout)
        assert "predicted_value" in out.columns
        assert len(out) == len(sample_df)

    def test_predict_custom_col_name(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--y", "value", "--pred-col", "yhat"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "yhat" in out.columns

    def test_predict_multiple_x(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--x", "score", "--y", "value"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "predicted_value" in out.columns


class TestRegressionSummary:
    def test_summary_mode_output_schema(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--y", "value", "--mode", "summary"])
        assert r.exit_code == 0, r.stderr
        out = df_from_stdout(r.stdout)
        expected_cols = {"feature", "coefficient", "std_err", "t_stat", "p_value", "r_squared", "rmse"}
        assert expected_cols.issubset(set(out.columns))

    def test_summary_has_intercept_row(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--y", "value", "--mode", "summary"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "intercept" in out["feature"].tolist()

    def test_summary_no_intercept(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, [
            "--x", "age", "--y", "value", "--mode", "summary", "--no-fit-intercept"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "intercept" not in out["feature"].tolist()


class TestRegressionErrors:
    def test_missing_x_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--y", "value"])
        assert r.exit_code != 0

    def test_unknown_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "nonexistent", "--y", "value"])
        assert r.exit_code != 0

    def test_invalid_mode_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_regression(runner, csv_in, ["--x", "age", "--y", "value", "--mode", "badmode"])
        assert r.exit_code != 0
