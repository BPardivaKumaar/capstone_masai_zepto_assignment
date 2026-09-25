# Zepto Data analysis & AI Platform - Capstone Submission

This repository is one connected project with three modules required by the assignment:

```text
zepto-assignment/
├── README.md
├── data_pipeline/
│   ├── scrape_pipeline.py
│   ├── requirements.txt
│   └── README.md
├── analytics/
│   ├── 01_eda.py
│   ├── 02_modeling.py
│   ├── reload_pipeline.py
│   ├── requirements.txt
│   ├── README.md
│   ├── titanic.csv              # generated/updated by 01_eda.py
│   ├── outputs/
│   └── artifacts/
└── support_assistant/
    ├── docs/
    ├── build_index.py
    ├── prompt_template.py
    ├── rag.py
    ├── main.py
    ├── run_examples.py
    ├── requirements.txt
    ├── Dockerfile
    └── README.md
```

The assignment requires exactly one public GitHub repository, a root README, all three folders, reproducible run instructions, and a visible feature-branch/merge workflow in Git history. fileciteturn0file0L9-L17

## 1. Setup in VS Code

Use Python 3.11 for the cleanest compatibility across the three modules.

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install each module's requirements:

```powershell
pip install -r data_pipeline\requirements.txt
pip install -r analytics\requirements.txt
pip install -r support_assistant\requirements.txt
```

Keeping requirements per module avoids forcing unrelated dependencies into every environment.

## 2. Module 1 - Data Pipeline

The assignment requires `requests` + `BeautifulSoup`, at least 60 books across at least 3 categories, type cleaning, the fixed 1 GBP = 105.50 INR conversion, a normalized two-table SQLite schema, at least five SQL queries covering the specified clauses, a JOIN, and a pandas `read_sql` / `merge` comparison. fileciteturn0file0L27-L50

Run:

```powershell
python data_pipeline\scrape_pipeline.py
```

Expected generated files:

- `data_pipeline/raw_books.csv`
- `data_pipeline/cleaned_books.csv`
- `data_pipeline/books.db`
- `data_pipeline/sql_outputs.md`

The scraper follows pagination automatically for Travel, Mystery, and Fiction.

## 3. Module 2 - Analytics Pipeline

The assignment requires one Titanic load, missing-value thresholds, EDA, the exact six-column correlation matrix, multivariate charts and interpretations, train-only preprocessing, three classifiers, full metrics, imbalance comparison, GridSearchCV with OOB score, fare regression, a separate metric group for regression, and a reloadable complete joblib pipeline. fileciteturn0file0L59-L85

Run in this order:

```powershell
python analytics\01_eda.py
python analytics\02_modeling.py
python analytics\reload_pipeline.py
```

`01_eda.py` performs the one `sns.load_dataset('titanic')` call and creates the offline `titanic.csv` continuation file. `02_modeling.py` reads that same file and does not make another network dataset call.

Generated material is placed under:

- `analytics/outputs/`
- `analytics/artifacts/best_pipeline.joblib`

The acceptance criteria for this module are summarized in the assignment's lines 88-102. fileciteturn0file0L88-L102

## 4. Module 3 - Support Assistant

The assignment requires eight exact policy documents, local Sentence Transformers embeddings with `all-MiniLM-L6-v2`, ChromaDB, a structured prompt, a three-node LangGraph state graph with conditional routing, deterministic `MOCK_LLM` behavior, a Pydantic response schema, FastAPI, Docker, two example calls, and a written RAG architecture description. fileciteturn0file0L110-L118 fileciteturn0file0L142-L165

Build the local index:

```powershell
python support_assistant\build_index.py
```

Start the API:

```powershell
uvicorn support_assistant.main:app --host 127.0.0.1 --port 7860
```

In a second VS Code terminal:

```powershell
python support_assistant\run_examples.py
```

Required baseline behavior uses `MOCK_LLM` by default. Do not set it for grading.

### Test the endpoint manually

Request:

```http
POST http://127.0.0.1:7860/ask
Content-Type: application/json

{"query":"What is the delivery fee for an order below INR 149?"}
```

The response schema is:

```json
{
  "answer": "...",
  "sources": ["doc_01", "doc_02"],
  "confidence": 1.0
}
```

### Docker

From `support_assistant`:

```powershell
docker build -t zepto-support .
docker run --rm -p 7860:7860 zepto-support
```

The Dockerfile builds the local vector index during the image build and starts Uvicorn on port 7860.

## 5. Git workflow required by the assignment

The assignment checks the repository history for a feature branch with at least two commits and a merge back into `main`. fileciteturn0file0L15-L16

Use a simple workflow like this after creating the repository:

```powershell
git init
git add .
git commit -m "chore: initialize capstone structure"
git branch -M main

git checkout -b feature/zepto-platform
git add .
git commit -m "feat: implement data pipeline"
git add .
git commit -m "feat: implement analytics and support assistant"

git checkout main
git merge --no-ff feature/zepto-platform -m "merge: zepto platform feature"

git log --graph --oneline --decorate --all
```

The history should visibly show the feature branch, at least two feature-branch commits, and a merge commit.

## 6. What is intentionally not included

The assignment does not require screenshots, PDFs, slides, video, or audio. It explicitly requires written interpretations inside Markdown text/notebooks. fileciteturn0file0L11-L14

The optional live LLM and optional cloud deployment are not needed for full marks, so this repository keeps the required baseline offline/mock-first as requested by the specification.

## 7. Suggested final GitHub checklist

Before publishing the repo, run the three modules from a fresh virtual environment, check that generated reports contain real values, verify the FastAPI example responses, review the SQL output, and confirm:

```powershell
git status
git log --graph --oneline --decorate --all
```

Then make the GitHub repository **public** and submit that single repository URL.
