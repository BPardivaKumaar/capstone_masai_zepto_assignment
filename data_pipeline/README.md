# Module 1 - Data Pipeline

This module implements the required **scrape -> clean -> convert -> SQLite -> SQL -> pandas comparison** workflow.

## Design decisions

- Source: `books.toscrape.com`.
- Scraped categories: Travel, Mystery, Fiction. Pagination is followed automatically, so no manual copy/paste is needed.
- Numeric parsing failures in `price_gbp` and `rating` are median-imputed.
- Availability parsing failures are dropped because a boolean value cannot be meaningfully median-imputed.
- Currency conversion uses the required fixed project constant: **1 GBP = 105.50 INR**.
- SQLite is normalized into `categories` and `books`, linked by `category_id`.
- SQL results are written to `sql_outputs.md`. The JOIN result is reproduced with `pd.merge()` and checked for equality.

## Run

From the repository root:

```bash
pip install -r data_pipeline/requirements.txt
python data_pipeline/scrape_pipeline.py
```

Generated files:

- `raw_books.csv`
- `cleaned_books.csv`
- `books.db`
- `sql_outputs.md`
