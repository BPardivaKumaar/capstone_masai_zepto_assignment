"""Zepto Data Pipeline - scrape, clean, convert, load, query, compare."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any ,Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
GBP_TO_INR = 105.50
REQUEST_TIMEOUT = 20

# These three categories together contain well over 60 books.
CATEGORY_URLS = {
    "Travel": "catalogue/category/books/travel_2/index.html",
    "Mystery": "catalogue/category/books/mystery_3/index.html",
    "Fiction": "catalogue/category/books/fiction_10/index.html",
}

ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / "raw_books.csv"
CLEAN_CSV = ROOT / "cleaned_books.csv"
DB_PATH = ROOT / "books.db"
SQL_OUTPUT = ROOT / "sql_outputs.md"

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def request_page(session: requests.Session, url: str) -> BeautifulSoup:
    """Fetch a page and fail with a useful error for non-2xx responses."""
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0 Zepto-Capstone-Scraper/1.0"},
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape_category(session: requests.Session, category: str, relative_url: str) -> list[dict[str, Any]]:
    """Scrape every pagination page for one category."""
    rows: list[dict[str, Any]] = []
    next_url = urljoin(BASE_URL, relative_url)
    page_number = 1

    while next_url:
        soup = request_page(session, next_url)
        products = soup.select("article.product_pod")

        for product in products:
            title_link = product.select_one("h3 a")
            price_node = product.select_one("p.price_color")
            rating_node = product.select_one("p.star-rating")
            availability_node = product.select_one("p.instock.availability")

            rows.append(
                {
                    "title": title_link.get("title", "").strip() if title_link else "",
                    "price": price_node.get_text(" ", strip=True) if price_node else "",
                    "star_rating": (
                        rating_node.get("class", ["", ""])[1]
                        if rating_node and len(rating_node.get("class", [])) > 1
                        else ""
                    ),
                    "availability": (
                        availability_node.get_text(" ", strip=True) if availability_node else ""
                    ),
                    "category": category,
                }
            )

        next_link = soup.select_one("li.next a")
        next_url = urljoin(next_url, next_link.get("href")) if next_link else ""
        page_number += 1

    return rows


def scrape_all_books() -> pd.DataFrame:
    """Scrape at least three categories without manual copy-paste."""
    with requests.Session() as session:
        rows: list[dict[str, Any]] = []
        for category, path in CATEGORY_URLS.items():
            category_rows = scrape_category(session, category, path)
            print(f"Scraped {len(category_rows):>3} books from {category}")
            rows.extend(category_rows)

    df = pd.DataFrame(rows)
    if len(df) < 60 or df["category"].nunique() < 3:
        raise RuntimeError(
            f"Scrape scope is too small: {len(df)} rows across {df['category'].nunique()} categories."
        )
    return df


def parse_in_stock(value: Any) -> Optional[bool]:
    text = str(value).strip().lower()
    if "in stock" in text:
        return True
    if "out of stock" in text:
        return False
    return None


def clean_books(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean types and handle malformed rows defensibly."""
    df = raw.copy()

    # Required text fields: malformed/empty rows are dropped.
    for col in ["title", "category"]:
        df[col] = df[col].astype("string").str.strip()
    df = df[df["title"].notna() & df["category"].notna()]
    df = df[(df["title"] != "") & (df["category"] != "")]

    # Numeric fields: parse failures become NaN and are median-imputed.
    df["price_gbp"] = (
        df["price"]
        .astype("string")
        .str.replace("Â£", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
    )
    df["rating"] = df["star_rating"].map(RATING_MAP).astype("Float64")

    for numeric_col in ["price_gbp", "rating"]:
        median_value = df[numeric_col].median()
        df[numeric_col] = df[numeric_col].fillna(median_value)

    # Non-numeric parsing failures cannot be median-imputed, so drop those rows.
    df["in_stock"] = df["availability"].map(parse_in_stock).astype("boolean")
    before_stock_drop = len(df)
    df = df.dropna(subset=["in_stock"])
    stock_drop_count = before_stock_drop - len(df)

    df["rating"] = df["rating"].round().astype(int)
    df["price_gbp"] = df["price_gbp"].astype(float)
    df["in_stock"] = df["in_stock"].astype(bool)
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)

    result = df[
        ["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]
    ].reset_index(drop=True)

    if stock_drop_count:
        print(f"Dropped {stock_drop_count} rows with unparseable availability text.")
    return result


def create_database(cleaned: pd.DataFrame) -> None:
    """Create a normalized SQLite schema and load the cleaned data."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE books (
                book_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                price_gbp REAL NOT NULL,
                price_inr REAL NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                in_stock INTEGER NOT NULL CHECK (in_stock IN (0, 1)),
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            );
            """
        )

        categories = sorted(cleaned["category"].unique().tolist())
        conn.executemany(
            "INSERT INTO categories(category_name) VALUES (?)",
            [(name,) for name in categories],
        )

        category_map = {
            name: category_id
            for category_id, name in conn.execute(
                "SELECT category_id, category_name FROM categories"
            ).fetchall()
        }

        book_rows = [
            (
                row.title,
                float(row.price_gbp),
                float(row.price_inr),
                int(row.rating),
                int(row.in_stock),
                category_map[row.category],
            )
            for row in cleaned.itertuples(index=False)
        ]
        conn.executemany(
            """
            INSERT INTO books(title, price_gbp, price_inr, rating, in_stock, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            book_rows,
        )
        conn.commit()


def run_queries() -> None:
    """Execute six required SQL examples and store outputs as Markdown."""
    queries = {
        "1. SELECT + WHERE": """
            SELECT title, price_inr, rating
            FROM books
            WHERE rating >= 4
            ORDER BY rating DESC, title
            LIMIT 10;
        """,
        "2. ORDER BY + LIMIT": """
            SELECT title, price_inr
            FROM books
            ORDER BY price_inr DESC
            LIMIT 10;
        """,
        "3. DISTINCT": """
            SELECT DISTINCT category_name
            FROM categories
            ORDER BY category_name;
        """,
        "4. BETWEEN": """
            SELECT title, price_gbp
            FROM books
            WHERE price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp;
        """,
        "5. IN": """
            SELECT title, category_id, rating
            FROM books
            WHERE category_id IN (1, 2, 3)
            ORDER BY rating DESC, title
            LIMIT 10;
        """,
        "6. JOIN": """
            SELECT c.category_name, b.title, b.rating, b.price_inr
            FROM books AS b
            JOIN categories AS c ON b.category_id = c.category_id
            ORDER BY b.rating DESC, b.price_inr DESC, b.title
            LIMIT 10;
        """,
    }

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        outputs: dict[str, pd.DataFrame] = {}
        for name, query in queries.items():
            outputs[name] = pd.read_sql_query(query, conn)

        sql_join = outputs["6. JOIN"].copy()

        books_df = pd.read_sql_query(
            "SELECT title, rating, price_inr, category_id FROM books", conn
        )
        categories_df = pd.read_sql_query(
            "SELECT category_id, category_name FROM categories", conn
        )

    pandas_join = (
        books_df.merge(categories_df, on="category_id", how="inner")
        [["category_name", "title", "rating", "price_inr"]]
        .sort_values(["rating", "price_inr", "title"], ascending=[False, False, True])
        .head(10)
        .reset_index(drop=True)
    )
    sql_join = sql_join.reset_index(drop=True)

    equivalent = sql_join.equals(pandas_join)

    lines = [
        "# SQL Query Outputs",
        "",
        f"Fixed currency baseline: **1 GBP = {GBP_TO_INR:.2f} INR**",
        "",
    ]

    for name, query in queries.items():
        lines.extend([
            f"## {name}",
            "```sql",
            query.strip(),
            "```",
            "",
            outputs[name].to_markdown(index=False),
            "",
        ])

    lines.extend([
        "## JOIN: SQL vs pandas.merge",
        "",
        "### SQL `pd.read_sql` result",
        sql_join.to_markdown(index=False),
        "",
        "### pandas `pd.merge` result",
        pandas_join.to_markdown(index=False),
        "",
        f"**Equivalent output:** `{equivalent}`",
        "",
    ])
    SQL_OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    if not equivalent:
        raise AssertionError("SQL JOIN and pandas.merge results do not match.")


def main() -> None:
    print("Starting data pipeline...")
    raw = scrape_all_books()
    raw.to_csv(RAW_CSV, index=False)
    print(f"Saved raw data: {RAW_CSV}")

    cleaned = clean_books(raw)
    cleaned.to_csv(CLEAN_CSV, index=False)
    print(f"Saved cleaned data: {CLEAN_CSV}")

    create_database(cleaned)
    print(f"Saved SQLite database: {DB_PATH}")

    run_queries()
    print(f"Saved SQL outputs: {SQL_OUTPUT}")
    print(f"Final cleaned rows: {len(cleaned)} across {cleaned['category'].nunique()} categories")


if __name__ == "__main__":
    main()
