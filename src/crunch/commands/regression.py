"""crunch regression — fit a linear regression model."""

from __future__ import annotations

from typing import Annotated, Optional

import numpy as np
import pandas as pd
import typer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from crunch.io import read_input, write_output


def _apply_regression(
    df: pd.DataFrame,
    *,
    x_cols: list[str],
    y_col: str,
    mode: str,
    pred_col: str,
    test_size: float,
    random_state: int,
    fit_intercept: bool,
) -> pd.DataFrame:
    missing = [c for c in x_cols + [y_col] if c not in df.columns]
    if missing:
        raise typer.BadParameter(
            f"Column(s) not found: {missing}. Available: {list(df.columns)}"
        )

    # Drop rows with NaN in any feature or target column
    working = df[x_cols + [y_col]].dropna()
    if working.empty:
        raise typer.BadParameter("No rows remain after dropping NaN values in the selected columns.")

    X = working[x_cols].values
    y = working[y_col].values

    if test_size > 0.0:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = LinearRegression(fit_intercept=fit_intercept)
    model.fit(X_train, y_train)
    y_pred_test = model.predict(X_test)

    r2 = r2_score(y_test, y_pred_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))

    if mode == "predict":
        y_pred_all = model.predict(X)
        result = df.copy()
        # Re-align predictions to original index (NaN rows get NaN prediction)
        pred_series = pd.Series(index=working.index, data=y_pred_all, name=pred_col)
        result[pred_col] = pred_series
        return result

    # summary mode — compute basic stats via numpy
    coefs = list(model.coef_)
    features = list(x_cols)

    if fit_intercept:
        coefs = [model.intercept_] + coefs
        features = ["intercept"] + features

    # Compute std errors via OLS normal equations
    X_aug = np.hstack([np.ones((X_train.shape[0], 1)), X_train]) if fit_intercept else X_train
    n, p = X_aug.shape
    y_pred_train = model.predict(X_train)
    residuals = y_train - y_pred_train
    mse_resid = np.sum(residuals**2) / max(n - p, 1)
    try:
        XtX_inv = np.linalg.inv(X_aug.T @ X_aug)
        se = np.sqrt(np.diag(XtX_inv) * mse_resid)
    except np.linalg.LinAlgError:
        se = np.full(p, float("nan"))

    t_stats = np.array(coefs) / np.where(se == 0, float("nan"), se)

    from scipy import stats as scipy_stats  # lazy import — only needed for summary
    p_values = [
        float(2 * scipy_stats.t.sf(abs(t), df=max(n - p, 1))) if not np.isnan(t) else float("nan")
        for t in t_stats
    ]

    rows = []
    for feat, coef, stderr, t_stat, pval in zip(features, coefs, se, t_stats, p_values):
        rows.append(
            {
                "feature": feat,
                "coefficient": round(float(coef), 6),
                "std_err": round(float(stderr), 6),
                "t_stat": round(float(t_stat), 4),
                "p_value": round(pval, 6),
                "r_squared": round(r2, 6),
                "rmse": round(rmse, 6),
            }
        )
    return pd.DataFrame(rows)


def main(
    input: Annotated[str, typer.Option("--input", "-i", help="Input file or - for stdin")] = "-",
    output: Annotated[str, typer.Option("--output", "-o", help="Output file or - for stdout")] = "-",
    output_format: Annotated[
        Optional[str],
        typer.Option("--output-format", "-f", help="Output format: csv, tsv, xlsx, json, parquet, md"),
    ] = None,
    x: Annotated[
        Optional[list[str]],
        typer.Option("--x", help="Feature column(s). Repeatable."),
    ] = None,
    y: Annotated[
        str, typer.Option("--y", help="Target column")
    ] = ...,  # type: ignore[assignment]
    mode: Annotated[
        str,
        typer.Option("--mode", "-m", help="predict: append predictions column. summary: output stats CSV."),
    ] = "predict",
    pred_col: Annotated[
        Optional[str],
        typer.Option("--pred-col", help="Name for the prediction column (predict mode). Default: predicted_<y>."),
    ] = None,
    test_size: Annotated[
        float,
        typer.Option("--test-size", help="Fraction of data held out as test set (0.0 = use all data)."),
    ] = 0.0,
    random_state: Annotated[
        int,
        typer.Option("--random-state", help="Random seed for train/test split."),
    ] = 42,
    fit_intercept: Annotated[
        bool,
        typer.Option("--fit-intercept/--no-fit-intercept", help="Whether to fit an intercept term."),
    ] = True,
) -> None:
    """Fit a linear regression model on the input data.

    \b
    Modes:
      predict  — appends a column of predicted values to the rows (default)
      summary  — outputs a CSV with coefficients, std errors, t-stats, p-values, R², RMSE

    \b
    Examples:
      crunch regression -i data.csv --x age --x experience --y salary
      crunch regression -i data.csv --x age --y salary --mode summary
      crunch regression -i data.csv --x age --y salary --test-size 0.2
    """
    if not x:
        raise typer.BadParameter("At least one --x column is required.")
    if mode not in ("predict", "summary"):
        raise typer.BadParameter("--mode must be 'predict' or 'summary'.")
    if not 0.0 <= test_size < 1.0:
        raise typer.BadParameter("--test-size must be between 0.0 and 1.0 (exclusive).")

    resolved_pred_col = pred_col or f"predicted_{y}"

    df = read_input(input)
    result = _apply_regression(
        df,
        x_cols=x,
        y_col=y,
        mode=mode,
        pred_col=resolved_pred_col,
        test_size=test_size,
        random_state=random_state,
        fit_intercept=fit_intercept,
    )
    write_output(result, output, output_format)
