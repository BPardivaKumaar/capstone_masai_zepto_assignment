"""Reload the saved end-to-end classifier pipeline and predict on raw feature columns."""

from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "artifacts" / "best_pipeline.joblib"
CSV = ROOT / "titanic.csv"
FEATURES = ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"]


def main() -> None:
    if not ARTIFACT.exists():
        raise FileNotFoundError("Run `python analytics/02_modeling.py` first.")

    pipeline = joblib.load(ARTIFACT)
    df = pd.read_csv(CSV)
    raw_input = df[FEATURES].head(5)
    predictions = pipeline.predict(raw_input)

    print("Raw input rows:")
    print(raw_input.to_string(index=False))
    print("\nPredictions after reloading the complete pipeline:")
    print(predictions.tolist())
    print("\nReload check passed: preprocessing and model are stored together in one Pipeline artifact.")


if __name__ == "__main__":
    main()
