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
# Everything:
pip install "crunch-cli[all]"
```

## Commands

| Command | Description |
|---------|-------------|
| `filter` | Filter rows by column condition or pandas query expression |
| `sort` | Sort rows by one or more columns |
| `transform` | Apply a Python expression to a column |
| `regression` | Fit a linear regression; append predictions or output summary stats |
| `pivot` | Pivot table aggregation |
| `melt` | Unpivot (melt) from wide to long format |
| `plot` | Plot data with Altair (scatter, line, bar, hist, heatmap, pair, lm) |

## I/O

- **Input**: `-i/--input` — file path (`.csv`, `.tsv`, `.xlsx`, `.xls`) or `-` for stdin (default)
- **Output**: `-o/--output` — file path or `-` for stdout (default)
- **Format**: `-f/--output-format` — `csv` (default), `tsv`, `xlsx`, `json`, `parquet`, `md`
  Format is inferred from the output file extension when not specified.

## Piping

All commands default to reading from stdin and writing CSV to stdout, so you can chain them with `|`:

```bash
# Filter → sort → save as Excel
crunch filter -i sales.csv --column region --op eq --value "West" \
  | crunch sort --by revenue --desc \
  -o top_west.xlsx

# Use pandas query syntax
crunch filter -i data.csv --query "age > 30 and score < 80" | crunch sort --by name

# Melt then filter
crunch melt -i wide.csv --id-vars id name --value-vars q1 q2 q3 \
  | crunch filter --column value --op gt --value 0
```

## Plot examples

```bash
# Scatter plot to HTML (interactive)
crunch plot -i data.csv --type scatter --x age --y salary -o chart.html

# LM plot with regression annotation
crunch plot -i data.csv --type lm --x age --y salary -o lm.png

# Pair plot of selected columns
crunch plot -i data.csv --type pair --columns age salary score -o pairs.html

# Quick ASCII preview in terminal
crunch plot -i data.csv --type scatter --x age --y salary --ascii
```

## Development

```bash
pip install -e ".[plot,parquet]"
pip install pytest pytest-cov hypothesis ruff mypy pandas-stubs
pytest tests/ --cov=src/crunch
```
