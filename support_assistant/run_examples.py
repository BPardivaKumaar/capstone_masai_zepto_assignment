"""Call a locally running FastAPI service and save the required raw JSON examples."""

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "example_responses.md"
URL = "http://127.0.0.1:7860/ask"

EXAMPLES = [
    ("Policy / retrieval", "What is the delivery fee for an order below INR 149?"),
    ("General / direct", "What is the capital of France?"),
]


def main() -> None:
    lines = ["# FastAPI Example Calls", "", "These calls were run with `MOCK_LLM` left at its default.", ""]
    for label, query in EXAMPLES:
        response = requests.post(URL, json={"query": query}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        print(f"\n--- {label} ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        lines.extend(
            [
                f"## {label}",
                "",
                f"Request: `POST /ask` with `{{\"query\": \"{query}\"}}`",
                "",
                "```json",
                json.dumps(payload, indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved responses to {OUTPUT}")


if __name__ == "__main__":
    main()
