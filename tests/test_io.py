"""Tests for src/crunch/io.py."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crunch.io import detect_read_format, detect_write_format, read_input, write_output


class TestDetectReadFormat:
    def test_csv(self):
        assert detect_read_format("data.csv") == "csv"

    def test_tsv(self):
        assert detect_read_format("data.tsv") == "tsv"

    def test_txt_as_tsv(self):
        assert detect_read_format("data.txt") == "tsv"

    def test_xlsx(self):
        assert detect_read_format("data.xlsx") == "xlsx"

    def test_xls(self):
        assert detect_read_format("data.xls") == "xls"

    def test_parquet(self):
        assert detect_read_format("data.parquet") == "parquet"

    def test_case_insensitive(self):
        assert detect_read_format("DATA.CSV") == "csv"

    def test_unknown_raises(self):
        import typer
        with pytest.raises(typer.BadParameter):
            detect_read_format("data.foobar")


class TestDetectWriteFormat:
    def test_csv(self):
        assert detect_write_format("out.csv") == "csv"

    def test_xlsx(self):
        assert detect_write_format("out.xlsx") == "xlsx"

    def test_markdown(self):
        assert detect_write_format("out.md") == "md"

    def test_unknown_raises(self):
        import typer
        with pytest.raises(typer.BadParameter):
            detect_write_format("out.foobar")


class TestReadInput:
    def test_reads_csv_file(self, csv_file, sample_df):
        df = read_input(str(csv_file))
        assert list(df.columns) == list(sample_df.columns)
        assert len(df) == len(sample_df)

    def test_reads_excel_file(self, excel_file, sample_df):
        df = read_input(str(excel_file))
        assert list(df.columns) == list(sample_df.columns)
        assert len(df) == len(sample_df)

    def test_missing_file_raises(self):
        import typer
        with pytest.raises(typer.BadParameter, match="not found"):
            read_input("/nonexistent/path/data.csv")

    def test_empty_file_raises(self, tmp_path):
        import typer
        p = tmp_path / "empty.csv"
        p.write_text("")
        with pytest.raises(typer.BadParameter):
            read_input(str(p))


class TestWriteOutput:
    def test_writes_csv_to_file(self, tmp_path, sample_df):
        dest = tmp_path / "out.csv"
        write_output(sample_df, str(dest))
        result = pd.read_csv(dest)
        assert len(result) == len(sample_df)

    def test_writes_xlsx_to_file(self, tmp_path, sample_df):
        dest = tmp_path / "out.xlsx"
        write_output(sample_df, str(dest))
        result = pd.read_excel(dest)
        assert len(result) == len(sample_df)

    def test_writes_json_to_file(self, tmp_path, sample_df):
        dest = tmp_path / "out.json"
        write_output(sample_df, str(dest))
        result = pd.read_json(dest)
        assert len(result) == len(sample_df)

    def test_writes_tsv_to_file(self, tmp_path, sample_df):
        dest = tmp_path / "out.tsv"
        write_output(sample_df, str(dest))
        result = pd.read_csv(dest, sep="\t")
        assert len(result) == len(sample_df)

    def test_writes_markdown_to_file(self, tmp_path, sample_df):
        dest = tmp_path / "out.md"
        write_output(sample_df, str(dest))
        content = dest.read_text()
        assert "|" in content  # markdown table

    def test_explicit_format_overrides_extension(self, tmp_path, sample_df):
        dest = tmp_path / "out.csv"
        write_output(sample_df, str(dest), fmt="tsv")
        result = pd.read_csv(dest, sep="\t")
        assert len(result) == len(sample_df)

    def test_binary_format_to_stdout_raises(self, sample_df):
        import typer
        with pytest.raises(typer.BadParameter, match="binary"):
            write_output(sample_df, "-", fmt="xlsx")

    def test_unknown_format_raises(self, sample_df):
        import typer
        with pytest.raises(typer.BadParameter):
            write_output(sample_df, "-", fmt="foobar")
