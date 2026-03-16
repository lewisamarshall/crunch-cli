"""Property-based tests using Hypothesis.

Tests focus on invariants of the pure transform functions,
not specific values.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames, range_indexes

from crunch.commands.filter import _apply_filter
from crunch.commands.melt import _apply_melt
from crunch.commands.sort import _apply_sort
from crunch.commands.transform import _apply_transform

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

numeric_df = data_frames(
    columns=[
        column("x", elements=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)),
        column("y", elements=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)),
        column("z", elements=st.integers(min_value=0, max_value=100)),
    ],
    index=range_indexes(min_size=1, max_size=50),
)

text_df = data_frames(
    columns=[
        column("a", elements=st.text(min_size=1, max_size=10)),
        column("b", elements=st.integers(min_value=0, max_value=1000)),
    ],
    index=range_indexes(min_size=1, max_size=50),
)


# ---------------------------------------------------------------------------
# filter invariants
# ---------------------------------------------------------------------------

@given(df=numeric_df, threshold=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False))
@settings(max_examples=100)
def test_filter_never_increases_rows(df, threshold):
    """Filtering never returns more rows than the input."""
    result = _apply_filter(df, column="x", op="gt", value=str(threshold), query=None, case_sensitive=True)
    assert len(result) <= len(df)


@given(df=numeric_df, threshold=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False))
@settings(max_examples=100)
def test_filter_gt_complement_covers_input(df, threshold):
    """gt filter + le filter row counts sum to full DataFrame."""
    gt = _apply_filter(df, column="x", op="gt", value=str(threshold), query=None, case_sensitive=True)
    le = _apply_filter(df, column="x", op="le", value=str(threshold), query=None, case_sensitive=True)
    assert len(gt) + len(le) == len(df)


@given(df=numeric_df)
@settings(max_examples=50)
def test_filter_notnull_plus_isnull_equals_total(df):
    """notnull + isnull row counts equal input length for any column."""
    notnull = _apply_filter(df, column="x", op="notnull", value=None, query=None, case_sensitive=True)
    isnull = _apply_filter(df, column="x", op="isnull", value=None, query=None, case_sensitive=True)
    assert len(notnull) + len(isnull) == len(df)


# ---------------------------------------------------------------------------
# sort invariants
# ---------------------------------------------------------------------------

@given(df=numeric_df)
@settings(max_examples=100)
def test_sort_preserves_columns(df):
    """Sort never adds or removes columns."""
    result = _apply_sort(df, by=["x"], desc=False, na_position="last")
    assert set(result.columns) == set(df.columns)


@given(df=numeric_df)
@settings(max_examples=100)
def test_sort_preserves_row_count(df):
    """Sort never changes the number of rows."""
    result = _apply_sort(df, by=["x"], desc=False, na_position="last")
    assert len(result) == len(df)


@given(df=numeric_df)
@settings(max_examples=100)
def test_sort_ascending_is_monotone(df):
    """After ascending sort on x, non-NaN values are non-decreasing."""
    result = _apply_sort(df, by=["x"], desc=False, na_position="last")
    vals = result["x"].dropna().tolist()
    assert vals == sorted(vals)


@given(df=numeric_df)
@settings(max_examples=100)
def test_sort_descending_is_monotone(df):
    """After descending sort on x, non-NaN values are non-increasing."""
    result = _apply_sort(df, by=["x"], desc=True, na_position="last")
    vals = result["x"].dropna().tolist()
    assert vals == sorted(vals, reverse=True)


# ---------------------------------------------------------------------------
# transform invariants
# ---------------------------------------------------------------------------

@given(df=numeric_df)
@settings(max_examples=100)
def test_transform_preserves_row_count(df):
    """Transform never changes the number of rows."""
    result = _apply_transform(df, column="x", expr="col * 2", output_col=None, keep_original=False)
    assert len(result) == len(df)


@given(df=numeric_df)
@settings(max_examples=100)
def test_transform_output_col_added(df):
    """When --output-col is given, the new column exists in the result."""
    result = _apply_transform(df, column="x", expr="col + 1", output_col="x_plus_1", keep_original=False)
    assert "x_plus_1" in result.columns


@given(df=numeric_df)
@settings(max_examples=100)
def test_transform_keep_original_retains_source(df):
    """With keep_original=True, both source and new column are present."""
    result = _apply_transform(df, column="x", expr="col + 1", output_col="x_plus_1", keep_original=True)
    assert "x" in result.columns
    assert "x_plus_1" in result.columns


# ---------------------------------------------------------------------------
# melt invariants
# ---------------------------------------------------------------------------

@given(df=numeric_df)
@settings(max_examples=100)
def test_melt_row_count(df):
    """Melt with 1 id_var and 2 value_vars produces 2x rows."""
    result = _apply_melt(df, id_vars=["z"], value_vars=["x", "y"], var_name="var", value_name="val")
    assert len(result) == len(df) * 2


@given(df=numeric_df)
@settings(max_examples=100)
def test_melt_id_vars_preserved(df):
    """id_vars appear as columns in the melted output."""
    result = _apply_melt(df, id_vars=["z"], value_vars=["x", "y"], var_name="var", value_name="val")
    assert "z" in result.columns


@given(df=text_df)
@settings(max_examples=100)
def test_melt_var_name_column_contains_only_value_var_names(df):
    """The variable column only contains the names of the value_vars."""
    result = _apply_melt(df, id_vars=["a"], value_vars=["b"], var_name="metric", value_name="val")
    assert set(result["metric"].unique()) == {"b"}
