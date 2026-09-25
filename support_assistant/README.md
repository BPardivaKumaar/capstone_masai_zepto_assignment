# Module 3 - Support Assistant

This module implements a local RAG service using the exact eight policy documents supplied by the assignment, Sentence Transformers embeddings, ChromaDB, LangGraph, Pydantic, FastAPI, and a Dockerfile.

## Required baseline

`MOCK_LLM` defaults to enabled. Leave it unset for grading. In that mode:

- intent classification uses the required keyword heuristic;
- policy questions still use real local embedding + ChromaDB retrieval;
- policy answers use the required deterministic `Based on the retrieved context: ...` template;
- general questions use the fixed canned response;
- Pydantic validates the final `answer`, `sources`, and `confidence` fields.

No LLM API key is required for the baseline.

## Run locally

```bash
pip install -r support_assistant/requirements.txt
python support_assistant/build_index.py
uvicorn support_assistant.main:app --host 127.0.0.1 --port 7860
```

In a second VS Code terminal:

```bash
python support_assistant/run_examples.py
```

The script records the raw JSON responses in `support_assistant/example_responses.md`.

## Docker

From inside `support_assistant`:

```bash
docker build -t zepto-support .
docker run --rm -p 7860:7860 zepto-support
```

Then call `POST http://127.0.0.1:7860/ask`.

## Architecture - ingestion -> embedding -> retrieval -> generation

```text
8 policy .txt files
      |
      v
build_index.py
  ingestion / per-document chunking
      |
      v
SentenceTransformer(all-MiniLM-L6-v2)
  local 384-d embeddings
      |
      v
ChromaDB collection: zepto_policies
      |
      v
LangGraph: classify_intent
      |------------------------------|
      | policy_question               | general_question
      v                              v
retrieve_and_answer             direct_answer
      |                              |
      v                              v
top-3 cosine retrieval          canned/optional direct LLM
      |
      v
mock answer or structured LLM generation
      |
      v
Pydantic: {answer, sources, confidence}
      |
      v
FastAPI POST /ask
```

Ingestion and embedding are handled by `build_index.py`. Retrieval is handled by `PolicyRetriever.search()` inside `retrieve_and_answer`. The structured prompt is in `prompt_template.py`. Only classification/generation branches on `MOCK_LLM`; the ChromaDB retrieval step is always real in both modes.

## Optional real LLM extension

Set `MOCK_LLM=0` and provide `GROQ_API_KEY`. The code uses an OpenAI-compatible Groq HTTP endpoint. The generation path validates the JSON output with Pydantic and retries up to three total attempts when the output does not validate.
