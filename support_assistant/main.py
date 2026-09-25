"""FastAPI wrapper for the Zepto support assistant."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from support_assistant.rag import SupportResponse, ask

app = FastAPI(title="Zepto Policy Support Assistant", version="1.0.0")


class AskRequest(BaseModel):
    query: str = Field(min_length=1)


@app.post("/ask", response_model=SupportResponse)
def ask_endpoint(request: AskRequest) -> SupportResponse:
    return ask(request.query)
