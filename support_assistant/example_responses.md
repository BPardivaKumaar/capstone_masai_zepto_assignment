# FastAPI Example Calls

These calls were run with `MOCK_LLM` left at its default.

## Policy / retrieval

Request: `POST /ask` with `{"query": "What is the delivery fee for an order below INR 149?"}`

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard del",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_07"
  ],
  "confidence": 1.0
}
```

## General / direct

Request: `POST /ask` with `{"query": "What is the capital of France?"}`

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```
