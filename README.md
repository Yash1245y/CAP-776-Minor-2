# AI Usage and Impact on Students and Professionals

A reproducible, single-file Python data analytics project based on the supplied Kaggle CSV.

## Dataset
- Source: [Kaggle — AI Usage and Impact on Students and Professionals](https://www.kaggle.com/datasets/eishatuzzuhra/ai-usage-and-impact-on-students-and-professionals)
- Included raw file: `data/raw/original_dataset.csv`
- Observed shape at build time: 300 rows × 19 columns.
- The source CSV has no accompanying data dictionary; feature descriptions in the report are interpreted from field names.

## Setup
Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python analysis.py
```

`analysis.py` automatically finds the first CSV/XLSX/XLS file in `data/raw/`. To analyze a replacement dataset, put it there (keep only one input file to avoid ambiguity). The original included CSV is preserved.

## Outputs
- `data/processed/cleaned_dataset.csv` — cleaned data, with missing values preserved.
- `outputs/charts/` — PNG charts.
- `outputs/tables/` — descriptive statistics, category frequencies, missingness, IQR screening, correlations, and tests.
- `outputs/reports/analysis_report.md` — generated narrative report.
- `outputs/reports/data_quality_validation.json` — machine-readable cleaning audit.

## Cleaning policy
- Removes exact duplicate rows only.
- Parses numeric fields that contain display characters such as `$` or `hrs`.
- Standardizes observed variants in selected categorical fields.
- Sets values outside explicitly documented plausibility ranges to missing.
- Does not impute missing values or delete IQR outliers.
- Currency units are not specified by the dataset and are not inferred.

## Statistical methods
- Spearman rank correlations for selected numeric relationships.
- Two-sided Mann–Whitney U tests for student/professional differences in productivity and satisfaction.
- Rank-biserial effect size accompanies group tests.
- Pairwise sample sizes are reported. Tests are exploratory and do not imply causality.

## Reproducibility and caveats
All implementation is in `analysis.py`; no notebooks or auxiliary Python modules are required. Results are regenerated from the raw file at execution time. The dataset's sampling design, survey wording, collection date, currency unit, and formal variable definitions are not included in the supplied CSV. Interpret results accordingly.
