"""LangGraph RAG workflow with deterministic mock mode."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import chromadb
import requests
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph

from support_assistant.build_index import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    build_index,
)
from .prompt_template import build_general_prompt, build_policy_prompt

ROOT = Path(__file__).resolve().parent
KEYWORDS = [
    "delivery",
    "return",
    "refund",
    "membership",
    "tracking",
    "cancel",
    "gift card",
    "support hours",
]

CANNED_GENERAL = "I can only answer questions about Zepto policies right now."


class SupportResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class SupportState(TypedDict, total=False):
    query: str
    intent: Literal["policy_question", "general_question"]
    retrieved: list[dict[str, Any]]
    answer: str
    response: dict[str, Any]


class PolicyRetriever:
    """Owns the local embedding model and Chroma collection."""

    def __init__(self) -> None:
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            self.collection = self.client.get_collection(COLLECTION_NAME)
        except Exception:
            build_index()
            self.collection = self.client.get_collection(COLLECTION_NAME)

        if self.collection.count() < 8:
            build_index()
            self.collection = self.client.get_collection(COLLECTION_NAME)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        embedding = self.model.encode([query], normalize_embeddings=True)[0].tolist()
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        retrieved = []
        for i, document in enumerate(documents):
            source = (metadatas[i] or {}).get("source", f"chunk_{i+1}")
            retrieved.append(
                {
                    "id": source,
                    "document": document,
                    "distance": float(distances[i]) if i < len(distances) else None,
                }
            )
        return retrieved


_resources: PolicyRetriever | None = None


def get_retriever() -> PolicyRetriever:
    global _resources
    if _resources is None:
        _resources = PolicyRetriever()
    return _resources


def mock_mode() -> bool:
    return os.getenv("MOCK_LLM", "1") != "0"


def classify_mock(query: str) -> Literal["policy_question", "general_question"]:
    lower = query.lower()
    return "policy_question" if any(keyword in lower for keyword in KEYWORDS) else "general_question"


def groq_chat(prompt: str, system_message: str) -> str:
    """Optional real-LLM extension using Groq's OpenAI-compatible endpoint."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("MOCK_LLM=0 requires GROQ_API_KEY for the optional real-LLM path.")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def generate_validated_real_answer(prompt: str, source_ids: list[str]) -> SupportResponse:
    """Try the real LLM up to three total attempts, correcting schema errors."""
    last_error = "unknown error"
    corrective = ""
    for attempt in range(4):
        full_prompt = prompt + ("\n\nCORRECTION: Return valid JSON matching the required schema." if corrective else "")
        try:
            raw = groq_chat(
                full_prompt,
                "You are a strict JSON API. Follow the requested schema exactly and use only supplied policy context.",
            )
            candidate = SupportResponse.model_validate(parse_json(raw))
            # Sources are constrained to retrieved IDs for a grounded answer.
            if source_ids:
                candidate.sources = [source for source in candidate.sources if source in source_ids]
            return candidate
        except Exception as exc:  # noqa: BLE001 - retry path intentionally catches validation/API errors
            last_error = str(exc)
            corrective = "1"

    return SupportResponse(
        answer=f"ERROR: real-LLM output failed schema validation after 3 attempts: {last_error}",
        sources=source_ids,
        confidence=0.0,
    )


def classify_intent(state: SupportState) -> dict[str, Any]:
    query = state["query"]
    if mock_mode():
        intent = classify_mock(query)
    else:
        raw = groq_chat(
            "Classify this query as exactly one label: policy_question or general_question.\n\n"
            f"Query: {query}\n\nReturn only the label.",
            "You classify queries for a Zepto policy assistant.",
        ).strip().lower()
        if "policy_question" in raw:
            intent = "policy_question"
        elif "general_question" in raw:
            intent = "general_question"
        else:
            intent = classify_mock(query)
    return {"intent": intent}


def retrieve_and_answer(state: SupportState) -> dict[str, Any]:
    query = state["query"]
    retrieved = get_retriever().search(query, top_k=3)
    source_ids = [item["id"] for item in retrieved]
    top_snippet = retrieved[0]["document"][:200] if retrieved else "No matching policy context was found."

    if mock_mode():
        response = SupportResponse(
            answer=f"Based on the retrieved context: {top_snippet}",
            sources=source_ids,
            confidence=1.0,
        )
    else:
        context = "\n\n".join(
            f"[{item['id']}] {item['document']}" for item in retrieved
        )
        response = generate_validated_real_answer(
            build_policy_prompt(query, context), source_ids
        )

    return {
        "retrieved": retrieved,
        "answer": response.answer,
        "response": response.model_dump(),
    }


def direct_answer(state: SupportState) -> dict[str, Any]:
    query = state["query"]
    if mock_mode():
        response = SupportResponse(
            answer=CANNED_GENERAL,
            sources=[],
            confidence=1.0,
        )
    else:
        response = generate_validated_real_answer(build_general_prompt(query), [])

    return {"answer": response.answer, "response": response.model_dump()}


def route_after_classify(state: SupportState) -> Literal["retrieve_and_answer", "direct_answer"]:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    builder = StateGraph(SupportState)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("retrieve_and_answer", retrieve_and_answer)
    builder.add_node("direct_answer", direct_answer)
    builder.add_edge(START, "classify_intent")
    builder.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )
    builder.add_edge("retrieve_and_answer", END)
    builder.add_edge("direct_answer", END)
    return builder.compile()


graph = build_graph()


def ask(query: str) -> SupportResponse:
    state = graph.invoke({"query": query})
    return SupportResponse.model_validate(state["response"])
