# Model Comparison

## Classification and regression metric groups

The classification and regression metrics are kept in separate columns because they measure different problems and are not directly comparable as one shared scale.

| Type           | Model                    | Accuracy   | Precision   | Recall   | F1     | AUC    | MAE     | RMSE    | R2     | Adjusted R2   |
|:---------------|:-------------------------|:-----------|:------------|:---------|:-------|:-------|:--------|:--------|:-------|:--------------|
| Classification | Logistic Regression      | 0.8090     | 0.7833      | 0.6912   | 0.7344 | 0.8610 | -       | -       | -      | -             |
| Classification | Decision Tree            | 0.7640     | 0.7600      | 0.5588   | 0.6441 | 0.8374 | -       | -       | -      | -             |
| Classification | Random Forest            | 0.8034     | 0.7619      | 0.7059   | 0.7328 | 0.8237 | -       | -       | -      | -             |
| Regression     | Linear Regression (fare) | -          | -           | -        | -      | -      | 21.0986 | 41.7021 | 0.3482 | 0.3091        |

## Final classifier recommendation

Among the three classifiers, **Logistic Regression** has the highest F1 score (0.7344) under the chosen deployment criterion. Its accuracy is 0.8090, precision is 0.7833, recall is 0.6912, and AUC is 0.8610. These values are evaluated on the same held-out stratified test split used for all three classifiers, so the comparison is like-for-like. The saved artifact is the complete fitted pipeline, including preprocessing, so it can accept raw feature columns in the same schema during prediction.
