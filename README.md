# crunch

A pipe-friendly CLI tool for tabular data transformations.

```bash
crunch filter -i data.csv --column age --op gt --value 30 \
  | crunch sort --by name \
  | crunch transform --column salary --expr "col * 1.1" --output-col salary_adj \
  -o result.csv
```

## Install

```bash
pip install crunch-cli
# With plotting support:
pip install "crunch-cli[plot]"
# With formula-based regression (lm command):
pip install "crunch-cli[lm]"
# Everything:
pip install "crunch-cli[all]"
```

## Commands

| Command | Description |
|---------|-------------|
| `load` | Read a file and stream it to stdout (pipeline entry point) |
| `write` | Write stdin to a file, converting format as needed (pipeline exit point) |
| `filter` | Filter rows by column condition or pandas query expression |
| `sort` | Sort rows by one or more columns |
| `transform` | Apply a Python expression to a column |
| `pivot` | Pivot table aggregation |
| `melt` | Unpivot (melt) from wide to long format |
| `lm` | Formula-based OLS (`"y ~ x1 + x2"`); outputs coefficients, ANOVA, or full summary |
| `regression` | Fit a linear regression; append predictions or output summary stats |
| `plot` | Plot data with Altair (scatter, line, bar, hist, heatmap, pair, lm) |

## I/O

- **Input**: `-i/--input` — file path (`.csv`, `.tsv`, `.xlsx`, `.xls`, `.parquet`) or `-` for stdin (default)
  - Note: binary formats (`.xlsx`, `.xls`) cannot be read from stdin — use `crunch load` instead
- **Output**: `-o/--output` — file path or `-` for stdout (default)
- **Format**: `-f/--output-format` — `csv` (default), `tsv`, `xlsx`, `json`, `parquet`, `md`
  Format is inferred from the output file extension when not specified.
  - Note: binary formats (`xlsx`, `parquet`) cannot be written to stdout

## Piping

All commands default to reading from stdin and writing CSV to stdout, so you can chain them with `|`. Use `load` to start a pipeline from a file and `write` to save the result:

```bash
# load → filter → sort → write
crunch load sales.csv \
  | crunch filter --column region --op eq --value "West" \
  | crunch sort --by revenue --desc \
  | crunch write top_west.xlsx

# Use pandas query syntax
crunch load data.csv | crunch filter --query "age > 30 and score < 80" | crunch sort --by name

# Melt then filter
crunch load wide.csv | crunch melt --id-vars id name --value-vars q1 q2 q3 \
  | crunch filter --column value --op gt --value 0
```

## Statistical modelling

```bash
# OLS with R-style formula — outputs coefficient table with CIs, R², F-stat
crunch load data/penguins.csv | crunch lm "body_mass_g ~ flipper_length_mm + bill_length_mm"

# Type II ANOVA table
crunch load data/penguins.csv | crunch lm "body_mass_g ~ flipper_length_mm + C(species)" --anova

# Full statsmodels summary
crunch load data/penguins.csv | crunch lm "body_mass_g ~ flipper_length_mm" --summary
```

## Plot examples

```bash
# Scatter plot to HTML (interactive)
crunch load data.csv | crunch plot --type scatter --x age --y salary -o chart.html

# LM plot with regression annotation
crunch load data.csv | crunch plot --type lm --x age --y salary -o lm.png

# Pair plot of selected columns
crunch load data.csv | crunch plot --type pair --columns age salary score -o pairs.html

# Quick ASCII preview in terminal
crunch load data.csv | crunch plot --type scatter --x age --y salary --ascii
```

## Development

```bash
pip install -e ".[plot,parquet,lm]"
pip install pytest pytest-cov hypothesis
pytest tests/ --cov=src/crunch
```
