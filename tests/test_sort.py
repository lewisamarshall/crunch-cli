"""Tests for crunch sort command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.main import app
from tests.conftest import df_from_stdout


def invoke_sort(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["sort"] + args, input=csv_in)


class TestSort:
    def test_single_column_ascending(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "age"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        ages = out["age"].tolist()
        assert ages == sorted(ages)

    def test_single_column_descending(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "age", "--desc"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        ages = out["age"].dropna().tolist()
        assert ages == sorted(ages, reverse=True)

    def test_multi_column_sort(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "category", "--by", "age"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        # Within each category, ages should be sorted ascending
        for cat in out["category"].unique():
            ages = out[out["category"] == cat]["age"].tolist()
            assert ages == sorted(ages)

    def test_na_position_first(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "score", "--na-position", "first"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        # First row should be NaN
        assert out["score"].isna().iloc[0]

    def test_na_position_last(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "score", "--na-position", "last"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        # Last row should be NaN
        assert out["score"].isna().iloc[-1]

    def test_output_has_same_columns(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "name"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert list(out.columns) == list(sample_df.columns)

    def test_missing_by_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, [])
        assert r.exit_code != 0

    def test_unknown_column_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_sort(runner, csv_in, ["--by", "nonexistent"])
        assert r.exit_code != 0
