"""Titanic classification + imbalance study + tuning + fare regression."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.impute import SimpleImputer

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
ARTIFACTS = ROOT / "artifacts"
OUT.mkdir(exist_ok=True)
ARTIFACTS.mkdir(exist_ok=True)

RANDOM_STATE = 42

CLASS_FEATURES = ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"]
NUMERIC_CLASS = ["pclass", "age", "sibsp", "parch", "fare"]
CATEGORICAL_CLASS = ["sex", "embarked"]
REG_FEATURES = ["survived", "pclass", "sex", "age", "sibsp", "parch", "embarked"]
NUMERIC_REG = ["survived", "pclass", "age", "sibsp", "parch"]
CATEGORICAL_REG = ["sex", "embarked"]


def make_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipeline = ImbPipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = ImbPipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def classifier_pipeline(model) -> ImbPipeline:
    return ImbPipeline(
        steps=[
            ("preprocessor", make_preprocessor(NUMERIC_CLASS, CATEGORICAL_CLASS)),
            ("model", model),
        ]
    )


def evaluate_classifier(name: str, pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | str]:
    pred = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, pred)

    return {
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "auc": roc_auc_score(y_test, proba),
        "confusion_matrix": cm,
        "y_pred": pred,
        "y_proba": proba,
    }


def build_comparison_markdown(
    results: list[dict[str, float | str]], regression: dict[str, float], best_name: str
) -> str:
    rows = []
    for result in results:
        rows.append(
            {
                "Type": "Classification",
                "Model": result["model"],
                "Accuracy": f"{result['accuracy']:.4f}",
                "Precision": f"{result['precision']:.4f}",
                "Recall": f"{result['recall']:.4f}",
                "F1": f"{result['f1']:.4f}",
                "AUC": f"{result['auc']:.4f}",
                "MAE": "-",
                "RMSE": "-",
                "R2": "-",
                "Adjusted R2": "-",
            }
        )
    rows.append(
        {
            "Type": "Regression",
            "Model": "Linear Regression (fare)",
            "Accuracy": "-",
            "Precision": "-",
            "Recall": "-",
            "F1": "-",
            "AUC": "-",
            "MAE": f"{regression['mae']:.4f}",
            "RMSE": f"{regression['rmse']:.4f}",
            "R2": f"{regression['r2']:.4f}",
            "Adjusted R2": f"{regression['adjusted_r2']:.4f}",
        }
    )
    table = pd.DataFrame(rows).to_markdown(index=False)

    winner = next(r for r in results if r["model"] == best_name)
    recommendation = (
        f"Among the three classifiers, **{best_name}** has the highest F1 score ({winner['f1']:.4f}) under the chosen deployment criterion. "
        f"Its accuracy is {winner['accuracy']:.4f}, precision is {winner['precision']:.4f}, recall is {winner['recall']:.4f}, and AUC is {winner['auc']:.4f}. "
        "These values are evaluated on the same held-out stratified test split used for all three classifiers, so the comparison is like-for-like. "
        "The saved artifact is the complete fitted pipeline, including preprocessing, so it can accept raw feature columns in the same schema during prediction."
    )

    return f"""# Model Comparison

## Classification and regression metric groups

The classification and regression metrics are kept in separate columns because they measure different problems and are not directly comparable as one shared scale.

{table}

## Final classifier recommendation

{recommendation}
"""


def main() -> None:
    csv_path = ROOT / "titanic.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            "analytics/titanic.csv not found. Run `python analytics/01_eda.py` first."
        )

    df = pd.read_csv(csv_path)
    print(f"Loaded cleaned continuation dataset: {df.shape}")

    # ----------------------------- Train/test split FIRST -----------------------------
    X = df[CLASS_FEATURES].copy()
    y = df["survived"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    class_balance = y.value_counts(normalize=True).sort_index()
    print("\nClass balance (full cleaned data):")
    print(class_balance.to_string())
    print(
        "Stratification preserves the survived/not-survived proportion in the held-out test set, which makes model comparison more stable when the target classes are not exactly equal."
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }

    fitted: dict[str, ImbPipeline] = {}
    results: list[dict[str, float | str]] = []

    for name, model in models.items():
        pipeline = classifier_pipeline(model)
        pipeline.fit(X_train, y_train)
        fitted[name] = pipeline
        results.append(evaluate_classifier(name, pipeline, X_test, y_test))

    print("\n=== Classifier metrics ===")
    print(
        pd.DataFrame(
            [
                {
                    k: v
                    for k, v in r.items()
                    if k in {"model", "accuracy", "precision", "recall", "f1", "auc"}
                }
                for r in results
            ]
        ).to_string(index=False)
    )

    # Confusion matrices together.
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, result in zip(axes, results):
        ConfusionMatrixDisplay(
            confusion_matrix=result["confusion_matrix"], display_labels=["0", "1"]
        ).plot(ax=ax, colorbar=False)
        ax.set_title(result["model"])
    plt.tight_layout()
    plt.savefig(OUT / "confusion_matrices.png", dpi=150)
    plt.close(fig)

    # ROC curves together.
    plt.figure(figsize=(8, 6))
    for result in results:
        fpr, tpr, _ = roc_curve(y_test, result["y_proba"])
        plt.plot(fpr, tpr, label=f"{result['model']} (AUC={result['auc']:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", label="Chance")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "roc_curves.png", dpi=150)
    plt.close()

    # Decision tree visualization.
    tree_pipe = fitted["Decision Tree"]
    tree = tree_pipe.named_steps["model"]
    feature_names = tree_pipe.named_steps["preprocessor"].get_feature_names_out().tolist()
    plt.figure(figsize=(20, 10))
    plot_tree(
        tree,
        feature_names=feature_names,
        class_names=["Not survived", "Survived"],
        filled=True,
        max_depth=4,
        fontsize=8,
    )
    plt.title("Decision Tree (display limited to depth 4)")
    plt.tight_layout()
    plt.savefig(OUT / "decision_tree.png", dpi=150)
    plt.close()

    # ----------------------------- Imbalance comparison -----------------------------
    imbalance_models = {
        "Baseline": LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
        "class_weight=balanced": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
    }
    imbalance_rows = []
    for name, model in imbalance_models.items():
        pipe = classifier_pipeline(model)
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        imbalance_rows.append(
            {
                "variant": name,
                "precision": precision_score(y_test, pred, zero_division=0),
                "recall": recall_score(y_test, pred, zero_division=0),
                "f1": f1_score(y_test, pred, zero_division=0),
            }
        )

    smote_pipe = ImbPipeline(
        steps=[
            ("preprocessor", make_preprocessor(NUMERIC_CLASS, CATEGORICAL_CLASS)),
            ("smote", SMOTE(random_state=RANDOM_STATE)),
            ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]
    )
    smote_pipe.fit(X_train, y_train)
    smote_pred = smote_pipe.predict(X_test)
    imbalance_rows.append(
        {
            "variant": "SMOTE (training fold only)",
            "precision": precision_score(y_test, smote_pred, zero_division=0),
            "recall": recall_score(y_test, smote_pred, zero_division=0),
            "f1": f1_score(y_test, smote_pred, zero_division=0),
        }
    )

    imbalance_df = pd.DataFrame(imbalance_rows)
    imbalance_df.to_csv(OUT / "imbalance_comparison.csv", index=False)
    print("\n=== Imbalance comparison ===")
    print(imbalance_df.to_string(index=False))
    imbalance_best = imbalance_df.sort_values("f1", ascending=False).iloc[0]
    imbalance_text = (
        f"The three imbalance variants were evaluated on the same held-out test set. "
        f"Using F1 as the comparison criterion, **{imbalance_best['variant']}** achieved the highest observed F1 of {imbalance_best['f1']:.4f}. "
        "SMOTE is applied inside an imbalanced-learn pipeline after the train/test split, so synthetic samples are created from training data only and cannot leak test information."
    )
    (OUT / "imbalance_report.md").write_text(
        "# Imbalance Comparison\n\n"
        + imbalance_df.to_markdown(index=False)
        + "\n\n"
        + imbalance_text
        + "\n",
        encoding="utf-8",
    )

    # ----------------------------- Hyperparameter tuning -----------------------------
    rf_pipeline = classifier_pipeline(
        RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=-1,
            oob_score=True,
        )
    )
    grid = GridSearchCV(
        rf_pipeline,
        param_grid={
            "model__n_estimators": [100, 200],
            "model__max_depth": [8, 12],
            "model__max_features": ["sqrt", "log2"],
        },
        scoring="f1",
        cv=3,
        n_jobs=-1,
        refit=True,
    )
    grid.fit(X_train, y_train)
    best_rf = grid.best_estimator_
    oob_score = float(best_rf.named_steps["model"].oob_score_)

    print("\n=== Random Forest GridSearchCV ===")
    print(f"Best parameters: {grid.best_params_}")
    print(f"Best CV F1: {grid.best_score_:.4f}")
    print(f"OOB score: {oob_score:.4f}")

    tuning_report = pd.DataFrame(
        [
            {
                "best_params": str(grid.best_params_),
                "best_cv_f1": grid.best_score_,
                "oob_score": oob_score,
            }
        ]
    )
    tuning_report.to_csv(OUT / "gridsearch_result.csv", index=False)

    # ----------------------------- Regression side-task -----------------------------
    X_reg = df[REG_FEATURES].copy()
    y_reg = df["fare"].astype(float)
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
        X_reg, y_reg, test_size=0.20, random_state=RANDOM_STATE
    )

    reg_preprocessor = make_preprocessor(NUMERIC_REG, CATEGORICAL_REG)
    reg_pipeline = ImbPipeline(
        steps=[
            ("preprocessor", reg_preprocessor),
            ("model", LinearRegression()),
        ]
    )
    reg_pipeline.fit(Xr_train, yr_train)
    reg_pred = reg_pipeline.predict(Xr_test)

    mae = float(mean_absolute_error(yr_test, reg_pred))
    rmse = float(np.sqrt(mean_squared_error(yr_test, reg_pred)))
    r2 = float(r2_score(yr_test, reg_pred))
    p = len(reg_pipeline.named_steps["preprocessor"].get_feature_names_out())
    n = len(yr_test)
    adjusted_r2 = float(1 - (1 - r2) * (n - 1) / (n - p - 1)) if n > p + 1 else float("nan")

    reg_metrics = {"mae": mae, "rmse": rmse, "r2": r2, "adjusted_r2": adjusted_r2}
    print("\n=== Fare regression ===")
    print(pd.Series(reg_metrics).to_string())

    residuals = yr_test.to_numpy() - reg_pred
    plt.figure(figsize=(8, 5))
    plt.scatter(reg_pred, residuals, alpha=0.65)
    plt.axhline(0, linestyle="--")
    plt.xlabel("Predicted fare")
    plt.ylabel("Residual")
    plt.title("Fare regression residual plot")
    plt.tight_layout()
    plt.savefig(OUT / "fare_residuals.png", dpi=150)
    plt.close()

    # Simple quantitative support for the visual conclusion: compare residual spread by fitted-value bins.
    reg_bins = pd.qcut(pd.Series(reg_pred), q=4, duplicates="drop")
    spread_by_bin = pd.Series(residuals).groupby(reg_bins, observed=False).std()
    first_std = float(spread_by_bin.iloc[0])
    last_std = float(spread_by_bin.iloc[-1])
    hetero = abs(last_std / first_std) > 1.5 if first_std != 0 else False
    hetero_text = (
        "The residual plot suggests heteroscedasticity because the residual spread changes materially across fitted-value ranges."
        if hetero
        else "The residual plot does not show strong evidence of heteroscedasticity; residual spread is reasonably similar across fitted-value ranges."
    )
    (OUT / "regression_report.md").write_text(
        "# Fare Regression Report\n\n"
        + pd.Series(reg_metrics).to_frame("value").to_markdown()
        + "\n\n"
        + hetero_text
        + f"\n\nResidual standard deviations by fitted-value quartile:\n\n{spread_by_bin.to_string()}\n",
        encoding="utf-8",
    )

    # ----------------------------- Final model artifact -----------------------------
    best_result = max(results, key=lambda r: (r["f1"], r["auc"]))
    best_name = str(best_result["model"])
    best_pipeline = fitted[best_name]
    artifact_path = ARTIFACTS / "best_pipeline.joblib"
    joblib.dump(best_pipeline, artifact_path)

    # Save metrics and final comparison write-up.
    metrics_df = pd.DataFrame(
        [
            {
                "model": r["model"],
                "accuracy": r["accuracy"],
                "precision": r["precision"],
                "recall": r["recall"],
                "f1": r["f1"],
                "auc": r["auc"],
            }
            for r in results
        ]
    )
    metrics_df.to_csv(OUT / "classifier_metrics.csv", index=False)

    comparison_md = build_comparison_markdown(results, reg_metrics, best_name)
    (OUT / "model_comparison.md").write_text(comparison_md, encoding="utf-8")

    # Also store a machine-readable run summary.
    summary = {
        "best_initial_classifier": best_name,
        "gridsearch_best_params": grid.best_params_,
        "gridsearch_oob_score": oob_score,
        "regression_metrics": reg_metrics,
        "artifact": str(artifact_path.name),
    }
    pd.Series(summary, dtype="object").to_csv(OUT / "run_summary.csv")

    print(f"\nBest initial classifier by F1/AUC: {best_name}")
    print(f"Saved complete pipeline to {artifact_path}")
    print("Model comparison saved to outputs/model_comparison.md")
    print("Classification report for each model:")
    for result in results:
        print(f"\n--- {result['model']} ---")
        print(classification_report(y_test, result["y_pred"], digits=4, zero_division=0))


if __name__ == "__main__":
    main()
