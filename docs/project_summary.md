# Project Summary

## Objective
Explore reported AI adoption and its perceived relationship with productivity, accuracy, satisfaction, and time savings among students and professionals.

## Dataset snapshot
The included source file contains 300 rows and 19 columns. The exact data profile and all computed findings are generated in `outputs/reports/analysis_report.md` and `outputs/tables/`.

## Pipeline
1. Load and profile the original CSV.
2. Remove exact duplicate rows only.
3. Normalize observed category variants and parse numeric strings.
4. Validate ranges without fabricating values; retain missingness.
5. Produce descriptive and frequency tables.
6. Screen numeric fields for IQR outliers without deleting them.
7. Calculate selected Spearman correlations and group comparisons.
8. Generate labeled charts, a machine-readable quality audit, and a narrative report.

## Interpretation
The analysis is exploratory. The data are observational and the sampling design and data dictionary were not supplied. Correlation must not be interpreted as causation, and currency units are unknown.

## Run
Install `requirements.txt`, then execute `python analysis.py`.
