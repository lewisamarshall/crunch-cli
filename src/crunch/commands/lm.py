"""crunch lm — formula-based linear model with statistical output."""

from __future__ import annotations

from typing import Annotated, Optional

import pandas as pd
import typer

from crunch.io import read_input, write_output


def _require_statsmodels() -> None:
    try:
        import statsmodels  # noqa: F401
    except ImportError:
        raise typer.BadParameter(
            "crunch lm requires statsmodels. Install with: pip install statsmodels"
        )


def _fit(df: pd.DataFrame, formula: str) -> "statsmodels.regression.linear_model.RegressionResultsWrapper":  # type: ignore[name-defined]
    import statsmodels.formula.api as smf

    try:
        return smf.ols(formula, data=df).fit()
    except Exception as e:
        raise typer.BadParameter(f"Model failed: {e}")


def _coef_table(result: object) -> pd.DataFrame:
    import numpy as np

    r = result  # type: ignore[assignment]
    rows = []
    for term in r.params.index:
        rows.append(
            {
                "term": term,
                "coef": round(float(r.params[term]), 6),
                "std_err": round(float(r.bse[term]), 6),
                "t": round(float(r.tvalues[term]), 4),
                "p_value": round(float(r.pvalues[term]), 6),
                "conf_low": round(float(r.conf_int().loc[term, 0]), 6),
                "conf_high": round(float(r.conf_int().loc[term, 1]), 6),
            }
        )
    meta = pd.DataFrame(
        [{"term": "---", "coef": float("nan"), "std_err": float("nan"),
          "t": float("nan"), "p_value": float("nan"),
          "conf_low": float("nan"), "conf_high": float("nan")}]
    )
    summary_rows = pd.DataFrame(
        [
            {"term": "R²", "coef": round(float(r.rsquared), 6), "std_err": float("nan"),
             "t": float("nan"), "p_value": float("nan"),
             "conf_low": float("nan"), "conf_high": float("nan")},
            {"term": "R²_adj", "coef": round(float(r.rsquared_adj), 6), "std_err": float("nan"),
             "t": float("nan"), "p_value": float("nan"),
             "conf_low": float("nan"), "conf_high": float("nan")},
            {"term": "F_stat", "coef": round(float(r.fvalue), 4), "std_err": float("nan"),
             "t": float("nan"), "p_value": round(float(r.f_pvalue), 6),
             "conf_low": float("nan"), "conf_high": float("nan")},
            {"term": "n_obs", "coef": float(r.nobs), "std_err": float("nan"),
             "t": float("nan"), "p_value": float("nan"),
             "conf_low": float("nan"), "conf_high": float("nan")},
        ]
    )
    import numpy as np
    return pd.concat([pd.DataFrame(rows), meta, summary_rows], ignore_index=True)


def _anova_table(result: object) -> pd.DataFrame:
    from statsmodels.stats.anova import anova_lm

    try:
        tbl = anova_lm(result, typ=2)  # type: ignore[arg-type]
    except Exception as e:
        raise typer.BadParameter(f"ANOVA failed: {e}")
    return tbl.reset_index().rename(columns={"index": "term"})


def main(
    formula: Annotated[str, typer.Argument(help='R-style formula, e.g. "y ~ x1 + x2"')],
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, md"),
    ] = None,
    anova: Annotated[
        bool,
        typer.Option("--anova", help="Output a Type II ANOVA table instead of the coefficients table"),
    ] = False,
    summary: Annotated[
        bool,
        typer.Option("--summary", help="Print the full statsmodels summary to stdout (not pipeable)"),
    ] = False,
) -> None:
    """Fit an OLS linear model from an R-style formula and output statistics.

    \b
    Output (default): coefficients table with std errors, t-stats, p-values, CIs, R², F.
    Output (--anova): Type II ANOVA table (sum of squares, F, p-values per term).
    Output (--summary): full statsmodels text summary.

    \b
    Examples:
      crunch lm "body_mass_g ~ flipper_length_mm + species" -i data/penguins.csv
      crunch lm "lifeExp ~ gdpPercap + pop" -i data/gapminder.tsv --anova
      crunch load data/penguins.csv | crunch lm "body_mass_g ~ bill_length_mm + bill_depth_mm" --summary
    """
    if anova and summary:
        raise typer.BadParameter("--anova and --summary are mutually exclusive.")

    _require_statsmodels()

    df = read_input(input)
    result = _fit(df, formula)

    if summary:
        typer.echo(str(result.summary()))
        return

    if anova:
        table = _anova_table(result)
    else:
        table = _coef_table(result)

    write_output(table, output, output_format)
