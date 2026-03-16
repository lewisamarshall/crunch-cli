"""Tests for crunch lm command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.__main__ import app
from tests.conftest import df_from_stdout


def invoke_lm(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["lm"] + args, input=csv_in)


class TestLmCoefficients:
    def test_basic_formula(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "term" in out.columns
        assert "coef" in out.columns
        assert "p_value" in out.columns
        assert "Intercept" in out["term"].values

    def test_multiple_predictors(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["value ~ age + score"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        terms = out["term"].tolist()
        assert "age" in terms
        assert "score" in terms

    def test_r_squared_present(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "R²" in out["term"].values or "R2" in out["term"].values or any("R" in str(t) for t in out["term"])

    def test_ci_columns_present(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "conf_low" in out.columns
        assert "conf_high" in out.columns


class TestLmAnova:
    def test_anova_flag(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score", "--anova"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "term" in out.columns
        assert "sum_sq" in out.columns

    def test_anova_has_residual_row(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score", "--anova"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert "Residual" in out["term"].values


class TestLmSummary:
    def test_summary_flag(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score", "--summary"])
        assert r.exit_code == 0
        assert "OLS Regression Results" in r.stdout

    def test_anova_and_summary_mutually_exclusive(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["age ~ score", "--anova", "--summary"])
        assert r.exit_code != 0


class TestLmErrors:
    def test_invalid_formula_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, ["nonexistent ~ score"])
        assert r.exit_code != 0

    def test_no_formula_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_lm(runner, csv_in, [])
        assert r.exit_code != 0
