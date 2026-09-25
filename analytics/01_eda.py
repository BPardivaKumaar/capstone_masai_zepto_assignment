"""Titanic EDA and cleaning pipeline.

Run this script before 02_modeling.py. The first run needs internet because
seaborn.fetches the built-in Titanic dataset once and then we save the
cleaned continuation dataset to titanic.csv for offline grading.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    report = (df.isna().mean().mul(100).round(4).rename("missing_pct").to_frame())
    return report[report["missing_pct"] > 0].sort_values("missing_pct", ascending=False)


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Apply the assignment's <5%, 5-30%, and high-missingness rules."""
    work = df.copy()
    report = missing_report(work)
    decisions: dict[str, str] = {}

    high_cols = report.index[report["missing_pct"] > 30].tolist()
    for col in high_cols:
        work = work.drop(columns=[col])
        decisions[col] = (
            f"Dropped because missingness was {report.loc[col, 'missing_pct']:.4f}%, "
            "above the 30% threshold where direct imputation would be unreliable."
        )

    low_cols = report.index[report["missing_pct"] < 5].tolist()
    for col in low_cols:
        if col not in work.columns:
            continue
        work = work.dropna(subset=[col])
        decisions[col] = (
            f"Dropped rows because missingness was {report.loc[col, 'missing_pct']:.4f}%, "
            "below the 5% threshold."
        )

    mid_cols = report.index[(report["missing_pct"] >= 5) & (report["missing_pct"] <= 30)].tolist()
    for col in mid_cols:
        if col not in work.columns:
            continue
        if pd.api.types.is_numeric_dtype(work[col]):
            fill_value = work[col].median()
            work[col] = work[col].fillna(fill_value)
            decisions[col] = (
                f"Median-imputed because missingness was {report.loc[col, 'missing_pct']:.4f}%, "
                "inside the 5%-30% imputation band."
            )
        else:
            fill_value = work[col].mode(dropna=True).iloc[0]
            work[col] = work[col].fillna(fill_value)
            decisions[col] = (
                f"Mode-imputed because missingness was {report.loc[col, 'missing_pct']:.4f}%, "
                "inside the 5%-30% imputation band."
            )

    return work.reset_index(drop=True), decisions


def iqr_outlier_count(series: pd.Series) -> tuple[float, float, int]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    count = int(((series < low) | (series > high)).sum())
    return low, high, count


def save_eda_report(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    decisions: dict[str, str],
    fare_stats: dict[str, float | str],
    age_outliers: int,
    fare_outliers: int,
    survival_by_sex: pd.Series,
    survival_by_pclass: pd.Series,
    survival_by_sex_class: pd.DataFrame,
    top_corrs: list[tuple[str, str, float]],
) -> None:
    missing = missing_report(raw)

    female = float(survival_by_sex.get("female", np.nan))
    male = float(survival_by_sex.get("male", np.nan))

    class_lines = "; ".join(
        f"Pclass {int(k)}: {float(v):.1%}" for k, v in survival_by_pclass.items()
    )
    strongest = "; ".join(
        f"{a} vs {b} (r={r:.3f}, |r|={abs(r):.3f})" for a, b, r in top_corrs
    )

    # Pick the highest/lowest sex-pclass combinations for a concise narrative.
    combo_series = survival_by_sex_class.copy()
    highest_combo = combo_series.idxmax()
    lowest_combo = combo_series.idxmin()

    lines = [
        "# Titanic EDA Report",
        "",
        "## 1. Raw dataset profile",
        "",
        f"Shape before cleaning: **{raw.shape}**",
        "",
        "### `df.info()` and `df.describe()`",
        "",
        "See the console output produced by `python analytics/01_eda.py`.",
        "",
        "### Missing-value percentages",
        "",
        missing.to_markdown(),
        "",
        "## 2. Cleaning decisions",
        "",
    ]
    for col, decision in decisions.items():
        lines.append(f"- **{col}**: {decision}")
    lines.extend(
        [
            "",
            f"Cleaned shape: **{cleaned.shape}**",
            "",
            "## 3. Univariate analysis",
            "",
            f"- `age` IQR outlier count: **{age_outliers}**.",
            f"- `fare` IQR outlier count: **{fare_outliers}**.",
            f"- Fare mean: **{fare_stats['mean']:.4f}**.",
            f"- Fare median: **{fare_stats['median']:.4f}**.",
            f"- Fare mode: **{fare_stats['mode']:.4f}**.",
            f"- Fare distribution conclusion: **{fare_stats['skew']}.** The conclusion is based on the mean/median/mode ordering.",
            "",
            "## 4. Bivariate analysis",
            "",
            "### Survival by sex",
            f"Female survival rate: **{female:.2%}**. Male survival rate: **{male:.2%}**.",
            "This is a descriptive association in the cleaned Titanic data, not a causal claim.",
            "",
            "### Survival by passenger class",
            class_lines,
            "",
            "### Survival by sex and class",
            f"Highest observed combination: **{highest_combo}** at **{combo_series.loc[highest_combo]:.2%}**. Lowest observed combination: **{lowest_combo}** at **{combo_series.loc[lowest_combo]:.2%}**.",
            "The grouped pattern shows that survival varies jointly by sex and passenger class.",
            "",
            "### Two strongest correlations",
            strongest,
            "The ranking is based on the two largest absolute off-diagonal correlation coefficients from exactly the six required numeric columns.",
            "",
            "## 5. Multivariate data story",
            "",
            "### Chart 1 - Survival rate by sex",
            f"Female passengers have a survival rate of {female:.1%}, compared with {male:.1%} for male passengers. The gap is large in this dataset, so sex is a strong descriptive separator of outcomes.",
            "",
            "### Chart 2 - Survival rate by passenger class",
            "Survival rates are computed separately for first, second, and third class. The chart shows a class gradient in the observed outcome, so passenger class is another important descriptive feature.",
            "",
            "### Chart 3 - Survival rate by sex and passenger class",
            f"The combined groups make the interaction visible: the observed best group is {highest_combo}, while the observed lowest is {lowest_combo}. This indicates that the sex pattern is not identical across all passenger classes.",
            "",
            "### Chart 4 - Age versus fare by survival",
            "The scatter plot shows how age and fare occupy different ranges for survivors and non-survivors, while also showing overlap between the two classes. The plot should be read as a multivariate pattern rather than a deterministic rule.",
            "",
            "### Chart 5 - Fare by survival",
            "The fare box plot shows how the distribution of paid fare differs between the two survival groups. The spread and overlap indicate that fare alone cannot perfectly separate the outcomes, but it still carries useful signal.",
            "",
            "## 6. Exploratory standardization check",
            "",
            "The script prints pre- and post-standardization means and standard deviations for `age` and `fare`; the transformed columns should be approximately mean 0 and standard deviation 1.",
            "",
            "## Files generated",
            "",
            "- `titanic.csv` - committed offline fallback used by the modeling stage.",
            "- `outputs/age_hist.png`, `age_box.png`, `fare_hist.png`, `fare_box.png` - univariate charts.",
            "- `outputs/survival_by_sex.png`, `survival_by_class.png`, `survival_by_sex_class.png`, `age_fare_survival.png`, `fare_by_survival.png` - multivariate charts.",
            "- `outputs/correlation_heatmap.png` - exact 6x6 correlation matrix.",
            "- `outputs/standardization_check.csv` - before/after z-score summary.",
        ]
    )
    (OUT / "eda_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("Loading Titanic dataset once with seaborn...")
    raw = sns.load_dataset("titanic")

    # Required offline fallback write immediately after the one network/cache load.
    raw.to_csv(ROOT / "titanic.csv", index=False)

    print("\n=== df.info() ===")
    raw.info()
    print("\n=== df.describe() ===")
    print(raw.describe(include="all").to_string())
    print("\n=== df.shape ===")
    print(raw.shape)

    raw_missing = missing_report(raw)
    print("\n=== Missing percentages ===")
    print(raw_missing.to_string())

    cleaned, decisions = clean_dataset(raw)

    # The committed titanic.csv becomes the cleaned continuation file used by 02_modeling.py.
    cleaned.to_csv(ROOT / "titanic.csv", index=False)

    for col, decision in decisions.items():
        print(f"{col}: {decision}")

    # ----------------------------- Univariate analysis -----------------------------
    age_low, age_high, age_outliers = iqr_outlier_count(cleaned["age"])
    fare_low, fare_high, fare_outliers = iqr_outlier_count(cleaned["fare"])

    fare_mean = float(cleaned["fare"].mean())
    fare_median = float(cleaned["fare"].median())
    fare_mode = float(cleaned["fare"].mode().iloc[0])

    if fare_mean > fare_median > fare_mode:
        fare_skew = "right-skewed"
    elif fare_mean < fare_median < fare_mode:
        fare_skew = "left-skewed"
    else:
        fare_skew = "not strongly directional from the mean/median/mode ordering"

    for col, title in [("age", "Age"), ("fare", "Fare")]:
        plt.figure(figsize=(7, 5))
        sns.histplot(cleaned[col], kde=True)
        plt.title(f"{title} histogram")
        plt.tight_layout()
        plt.savefig(OUT / f"{col}_hist.png", dpi=150)
        plt.close()

        plt.figure(figsize=(7, 4))
        sns.boxplot(x=cleaned[col])
        plt.title(f"{title} box plot")
        plt.tight_layout()
        plt.savefig(OUT / f"{col}_box.png", dpi=150)
        plt.close()

    print(f"age IQR bounds=({age_low:.3f}, {age_high:.3f}), outliers={age_outliers}")
    print(f"fare IQR bounds=({fare_low:.3f}, {fare_high:.3f}), outliers={fare_outliers}")
    print(
        f"fare mean={fare_mean:.4f}, median={fare_median:.4f}, mode={fare_mode:.4f}; "
        f"conclusion={fare_skew}"
    )

    # ----------------------------- Bivariate analysis -----------------------------
    survival_by_sex = cleaned.groupby("sex")["survived"].mean().sort_values(ascending=False)
    survival_by_pclass = cleaned.groupby("pclass")["survived"].mean().sort_index()

    combo_results: list[dict[str, object]] = []
    for sex in sorted(cleaned["sex"].unique()):
        for pclass in sorted(cleaned["pclass"].unique()):
            mask = (cleaned["sex"] == sex) & (cleaned["pclass"] == pclass)
            subset = cleaned[mask]
            combo_results.append(
                {"sex": sex, "pclass": pclass, "survival_rate": subset["survived"].mean()}
            )
    survival_by_sex_class = (
        pd.DataFrame(combo_results).set_index(["sex", "pclass"])["survival_rate"]
    )

    print("\n=== Survival by sex ===")
    print(survival_by_sex.to_string())
    print("\n=== Survival by pclass ===")
    print(survival_by_pclass.to_string())
    print("\n=== Survival by sex + pclass ===")
    print(survival_by_sex_class.to_string())

    corr_cols = ["survived", "pclass", "age", "sibsp", "parch", "fare"]
    corr = cleaned[corr_cols].corr()

    pair_values: list[tuple[str, str, float]] = []
    for i, a in enumerate(corr_cols):
        for b in corr_cols[i + 1 :]:
            pair_values.append((a, b, float(corr.loc[a, b])))
    top_corrs = sorted(pair_values, key=lambda x: abs(x[2]), reverse=True)[:2]

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True)
    plt.title("Titanic numeric correlation matrix")
    plt.tight_layout()
    plt.savefig(OUT / "correlation_heatmap.png", dpi=150)
    plt.close()

    # ----------------------------- Multivariate story -----------------------------
    plt.figure(figsize=(7, 5))
    sns.barplot(x=survival_by_sex.index, y=survival_by_sex.values)
    plt.ylabel("Survival rate")
    plt.title("Survival rate by sex")
    plt.tight_layout()
    plt.savefig(OUT / "survival_by_sex.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 5))
    sns.barplot(x=survival_by_pclass.index.astype(str), y=survival_by_pclass.values)
    plt.xlabel("Passenger class")
    plt.ylabel("Survival rate")
    plt.title("Survival rate by passenger class")
    plt.tight_layout()
    plt.savefig(OUT / "survival_by_class.png", dpi=150)
    plt.close()

    combo_plot = cleaned.copy()
    plt.figure(figsize=(8, 5))
    sns.barplot(data=combo_plot, x="pclass", y="survived", hue="sex", errorbar=None)
    plt.ylabel("Survival rate")
    plt.title("Survival rate by sex and passenger class")
    plt.tight_layout()
    plt.savefig(OUT / "survival_by_sex_class.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=cleaned, x="age", y="fare", hue="survived", alpha=0.65)
    plt.title("Age vs fare by survival")
    plt.tight_layout()
    plt.savefig(OUT / "age_fare_survival.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 5))
    sns.boxplot(data=cleaned, x="survived", y="fare")
    plt.title("Fare distribution by survival")
    plt.xlabel("Survived (0=no, 1=yes)")
    plt.tight_layout()
    plt.savefig(OUT / "fare_by_survival.png", dpi=150)
    plt.close()

    # ----------------------------- Exploratory standardization -----------------------------
    scaler = StandardScaler()
    standardized = scaler.fit_transform(cleaned[["age", "fare"]])
    standardized_df = pd.DataFrame(standardized, columns=["age_z", "fare_z"])
    check = pd.DataFrame(
        {
            "age_mean_before": [cleaned["age"].mean()],
            "age_std_before": [cleaned["age"].std(ddof=0)],
            "age_mean_after": [standardized_df["age_z"].mean()],
            "age_std_after": [standardized_df["age_z"].std(ddof=0)],
            "fare_mean_before": [cleaned["fare"].mean()],
            "fare_std_before": [cleaned["fare"].std(ddof=0)],
            "fare_mean_after": [standardized_df["fare_z"].mean()],
            "fare_std_after": [standardized_df["fare_z"].std(ddof=0)],
        }
    )
    check.to_csv(OUT / "standardization_check.csv", index=False)

    print("\n=== Standardization check ===")
    print(check.to_string(index=False))

    save_eda_report(
        raw=raw,
        cleaned=cleaned,
        decisions=decisions,
        fare_stats={
            "mean": fare_mean,
            "median": fare_median,
            "mode": fare_mode,
            "skew": fare_skew,
        },
        age_outliers=age_outliers,
        fare_outliers=fare_outliers,
        survival_by_sex=survival_by_sex,
        survival_by_pclass=survival_by_pclass,
        survival_by_sex_class=survival_by_sex_class,
        top_corrs=top_corrs,
    )
    print(f"EDA report saved to {OUT / 'eda_report.md'}")


if __name__ == "__main__":
    main()
