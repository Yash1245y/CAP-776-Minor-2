#!/usr/bin/env python3
"""
AI Usage and Impact on Students and Professionals — reproducible analytics pipeline.
All implementation is intentionally contained in this single file.
"""
from pathlib import Path
import logging, re, sys, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

BASE = Path(__file__).resolve().parent
RAW_DIR = BASE / "data" / "raw"
PROCESSED_DIR = BASE / "data" / "processed"
CHART_DIR = BASE / "outputs" / "charts"
REPORT_DIR = BASE / "outputs" / "reports"
TABLE_DIR = BASE / "outputs" / "tables"
for folder in (PROCESSED_DIR, CHART_DIR, REPORT_DIR, TABLE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("ai_usage_analysis")
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.figsize": (9, 5.5), "axes.titlesize": 14,
                     "axes.labelsize": 11, "savefig.dpi": 160})


def find_input():
    files = sorted([*RAW_DIR.glob("*.csv"), *RAW_DIR.glob("*.xlsx"), *RAW_DIR.glob("*.xls")])
    if not files:
        raise FileNotFoundError(f"No CSV/XLSX dataset found in {RAW_DIR}")
    if len(files) > 1:
        log.warning("Multiple data files found; using %s", files[0].name)
    return files[0]


def load_data(path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def numeric_clean(series):
    """Parse numeric strings, tolerating currency symbols and unit suffixes."""
    cleaned = series.astype("string").str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace(r"[^0-9eE.+\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def standardize_categories(df):
    maps = {
        "Gender": {"m": "Male", "male": "Male", "f": "Female", "female": "Female",
                   "other": "Other", "non-binary": "Non-binary"},
        "AI_Tool": {"chatgpt": "ChatGPT", "chat gpt": "ChatGPT",
                    "google gemini": "Google Gemini", "gemini": "Google Gemini"},
        "Education_Level": {"undergrad": "Undergraduate", "bachelors": "Bachelor's",
                            "ba/bsc": "Bachelor's", "masters": "Master's",
                            "ph.d.": "PhD", "phd": "PhD"},
        "Would_Recommend": {"yes": "Yes", "no": "No", "maybe": "Maybe"},
    }
    for col, mapping in maps.items():
        if col in df:
            s = df[col].astype("string").str.strip()
            df[col] = s.map(lambda x: mapping.get(x.casefold(), x) if pd.notna(x) else pd.NA)
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if col not in maps:
            df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
    return df


def clean_data(raw):
    df = raw.copy()
    initial_rows = len(df)
    exact_dupes = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    # Normalize common text variants before converting numeric columns.
    df = standardize_categories(df)
    numeric_cols = ["Age", "Monthly_Income", "AI_Usage_Hours_Per_Day", "Monthly_AI_Cost",
                    "Productivity_Score", "Accuracy_Rating", "Satisfaction_Score",
                    "Time_Saved_Hours_Per_Week", "Work_or_Study_Hours_Per_Day"]
    for col in numeric_cols:
        if col in df:
            df[col] = numeric_clean(df[col])
    # Plausibility limits are based on units implied by column names and standard scales.
    bounds = {"Age": (13, 100), "AI_Usage_Hours_Per_Day": (0, 24),
              "Work_or_Study_Hours_Per_Day": (0, 24),
              "Time_Saved_Hours_Per_Week": (0, 168), "Monthly_AI_Cost": (0, None),
              "Monthly_Income": (0, None), "Productivity_Score": (0, 10),
              "Accuracy_Rating": (1, 5), "Satisfaction_Score": (1, 10)}
    invalid_counts = {}
    for col, (lo, hi) in bounds.items():
        if col not in df: continue
        invalid = df[col].notna() & ((df[col] < lo) | ((df[col] > hi) if hi is not None else False))
        invalid_counts[col] = int(invalid.sum())
        df.loc[invalid, col] = np.nan
    # Preserve missingness; no statistically unjustified blanket imputation.
    stats_out = {
        "input_rows": initial_rows, "rows_after_exact_deduplication": len(df),
        "exact_duplicate_rows_removed": exact_dupes,
        "columns": len(df.columns),
        "missing_cells_before": int(raw.isna().sum().sum()),
        "missing_cells_after": int(df.isna().sum().sum()),
        "invalid_values_set_missing_by_column": invalid_counts,
        "duplicate_user_ids_after_exact_deduplication":
            int(df["User_ID"].duplicated().sum()) if "User_ID" in df else None
    }
    return df, stats_out


def save_table(df, name):
    df.to_csv(TABLE_DIR / name, index=True)


def descriptive_tables(df):
    numeric = df.select_dtypes(include=np.number)
    desc = numeric.describe().T
    desc["median"] = numeric.median()
    desc["mode"] = numeric.mode().iloc[0] if not numeric.mode().empty else np.nan
    desc["variance"] = numeric.var()
    desc.to_csv(TABLE_DIR / "numeric_descriptive_statistics.csv")
    categorical_rows = []
    for col in df.select_dtypes(exclude=np.number).columns:
        if col == "User_ID": continue
        counts = df[col].value_counts(dropna=False)
        for value, count in counts.items():
            categorical_rows.append({"column": col, "category": str(value) if pd.notna(value) else "Missing",
                                     "count": int(count), "percentage": count / len(df) * 100})
    pd.DataFrame(categorical_rows).to_csv(TABLE_DIR / "categorical_frequency_distributions.csv", index=False)
    missing = pd.DataFrame({"column": df.columns, "missing_count": df.isna().sum().values,
                            "missing_percent": df.isna().mean().values * 100})
    missing.to_csv(TABLE_DIR / "missing_value_summary.csv", index=False)
    return desc, missing


def outlier_table(df):
    rows = []
    for col in df.select_dtypes(include=np.number):
        s = df[col].dropna()
        if len(s) < 4: continue
        q1, q3 = s.quantile([.25, .75]); iqr = q3-q1
        low, high = q1-1.5*iqr, q3+1.5*iqr
        vals = s[(s < low) | (s > high)]
        rows.append({"column": col, "q1": q1, "q3": q3, "iqr": iqr,
                     "lower_fence": low, "upper_fence": high,
                     "outlier_count": len(vals), "outlier_percent_of_nonmissing": len(vals)/len(s)*100})
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "iqr_outlier_screening.csv", index=False)
    return out


def correlation_analysis(df):
    cols = [c for c in ["Age", "Monthly_Income", "AI_Usage_Hours_Per_Day", "Monthly_AI_Cost",
                         "Productivity_Score", "Accuracy_Rating", "Satisfaction_Score",
                         "Time_Saved_Hours_Per_Week", "Work_or_Study_Hours_Per_Day"] if c in df]
    corr = df[cols].corr(method="spearman")
    corr.to_csv(TABLE_DIR / "spearman_correlation_matrix.csv")
    pairs = [("AI_Usage_Hours_Per_Day", "Productivity_Score"),
             ("Time_Saved_Hours_Per_Week", "Productivity_Score"),
             ("Productivity_Score", "Satisfaction_Score"),
             ("Accuracy_Rating", "Satisfaction_Score"),
             ("AI_Usage_Hours_Per_Day", "Time_Saved_Hours_Per_Week")]
    results=[]
    for x,y in pairs:
        if x not in df or y not in df: continue
        pair=df[[x,y]].dropna()
        if len(pair)<3: continue
        r,p=stats.spearmanr(pair[x],pair[y])
        # Percentile bootstrap CI for Spearman rho; deterministic for reproducibility.
        rng=np.random.default_rng(20261127)
        boot=[]
        xa=pair[x].to_numpy(); ya=pair[y].to_numpy(); n_pair=len(pair)
        for _ in range(1000):
            idx=rng.integers(0,n_pair,n_pair)
            if np.unique(xa[idx]).size > 1 and np.unique(ya[idx]).size > 1:
                boot.append(stats.spearmanr(xa[idx],ya[idx]).statistic)
        ci_low,ci_high=np.percentile(boot,[2.5,97.5]) if boot else (np.nan,np.nan)
        results.append({"variable_x":x,"variable_y":y,"method":"Spearman rank correlation",
                        "n":len(pair),"coefficient":r,"p_value":p,
                        "bootstrap_95ci_lower":ci_low,"bootstrap_95ci_upper":ci_high})
    res=pd.DataFrame(results)
    res.to_csv(TABLE_DIR / "correlation_tests.csv",index=False)
    return corr,res


def hypothesis_tests(df):
    rows=[]
    if {"User_Type","Productivity_Score"}.issubset(df.columns):
        a=df.loc[df.User_Type.astype("string").str.casefold()=="student","Productivity_Score"].dropna()
        b=df.loc[df.User_Type.astype("string").str.casefold()=="professional","Productivity_Score"].dropna()
        if len(a)>=2 and len(b)>=2:
            u,p=stats.mannwhitneyu(a,b,alternative="two-sided")
            # Rank-biserial effect size; positive means first group tends higher.
            effect=1-(2*u)/(len(a)*len(b))
            rows.append({"comparison":"Productivity score: Student vs Professional",
                         "test":"Mann–Whitney U, two-sided","n_group_1":len(a),"n_group_2":len(b),
                         "group_1_median":a.median(),"group_2_median":b.median(),
                         "statistic":u,"p_value":p,"effect_size_rank_biserial":effect})
    if {"User_Type","Satisfaction_Score"}.issubset(df.columns):
        a=df.loc[df.User_Type.astype("string").str.casefold()=="student","Satisfaction_Score"].dropna()
        b=df.loc[df.User_Type.astype("string").str.casefold()=="professional","Satisfaction_Score"].dropna()
        if len(a)>=2 and len(b)>=2:
            u,p=stats.mannwhitneyu(a,b,alternative="two-sided")
            effect=1-(2*u)/(len(a)*len(b))
            rows.append({"comparison":"Satisfaction score: Student vs Professional",
                         "test":"Mann–Whitney U, two-sided","n_group_1":len(a),"n_group_2":len(b),
                         "group_1_median":a.median(),"group_2_median":b.median(),
                         "statistic":u,"p_value":p,"effect_size_rank_biserial":effect})
    out=pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "hypothesis_tests.csv",index=False)
    return out


def make_charts(df, corr):
    charts=[]
    def save(name):
        plt.tight_layout(); plt.savefig(CHART_DIR/name,bbox_inches="tight"); plt.close(); charts.append(name)
    for col in ["Age","AI_Usage_Hours_Per_Day","Productivity_Score","Satisfaction_Score",
                "Time_Saved_Hours_Per_Week","Work_or_Study_Hours_Per_Day"]:
        if col in df and df[col].notna().sum():
            plt.figure(); sns.histplot(df[col].dropna(),kde=True,bins=20,color="steelblue")
            plt.title(f"Distribution of {col.replace('_',' ')}"); plt.xlabel(col.replace('_',' ')); plt.ylabel("Number of records")
            save(f"distribution_{col.lower()}.png")
    for col in ["User_Type","AI_Tool","AI_Purpose","Would_Recommend","Gender","Education_Level"]:
        if col in df:
            counts=df[col].value_counts().head(12)
            if len(counts):
                plt.figure(figsize=(10,max(4,.35*len(counts))))
                sns.barplot(x=counts.values,y=counts.index,color="steelblue")
                plt.title(f"Records by {col.replace('_',' ')} (top 12)"); plt.xlabel("Number of records"); plt.ylabel(col.replace('_',' '))
                save(f"category_{col.lower()}.png")
    if "User_Type" in df:
        counts=df["User_Type"].value_counts()
        if len(counts):
            plt.figure(figsize=(7,6)); plt.pie(counts.values,labels=counts.index,autopct="%1.1f%%",startangle=90)
            plt.title("Share of students and professionals"); plt.axis("equal")
            save("user_type_share_pie.png")
    if {"AI_Usage_Hours_Per_Day","Productivity_Score"}.issubset(df):
        plt.figure(); sns.regplot(data=df,x="AI_Usage_Hours_Per_Day",y="Productivity_Score",
                                  scatter_kws={"alpha":.55},line_kws={"color":"crimson"})
        plt.title("Daily AI use vs productivity score"); plt.xlabel("AI usage (hours/day)"); plt.ylabel("Productivity score")
        save("ai_usage_vs_productivity.png")
    if {"Time_Saved_Hours_Per_Week","Productivity_Score"}.issubset(df):
        plt.figure(); sns.scatterplot(data=df,x="Time_Saved_Hours_Per_Week",y="Productivity_Score",
                                      hue="User_Type" if "User_Type" in df else None,alpha=.75)
        plt.title("Weekly time saved vs productivity score"); plt.xlabel("Time saved (hours/week)"); plt.ylabel("Productivity score")
        save("time_saved_vs_productivity.png")
    if {"User_Type","Productivity_Score"}.issubset(df):
        plt.figure(); sns.boxplot(data=df,x="User_Type",y="Productivity_Score",color="steelblue")
        plt.title("Productivity score by user type"); plt.xlabel("User type"); plt.ylabel("Productivity score")
        save("productivity_by_user_type.png")
    if corr.size:
        plt.figure(figsize=(11,8)); sns.heatmap(corr,annot=True,fmt=".2f",cmap="vlag",center=0,square=True)
        plt.title("Spearman correlation heatmap"); save("spearman_correlation_heatmap.png")
    return charts


def fmt_num(x, digits=2):
    return "not available" if pd.isna(x) else f"{x:.{digits}f}"


def fmt_p(x):
    return "not available" if pd.isna(x) else (f"{x:.3g}" if x < 0.001 else f"{x:.4f}")


def build_report(raw, df, clean_stats, desc, missing, outliers, corr_tests, tests, charts):
    lines=["# AI Usage and Impact on Students and Professionals — Analysis Report","",
           "## Executive summary",
           f"- Original dataset: **{len(raw):,} rows × {len(raw.columns)} columns**.",
           f"- Cleaned dataset: **{len(df):,} rows × {len(df.columns)} columns**.",
           f"- Removed **{clean_stats['exact_duplicate_rows_removed']} exact duplicate rows**; no non-identical records were removed.",
           f"- Missing cells after cleaning: **{clean_stats['missing_cells_after']:,}**. Missing values were retained rather than filled with unsupported assumptions.",
           "- IQR outliers are flagged for review only; they are not automatically deleted.",
           "- Findings describe associations in this observational dataset and do not establish causation.","",
           "## Dataset and field interpretation",
           "The CSV contains 19 fields. Meanings below are interpreted from field names; the supplied file does not include a separate data dictionary.",
           "- Identity/context: User_ID, Age, Gender, Country, User_Type, Education_Level, Profession.",
           "- AI adoption: Monthly_Income, AI_Tool, AI_Purpose, AI_Usage_Hours_Per_Day, Tasks_Performed, Monthly_AI_Cost.",
           "- Reported outcomes: Productivity_Score, Accuracy_Rating, Satisfaction_Score, Time_Saved_Hours_Per_Week, Work_or_Study_Hours_Per_Day, Would_Recommend.","",
           "## Data quality and preprocessing",
           f"- Exact duplicates removed: {clean_stats['exact_duplicate_rows_removed']}.",
           f"- Missing cells before cleaning: {clean_stats['missing_cells_before']}; after cleaning: {clean_stats['missing_cells_after']}.",
           "- Numeric strings were parsed after removing display-only currency/unit characters (e.g. `$`, `hrs`). Currency units are not specified in the source, so income/cost values are not labelled with a currency.",
           "- Known spelling/case variants were standardized for Gender, AI_Tool, Education_Level, and Would_Recommend.",
           "- Plausibility validation: Age 13–100; daily hours 0–24; weekly time saved 0–168; Productivity 0–10; Accuracy 1–5; Satisfaction 1–10; monetary fields non-negative.",
           "- Values outside these limits were set to missing, not silently clipped. Review `data_quality_validation.json` for counts.",
           "- Missing values were not imputed. IQR outlier screening is documented in `iqr_outlier_screening.csv`; potential outliers remain in the cleaned data.","",
           "## Dataset profile",
           f"- User type distribution: {df['User_Type'].value_counts().to_dict() if 'User_Type' in df else 'not available'}",
           f"- Most common AI tool: {df['AI_Tool'].mode().iloc[0] if 'AI_Tool' in df and not df['AI_Tool'].mode().empty else 'not available'}",
           f"- Most common AI purpose: {df['AI_Purpose'].mode().iloc[0] if 'AI_Purpose' in df and not df['AI_Purpose'].mode().empty else 'not available'}","",
           "## Descriptive statistics",
           "See `outputs/tables/numeric_descriptive_statistics.csv` for count, mean, standard deviation, min/max, quartiles, median, mode and variance.",
           "## Statistical analysis","",
           "### Spearman correlations"]
    if len(corr_tests):
        for _,r in corr_tests.iterrows():
            lines.append(f"- {r.variable_x} vs {r.variable_y}: ρ = {fmt_num(r.coefficient,3)}, n = {int(r.n)}, p = {fmt_p(r.p_value)}, bootstrap 95% CI [{fmt_num(r.bootstrap_95ci_lower,3)}, {fmt_num(r.bootstrap_95ci_upper,3)}].")
    else: lines.append("- No eligible correlation pairs were available.")
    lines += ["","### Group comparisons (Mann–Whitney U, two-sided)"]
    if len(tests):
        for _,r in tests.iterrows():
            lines.append(f"- {r.comparison}: medians {fmt_num(r.group_1_median)} (n={int(r.n_group_1)}) vs {fmt_num(r.group_2_median)} (n={int(r.n_group_2)}); p={fmt_p(r.p_value)}; rank-biserial effect={fmt_num(r.effect_size_rank_biserial,3)}.")
    else: lines.append("- Group tests could not be run because sample sizes were insufficient.")
    lines += ["","P-values are not proof of practical importance. Correlation tests are pairwise and do not adjust for confounding or multiple comparisons.",
              "## Visualizations",""] + [f"- `{x}`" for x in charts]
    lines += ["","## Limitations",
              "- The dataset is a sample of 300 records; representativeness and sampling method are not documented in the supplied CSV.",
              "- The source provides no data dictionary, currency unit, survey wording, collection dates, or sampling design.",
              "- Several variables are self-reported scores/hours; measurement error and response bias are possible.",
              "- Cross-sectional observational data cannot establish that AI use causes productivity, accuracy, satisfaction, or time savings.",
              "- Missingness may bias complete-case statistics; no imputation was performed.",
              "- Profession and task descriptions are high-cardinality free-text fields and are not aggressively grouped.","",
              "## Recommendations",
              "- Interpret AI-use and outcome relationships as exploratory; validate them with a larger, representative, longitudinal sample.",
              "- Track consistent outcome definitions and units (especially currency, productivity scale, and time saved) in future data collection.",
              "- Compare students and professionals with attention to group sizes, uncertainty, and potential confounders such as profession and working hours.",
              "- Use the generated charts and tables to identify hypotheses for follow-up rather than making causal claims.","",
              "## Reproducibility",
              "Run `python analysis.py` from the project directory after installing `requirements.txt`. The script recreates the cleaned dataset, charts, CSV tables, JSON validation log, and this report."]
    (REPORT_DIR/"analysis_report.md").write_text("\n".join(lines),encoding="utf-8")


def main():
    path=find_input()
    log.info("Loading dataset: %s",path.name)
    raw=load_data(path)
    if raw.empty: raise ValueError("Input dataset is empty.")
    log.info("Loaded %d rows and %d columns",*raw.shape)
    df,clean_stats=clean_data(raw)
    cleaned_path=PROCESSED_DIR/"cleaned_dataset.csv"
    df.to_csv(cleaned_path,index=False)
    (REPORT_DIR/"data_quality_validation.json").write_text(json.dumps(clean_stats,indent=2,default=str),encoding="utf-8")
    desc,missing=descriptive_tables(df)
    outliers=outlier_table(df)
    corr,corr_tests=correlation_analysis(df)
    tests=hypothesis_tests(df)
    charts=make_charts(df,corr)
    build_report(raw,df,clean_stats,desc,missing,outliers,corr_tests,tests,charts)
    # Automated integrity checks on generated outputs.
    assert len(pd.read_csv(cleaned_path))==len(df)
    assert (TABLE_DIR/"numeric_descriptive_statistics.csv").exists()
    assert (REPORT_DIR/"analysis_report.md").exists()
    assert len(list(CHART_DIR.glob("*.png")))>0
    log.info("Finished. Cleaned rows=%d; exact duplicates removed=%d; charts=%d",
             len(df),clean_stats["exact_duplicate_rows_removed"],len(charts))
    print("\nKEY FINDINGS")
    print(f"Rows: {len(raw)} original -> {len(df)} cleaned; columns: {len(df.columns)}")
    print(f"Exact duplicates removed: {clean_stats['exact_duplicate_rows_removed']}")
    print(f"Missing cells after cleaning: {clean_stats['missing_cells_after']}")
    if "User_Type" in df: print("User type counts:",df["User_Type"].value_counts().to_dict())
    if "AI_Tool" in df: print("Top AI tools:",df["AI_Tool"].value_counts().head(5).to_dict())
    if len(corr_tests): print("Spearman tests:\n",corr_tests.to_string(index=False))
    if len(tests): print("Group tests:\n",tests.to_string(index=False))
    print(f"\nOutputs saved under: {BASE/'outputs'}")

if __name__=="__main__":
    try: main()
    except Exception:
        log.exception("Analysis pipeline failed.")
        raise
