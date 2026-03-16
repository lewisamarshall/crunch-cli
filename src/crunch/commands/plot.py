"""crunch plot — visualize tabular data with Altair or plotext."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input

_CHART_TYPES = {"scatter", "line", "bar", "hist", "heatmap", "pair", "lm"}


def _require_altair() -> None:
    try:
        import altair  # noqa: F401
        import vl_convert  # noqa: F401
    except ImportError:
        raise typer.BadParameter(
            "Plotting requires altair and vl-convert-python. "
            "Install with: pip install 'crunch-cli[plot]'"
        )


def _build_altair_chart(
    df: pd.DataFrame,
    *,
    chart_type: str,
    x: Optional[str],
    y: Optional[str],
    color: Optional[str],
    columns: Optional[list[str]],
    title: str,
    width: int,
    height: int,
) -> "altair.TopLevelSpec":  # type: ignore[name-defined]
    import altair as alt

    color_enc = alt.Color(color) if color else alt.Undefined
    props = dict(title=title, width=width, height=height)

    if chart_type == "scatter":
        _need_xy(x, y, chart_type)
        return (
            alt.Chart(df, **props)
            .mark_point()
            .encode(x=alt.X(x), y=alt.Y(y), color=color_enc)
        )

    if chart_type == "line":
        _need_xy(x, y, chart_type)
        return (
            alt.Chart(df, **props)
            .mark_line()
            .encode(x=alt.X(x), y=alt.Y(y), color=color_enc)
        )

    if chart_type == "bar":
        _need_xy(x, y, chart_type)
        return (
            alt.Chart(df, **props)
            .mark_bar()
            .encode(x=alt.X(x), y=alt.Y(y), color=color_enc)
        )

    if chart_type == "hist":
        if x is None:
            raise typer.BadParameter("--x is required for --type hist.")
        return (
            alt.Chart(df, **props)
            .mark_bar()
            .encode(alt.X(x, bin=True), y="count()")
        )

    if chart_type == "heatmap":
        _need_xy(x, y, chart_type)
        z = color or "count()"
        return (
            alt.Chart(df, **props)
            .mark_rect()
            .encode(
                x=alt.X(x),
                y=alt.Y(y),
                color=alt.Color(z, scale=alt.Scale(scheme="viridis")),
            )
        )

    if chart_type == "pair":
        numeric_cols = columns or list(df.select_dtypes("number").columns)
        if len(numeric_cols) < 2:
            raise typer.BadParameter("pair plot requires at least 2 numeric columns.")
        chart = (
            alt.Chart(df)
            .mark_point()
            .encode(
                x=alt.X(alt.repeat("column"), type="quantitative"),
                y=alt.Y(alt.repeat("row"), type="quantitative"),
                color=color_enc,
            )
            .properties(width=width // len(numeric_cols), height=height // len(numeric_cols))
            .repeat(row=numeric_cols, column=numeric_cols)
        )
        return chart

    if chart_type == "lm":
        _need_xy(x, y, chart_type)
        return _build_lm_chart(df, x=x, y=y, color=color_enc, title=title, width=width, height=height)

    raise typer.BadParameter(f"Unknown chart type '{chart_type}'.")


def _need_xy(x: Optional[str], y: Optional[str], chart_type: str) -> None:
    if x is None or y is None:
        raise typer.BadParameter(f"--x and --y are required for --type {chart_type}.")


def _build_lm_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: object,
    title: str,
    width: int,
    height: int,
) -> "altair.LayerChart":  # type: ignore[name-defined]
    import altair as alt
    from scipy import stats as scipy_stats

    clean = df[[x, y]].dropna()
    slope, intercept, r_value, p_value, _ = scipy_stats.linregress(clean[x], clean[y])
    r2 = r_value**2

    sign = "+" if intercept >= 0 else "-"
    annotation_text = (
        f"y = {slope:.3f}x {sign} {abs(intercept):.3f}\n"
        f"R² = {r2:.3f}   p = {p_value:.4g}"
    )

    x_annot = float(clean[x].quantile(0.05))
    y_annot = float(clean[y].quantile(0.95))

    scatter = (
        alt.Chart(df)
        .mark_point(opacity=0.6)
        .encode(x=alt.X(x, type="quantitative"), y=alt.Y(y, type="quantitative"), color=color)
    )

    regression_line = (
        alt.Chart(df)
        .mark_line(color="red", strokeDash=[5, 5])
        .transform_regression(x, y)
        .encode(x=alt.X(x, type="quantitative"), y=alt.Y(y, type="quantitative"))
    )

    annot_df = pd.DataFrame({"x": [x_annot], "y": [y_annot], "text": [annotation_text]})
    annotation = (
        alt.Chart(annot_df)
        .mark_text(align="left", baseline="top", fontSize=11, color="black")
        .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text=alt.Text("text:N"))
    )

    return (
        alt.layer(scatter, regression_line, annotation)
        .properties(title=title, width=width, height=height)
    )


def _ascii_plot(df: pd.DataFrame, chart_type: str, x: Optional[str], y: Optional[str]) -> None:
    try:
        import plotext as plt
    except ImportError:
        raise typer.BadParameter(
            "ASCII plotting requires plotext. Install with: pip install 'crunch-cli[plot]'"
        )

    if chart_type in ("scatter", "lm"):
        _need_xy(x, y, chart_type)
        plt.scatter(df[x].tolist(), df[y].tolist())  # type: ignore[index]
        plt.xlabel(x)
        plt.ylabel(y)
    elif chart_type == "line":
        _need_xy(x, y, chart_type)
        plt.plot(df[x].tolist(), df[y].tolist())  # type: ignore[index]
        plt.xlabel(x)
        plt.ylabel(y)
    elif chart_type == "bar":
        _need_xy(x, y, chart_type)
        plt.bar(df[x].tolist(), df[y].tolist())  # type: ignore[index]
        plt.xlabel(x)
        plt.ylabel(y)
    elif chart_type == "hist":
        if x is None:
            raise typer.BadParameter("--x is required for --type hist.")
        plt.hist(df[x].dropna().tolist())
        plt.xlabel(x)
    else:
        raise typer.BadParameter(f"--ascii does not support chart type '{chart_type}'. Use scatter, line, bar, or hist.")

    plt.show()


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output file (.html .png .svg .pdf .json) or - for stdout (JSON spec)")
    ] = None,
    chart_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Chart type: scatter line bar hist heatmap pair lm"),
    ] = ...,  # type: ignore[assignment]
    x: Annotated[Optional[str], typer.Option("--x", help="Column for x-axis")] = None,
    y: Annotated[Optional[str], typer.Option("--y", help="Column for y-axis")] = None,
    color: Annotated[Optional[str], typer.Option("--color", help="Column for color encoding")] = None,
    columns: Annotated[
        Optional[list[str]],
        typer.Option("--columns", help="Columns for pair plot (defaults to all numeric). Repeatable."),
    ] = None,
    title: Annotated[str, typer.Option("--title", help="Chart title")] = "",
    width: Annotated[int, typer.Option("--width", help="Chart width in pixels")] = 600,
    height: Annotated[int, typer.Option("--height", help="Chart height in pixels")] = 400,
    ascii_mode: Annotated[
        bool,
        typer.Option("--ascii", help="Render as ASCII chart in the terminal (uses plotext)"),
    ] = False,
) -> None:
    """Plot data using Altair (default) or plotext for terminal ASCII output.

    \b
    Output formats (inferred from file extension):
      .html   — interactive Vega-Lite chart
      .png    — static PNG (requires vl-convert)
      .svg    — static SVG (requires vl-convert)
      .pdf    — static PDF (requires vl-convert)
      .json   — Vega-Lite JSON spec
      -       — stdout: Vega-Lite JSON spec

    \b
    Chart types:
      scatter   Plain scatter plot
      line      Line chart
      bar       Bar chart
      hist      Histogram of a single column
      heatmap   2-D heatmap
      pair      Scatter matrix of numeric columns
      lm        Scatter + OLS regression line with stats annotation

    \b
    Examples:
      crunch plot -i data.csv --type scatter --x age --y salary -o chart.html
      crunch plot -i data.csv --type lm --x age --y salary -o lm.png
      crunch plot -i data.csv --type pair --columns age salary score -o pairs.html
      crunch plot -i data.csv --type scatter --x age --y salary --ascii
    """
    if chart_type not in _CHART_TYPES:
        raise typer.BadParameter(
            f"Unknown chart type '{chart_type}'. Choose from: {', '.join(sorted(_CHART_TYPES))}"
        )

    df = read_input(input)

    if ascii_mode:
        _ascii_plot(df, chart_type, x, y)
        return

    _require_altair()

    chart = _build_altair_chart(
        df,
        chart_type=chart_type,
        x=x,
        y=y,
        color=color,
        columns=columns,
        title=title,
        width=width,
        height=height,
    )

    dest = output or "-"
    if dest == "-":
        import sys
        sys.stdout.write(chart.to_json())
        sys.stdout.write("\n")
    else:
        chart.save(dest)
        typer.echo(f"Chart saved to {dest}", err=True)
