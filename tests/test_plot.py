"""Tests for crunch plot command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from crunch.__main__ import app


def invoke_plot(runner: CliRunner, csv_in: str, args: list[str]):
    return runner.invoke(app, ["plot"] + args, input=csv_in)


class TestPlotValidation:
    def test_unknown_type_raises(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "donut"])
        assert r.exit_code != 0

    def test_scatter_requires_x_and_y(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "scatter", "--x", "age"])
        assert r.exit_code != 0

    def test_hist_requires_x(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "hist"])
        assert r.exit_code != 0

    def test_pair_requires_two_numeric_columns(self, runner, sample_df):
        # Passing only one column should fail
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "pair", "--columns", "age"])
        assert r.exit_code != 0


class TestPlotOutput:
    def test_scatter_json_to_stdout(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "scatter", "--x", "age", "--y", "score"])
        assert r.exit_code == 0
        spec = json.loads(r.stdout)
        assert "$schema" in spec

    def test_hist_json_to_stdout(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "hist", "--x", "age"])
        assert r.exit_code == 0
        spec = json.loads(r.stdout)
        assert "$schema" in spec

    def test_bar_json_to_stdout(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "bar", "--x", "category", "--y", "age"])
        assert r.exit_code == 0
        spec = json.loads(r.stdout)
        assert "$schema" in spec

    def test_scatter_with_color(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "scatter", "--x", "age", "--y", "score", "--color", "category"])
        assert r.exit_code == 0
        spec = json.loads(r.stdout)
        assert "encoding" in spec

    def test_lm_chart_to_stdout(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "lm", "--x", "age", "--y", "score"])
        assert r.exit_code == 0
        spec = json.loads(r.stdout)
        assert "$schema" in spec

    def test_pair_json_to_stdout(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "pair"])
        assert r.exit_code == 0

    def test_saves_html_file(self, runner, sample_df, tmp_path):
        dest = tmp_path / "chart.html"
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "scatter", "--x", "age", "--y", "score", "-o", str(dest)])
        assert r.exit_code == 0
        assert dest.exists()
        assert "<html" in dest.read_text().lower()

    def test_title_appears_in_spec(self, runner, sample_df):
        csv_in = sample_df.to_csv(index=False)
        r = invoke_plot(runner, csv_in, ["--type", "scatter", "--x", "age", "--y", "score", "--title", "My Chart"])
        assert r.exit_code == 0
        assert "My Chart" in r.stdout
