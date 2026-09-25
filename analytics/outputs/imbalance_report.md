# Imbalance Comparison

| variant                    |   precision |   recall |       f1 |
|:---------------------------|------------:|---------:|---------:|
| Baseline                   |    0.783333 | 0.691176 | 0.734375 |
| class_weight=balanced      |    0.71831  | 0.75     | 0.733813 |
| SMOTE (training fold only) |    0.735294 | 0.735294 | 0.735294 |

The three imbalance variants were evaluated on the same held-out test set. Using F1 as the comparison criterion, **SMOTE (training fold only)** achieved the highest observed F1 of 0.7353. SMOTE is applied inside an imbalanced-learn pipeline after the train/test split, so synthetic samples are created from training data only and cannot leak test information.
