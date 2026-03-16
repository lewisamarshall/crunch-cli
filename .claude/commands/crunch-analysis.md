Analyse the data file or question provided using the crunch CLI. Follow these steps:

1. **Inspect** the data first with `head` or by reading the file to understand columns and types.
2. **Plan** a pipeline using the appropriate crunch commands:
   - `crunch filter` — row filtering with `--column/--op/--value` or `--query "expr"`
   - `crunch sort` — sort by one or more columns with `--by col --desc`
   - `crunch transform` — derive new columns with `--column new_col --expr "expression"`
   - `crunch pivot` — aggregate: requires `--index`, `--columns`, and optionally `--values` and `--aggfunc`
   - `crunch melt` — reshape wide→long with `--id-vars` and `--value-vars`
   - `crunch regression` — OLS regression with `--target` and `--features`
   - `crunch plot` — visualise with `--type scatter|line|bar|hist|heatmap|pair|lm`, `--x`, `--y`, `--color`, `-o file.html`
3. **Run** the pipeline using Bash, piping commands together with `|`.
4. **Interpret** the output and summarise findings for the user.

## Key syntax reminders

- Input defaults to stdin (`-i -`), output to stdout (`-o -`) — commands are pipeable
- `filter` needs `--op` explicitly: `--column year --op eq --value 2007` (not `--eq`)
- `pivot` requires both `--index` and `--columns`; with a single `--values` column, the flattened header is just the column value (e.g. `2007`), not `values_2007`
- `plot` saves to file via `-o chart.html` (supports .html, .png, .svg, .pdf, .json); use `--ascii` for terminal output
- Sample datasets are in `data/penguins.csv` and `data/gapminder.tsv`

## Example pipelines

```bash
# Filter then sort
crunch filter -i data/penguins.csv --query "body_mass_g > 4000" | crunch sort --by bill_length_mm --desc

# Grouped mean via pivot (filter to one value first so column header is clean)
crunch filter -i data/gapminder.tsv --query "year == 2007" | crunch pivot --index continent --columns year --values lifeExp --aggfunc mean

# Scatter plot coloured by category
crunch plot -i data/penguins.csv --type scatter --x bill_length_mm --y body_mass_g --color species -o scatter.html

# Regression with stats annotation
crunch plot -i data/penguins.csv --type lm --x flipper_length_mm --y body_mass_g -o lm.html

# Full pipeline: filter → pivot → plot
crunch filter -i data/gapminder.tsv --query "year == 2007" | crunch pivot --index continent --columns year --values lifeExp --aggfunc mean | crunch plot --type bar --x continent --y 2007 --title "Life Expectancy 2007" -o lifeexp.html
```
