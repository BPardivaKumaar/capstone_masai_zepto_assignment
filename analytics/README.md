# Module 2 - Analytics Pipeline

This module is intentionally split into two ordered Python scripts so it is easy to run in VS Code:

1. `01_eda.py` - the only `sns.load_dataset('titanic')` call; profiling, missing-value handling, EDA, charts, correlation analysis, and standardization sanity check.
2. `02_modeling.py` - reads the same committed `titanic.csv`, performs the stratified split before preprocessing, trains/evaluates the three required classifiers, performs imbalance comparison, GridSearchCV, fare regression, and saves the complete best pipeline.
3. `reload_pipeline.py` - reloads the saved `joblib` artifact and predicts on raw feature columns.

## Important dataset decision

The assignment asks for an immediate offline CSV write after the single Seaborn load and also requires the modeling stage to continue from the same cleaned data. `01_eda.py` therefore writes the raw DataFrame to `titanic.csv` immediately, performs the required cleaning, then overwrites `titanic.csv` with the cleaned continuation dataset. No second `sns.load_dataset('titanic')` call is made anywhere in the module.

## Run

```bash
pip install -r analytics/requirements.txt
python analytics/01_eda.py
python analytics/02_modeling.py
python analytics/reload_pipeline.py
```

The scripts generate the required plots and written interpretations under `analytics/outputs/` and save the complete fitted classifier pipeline under `analytics/artifacts/best_pipeline.joblib`.
