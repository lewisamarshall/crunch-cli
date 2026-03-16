"""Tests for crunch filter command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.main import app
from tests.conftest import df_from_stdout


def invoke_filter(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["filter"] + args, input=csv_in)


class TestFilterColumnOp:
    def test_gt_numeric(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "age", "--op", "gt", "--value", "30"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["age"] > 30).all()
        assert len(out) < len(sample_df)

    def test_lt_numeric(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "age", "--op", "lt", "--value", "30"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["age"] < 30).all()

    def test_eq_string(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "category", "--op", "eq", "--value", "A"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["category"] == "A").all()

    def test_ne(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "category", "--op", "ne", "--value", "A"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["category"] != "A").all()

    def test_ge(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "age", "--op", "ge", "--value", "32"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["age"] >= 32).all()

    def test_le(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "age", "--op", "le", "--value", "30"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["age"] <= 30).all()

    def test_contains(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "name", "--op", "contains", "--value", "li"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["name"].str.contains("li").all()

    def test_contains_case_insensitive(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, [
            "--column", "name", "--op", "contains", "--value", "ALICE", "--no-case-sensitive"
        ])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert len(out) > 0

    def test_startswith(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "name", "--op", "startswith", "--value", "A"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["name"].str.startswith("A").all()

    def test_endswith(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "name", "--op", "endswith", "--value", "e"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["name"].str.endswith("e").all()

    def test_isnull(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "score", "--op", "isnull"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["score"].isna().all()
        assert len(out) == 1  # one NaN row in fixture

    def test_notnull(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "score", "--op", "notnull"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert out["score"].notna().all()


class TestFilterQuery:
    def test_query_mode(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--query", "age > 30 and age < 40"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert ((out["age"] > 30) & (out["age"] < 40)).all()

    def test_query_mutually_exclusive_with_column(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--query", "age > 30", "--column", "age"])
        assert r.exit_code != 0


class TestFilterErrors:
    def test_missing_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "nonexistent", "--op", "eq", "--value", "x"])
        assert r.exit_code != 0

    def test_no_args_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, [])
        assert r.exit_code != 0

    def test_empty_result_returns_header_only(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_filter(runner, csv_in, ["--column", "age", "--op", "gt", "--value", "999"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert len(out) == 0
        assert list(out.columns) == list(sample_df.columns)
