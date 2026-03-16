"""Integration tests — multi-command pipe simulations."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from crunch.__main__ import app
from tests.conftest import df_from_stdout


class TestPipelineIntegration:
    def test_filter_then_sort(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)

        r1 = runner.invoke(app, ["filter", "--column", "age", "--op", "gt", "--value", "30"], input=csv_in)
        assert r1.exit_code == 0

        r2 = runner.invoke(app, ["sort", "--by", "name"], input=r1.stdout)
        assert r2.exit_code == 0

        out = df_from_stdout(r2.stdout)
        assert (out["age"] > 30).all()
        names = out["name"].tolist()
        assert names == sorted(names)

    def test_filter_transform_sort(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)

        r1 = runner.invoke(app, ["filter", "--column", "age", "--op", "gt", "--value", "25"], input=csv_in)
        assert r1.exit_code == 0

        r2 = runner.invoke(app, [
            "transform", "--column", "age", "--expr", "col * 2", "--output-col", "double_age", "--keep-original"
        ], input=r1.stdout)
        assert r2.exit_code == 0

        r3 = runner.invoke(app, ["sort", "--by", "age", "--desc"], input=r2.stdout)
        assert r3.exit_code == 0

        out = df_from_stdout(r3.stdout)
        assert "double_age" in out.columns
        assert "age" in out.columns
        ages = out["age"].dropna().tolist()
        assert ages == sorted(ages, reverse=True)

    def test_melt_then_filter(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)

        r1 = runner.invoke(app, [
            "melt",
            "--id-vars", "name", "--id-vars", "category",
            "--value-vars", "age", "--value-vars", "score",
        ], input=csv_in)
        assert r1.exit_code == 0

        r2 = runner.invoke(app, ["filter", "--column", "variable", "--op", "eq", "--value", "age"], input=r1.stdout)
        assert r2.exit_code == 0

        out = df_from_stdout(r2.stdout)
        assert (out["variable"] == "age").all()

    def test_stdin_from_file_to_stdout(self, runner, csv_file):
        r = runner.invoke(app, ["filter", "-i", str(csv_file), "--column", "age", "--op", "gt", "--value", "30"])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert (out["age"] > 30).all()
