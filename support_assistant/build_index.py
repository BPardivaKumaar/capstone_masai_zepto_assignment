"""Build the local Sentence-Transformers + ChromaDB index."""

from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "zepto_policies"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_documents() -> tuple[list[str], list[str], list[dict[str, str]]]:
    paths = sorted(DOCS_DIR.glob("doc_*.txt"))
    if len(paths) != 8:
        raise RuntimeError(f"Expected exactly 8 policy documents, found {len(paths)}")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    for path in paths:
        ids.append(path.stem)
        documents.append(path.read_text(encoding="utf-8").strip())
        metadatas.append({"source": path.stem})
    return ids, documents, metadatas


def build_index() -> None:
    ids, documents, metadatas = load_documents()
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )
    print(f"Indexed {collection.count()} chunks/documents into '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    build_index()
