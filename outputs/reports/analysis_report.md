# AI Usage and Impact on Students and Professionals — Analysis Report

## Executive summary
- Original dataset: **300 rows × 19 columns**.
- Cleaned dataset: **288 rows × 19 columns**.
- Removed **12 exact duplicate rows**; no non-identical records were removed.
- Missing cells after cleaning: **197**. Missing values were retained rather than filled with unsupported assumptions.
- IQR outliers are flagged for review only; they are not automatically deleted.
- Findings describe associations in this observational dataset and do not establish causation.

## Dataset and field interpretation
The CSV contains 19 fields. Meanings below are interpreted from field names; the supplied file does not include a separate data dictionary.
- Identity/context: User_ID, Age, Gender, Country, User_Type, Education_Level, Profession.
- AI adoption: Monthly_Income, AI_Tool, AI_Purpose, AI_Usage_Hours_Per_Day, Tasks_Performed, Monthly_AI_Cost.
- Reported outcomes: Productivity_Score, Accuracy_Rating, Satisfaction_Score, Time_Saved_Hours_Per_Week, Work_or_Study_Hours_Per_Day, Would_Recommend.

## Data quality and preprocessing
- Exact duplicates removed: 12.
- Missing cells before cleaning: 204; after cleaning: 197.
- Numeric strings were parsed after removing display-only currency/unit characters (e.g. `$`, `hrs`). Currency units are not specified in the source, so income/cost values are not labelled with a currency.
- Known spelling/case variants were standardized for Gender, AI_Tool, Education_Level, and Would_Recommend.
- Plausibility validation: Age 13–100; daily hours 0–24; weekly time saved 0–168; Productivity 0–10; Accuracy 1–5; Satisfaction 1–10; monetary fields non-negative.
- Values outside these limits were set to missing, not silently clipped. Review `data_quality_validation.json` for counts.
- Missing values were not imputed. IQR outlier screening is documented in `iqr_outlier_screening.csv`; potential outliers remain in the cleaned data.

## Dataset profile
- User type distribution: {'Student': 151, 'Professional': 137}
- Most common AI tool: ChatGPT
- Most common AI purpose: Coding

## Descriptive statistics
See `outputs/tables/numeric_descriptive_statistics.csv` for count, mean, standard deviation, min/max, quartiles, median, mode and variance.
## Statistical analysis

### Spearman correlations
- AI_Usage_Hours_Per_Day vs Productivity_Score: ρ = 0.799, n = 267, p = 1.43e-60, bootstrap 95% CI [0.751, 0.842].
- Time_Saved_Hours_Per_Week vs Productivity_Score: ρ = 0.747, n = 264, p = 2.33e-48, bootstrap 95% CI [0.688, 0.797].
- Productivity_Score vs Satisfaction_Score: ρ = 0.632, n = 267, p = 3.15e-31, bootstrap 95% CI [0.553, 0.709].
- Accuracy_Rating vs Satisfaction_Score: ρ = 0.517, n = 267, p = 1.27e-19, bootstrap 95% CI [0.426, 0.605].
- AI_Usage_Hours_Per_Day vs Time_Saved_Hours_Per_Week: ρ = 0.824, n = 271, p = 2.95e-68, bootstrap 95% CI [0.772, 0.866].

### Group comparisons (Mann–Whitney U, two-sided)
- Productivity score: Student vs Professional: medians 4.90 (n=143) vs 5.10 (n=131); p=0.5399; rank-biserial effect=0.043.
- Satisfaction score: Student vs Professional: medians 6.00 (n=150) vs 6.00 (n=131); p=0.6796; rank-biserial effect=-0.028.

P-values are not proof of practical importance. Correlation tests are pairwise and do not adjust for confounding or multiple comparisons.
## Visualizations

- `distribution_age.png`
- `distribution_ai_usage_hours_per_day.png`
- `distribution_productivity_score.png`
- `distribution_satisfaction_score.png`
- `distribution_time_saved_hours_per_week.png`
- `distribution_work_or_study_hours_per_day.png`
- `category_user_type.png`
- `category_ai_tool.png`
- `category_ai_purpose.png`
- `category_would_recommend.png`
- `category_gender.png`
- `category_education_level.png`
- `user_type_share_pie.png`
- `ai_usage_vs_productivity.png`
- `time_saved_vs_productivity.png`
- `productivity_by_user_type.png`
- `spearman_correlation_heatmap.png`

## Limitations
- The dataset is a sample of 300 records; representativeness and sampling method are not documented in the supplied CSV.
- The source provides no data dictionary, currency unit, survey wording, collection dates, or sampling design.
- Several variables are self-reported scores/hours; measurement error and response bias are possible.
- Cross-sectional observational data cannot establish that AI use causes productivity, accuracy, satisfaction, or time savings.
- Missingness may bias complete-case statistics; no imputation was performed.
- Profession and task descriptions are high-cardinality free-text fields and are not aggressively grouped.

## Recommendations
- Interpret AI-use and outcome relationships as exploratory; validate them with a larger, representative, longitudinal sample.
- Track consistent outcome definitions and units (especially currency, productivity scale, and time saved) in future data collection.
- Compare students and professionals with attention to group sizes, uncertainty, and potential confounders such as profession and working hours.
- Use the generated charts and tables to identify hypotheses for follow-up rather than making causal claims.

## Reproducibility
Run `python analysis.py` from the project directory after installing `requirements.txt`. The script recreates the cleaned dataset, charts, CSV tables, JSON validation log, and this report.