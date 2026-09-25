# Titanic EDA Report

## 1. Raw dataset profile

Shape before cleaning: **(891, 15)**

### `df.info()` and `df.describe()`

See the console output produced by `python analytics/01_eda.py`.

### Missing-value percentages

|             |   missing_pct |
|:------------|--------------:|
| deck        |       77.2166 |
| age         |       19.8653 |
| embarked    |        0.2245 |
| embark_town |        0.2245 |

## 2. Cleaning decisions

- **deck**: Dropped because missingness was 77.2166%, above the 30% threshold where direct imputation would be unreliable.
- **embarked**: Dropped rows because missingness was 0.2245%, below the 5% threshold.
- **embark_town**: Dropped rows because missingness was 0.2245%, below the 5% threshold.
- **age**: Median-imputed because missingness was 19.8653%, inside the 5%-30% imputation band.

Cleaned shape: **(889, 14)**

## 3. Univariate analysis

- `age` IQR outlier count: **65**.
- `fare` IQR outlier count: **114**.
- Fare mean: **32.0967**.
- Fare median: **14.4542**.
- Fare mode: **8.0500**.
- Fare distribution conclusion: **right-skewed.** The conclusion is based on the mean/median/mode ordering.

## 4. Bivariate analysis

### Survival by sex
Female survival rate: **74.04%**. Male survival rate: **18.89%**.
This is a descriptive association in the cleaned Titanic data, not a causal claim.

### Survival by passenger class
Pclass 1: 62.6%; Pclass 2: 47.3%; Pclass 3: 24.2%

### Survival by sex and class
Highest observed combination: **('female', np.int64(1))** at **96.74%**. Lowest observed combination: **('male', np.int64(3))** at **13.54%**.
The grouped pattern shows that survival varies jointly by sex and passenger class.

### Two strongest correlations
pclass vs fare (r=-0.548, |r|=0.548); sibsp vs parch (r=0.415, |r|=0.415)
The ranking is based on the two largest absolute off-diagonal correlation coefficients from exactly the six required numeric columns.

## 5. Multivariate data story

### Chart 1 - Survival rate by sex
Female passengers have a survival rate of 74.0%, compared with 18.9% for male passengers. The gap is large in this dataset, so sex is a strong descriptive separator of outcomes.

### Chart 2 - Survival rate by passenger class
Survival rates are computed separately for first, second, and third class. The chart shows a class gradient in the observed outcome, so passenger class is another important descriptive feature.

### Chart 3 - Survival rate by sex and passenger class
The combined groups make the interaction visible: the observed best group is ('female', np.int64(1)), while the observed lowest is ('male', np.int64(3)). This indicates that the sex pattern is not identical across all passenger classes.

### Chart 4 - Age versus fare by survival
The scatter plot shows how age and fare occupy different ranges for survivors and non-survivors, while also showing overlap between the two classes. The plot should be read as a multivariate pattern rather than a deterministic rule.

### Chart 5 - Fare by survival
The fare box plot shows how the distribution of paid fare differs between the two survival groups. The spread and overlap indicate that fare alone cannot perfectly separate the outcomes, but it still carries useful signal.

## 6. Exploratory standardization check

The script prints pre- and post-standardization means and standard deviations for `age` and `fare`; the transformed columns should be approximately mean 0 and standard deviation 1.

## Files generated

- `titanic.csv` - committed offline fallback used by the modeling stage.
- `outputs/age_hist.png`, `age_box.png`, `fare_hist.png`, `fare_box.png` - univariate charts.
- `outputs/survival_by_sex.png`, `survival_by_class.png`, `survival_by_sex_class.png`, `age_fare_survival.png`, `fare_by_survival.png` - multivariate charts.
- `outputs/correlation_heatmap.png` - exact 6x6 correlation matrix.
- `outputs/standardization_check.csv` - before/after z-score summary.