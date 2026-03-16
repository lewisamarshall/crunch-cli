"""Tests for crunch load command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from crunch.__main__ import app
from tests.conftest import df_from_stdout


def invoke_load(runner: CliRunner, args: list[str]):
    return runner.invoke(app, ["load"] + args)


class TestLoad:
    def test_loads_csv(self, runner, csv_file, sample_df):
        r = invoke_load(runner, [str(csv_file)])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert list(out.columns) == list(sample_df.columns)
        assert len(out) == len(sample_df)

    def test_loads_excel(self, runner, excel_file, sample_df):
        r = invoke_load(runner, [str(excel_file)])
        assert r.exit_code == 0
        out = df_from_stdout(r.stdout)
        assert list(out.columns) == list(sample_df.columns)

    def test_format_conversion_to_tsv(self, runner, csv_file):
        r = invoke_load(runner, [str(csv_file), "-f", "tsv"])
        assert r.exit_code == 0
        # TSV output is tab-separated
        assert "\t" in r.stdout.splitlines()[0]

    def test_format_conversion_to_json(self, runner, csv_file):
        r = invoke_load(runner, [str(csv_file), "-f", "json"])
        assert r.exit_code == 0
        assert r.stdout.strip().startswith("[")

    def test_missing_file_raises(self, runner):
        r = invoke_load(runner, ["nonexistent.csv"])
        assert r.exit_code != 0

    def test_no_args_raises(self, runner):
        r = invoke_load(runner, [])
        assert r.exit_code != 0
