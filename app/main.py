import logging

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import Principal, get_principal
from app.rag import answer_question
from app.ui import router as ui_router
from app.payment_api import router as payment_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local RAG Security Lab",
    description="A local lab for evaluating RAG security controls.",
    version="0.1.0",
)
app.include_router(ui_router)
app.include_router(payment_router)

MODEL = "optimized-gemma:latest"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=4000)


class GenerationResponse(BaseModel):
    model: str
    answer: str


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=4000)


class RetrievedSource(BaseModel):
    document_id: str
    source: str
    access_level: str


class QueryResponse(BaseModel):
    mode: str
    model: str
    answer: str
    sources: list[RetrievedSource]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return {
        "user_id": principal.user_id,
        "role": principal.role,
    }


@app.post(
    "/generate",
    response_model=GenerationResponse,
    dependencies=[Depends(get_principal)],
)
async def generate(request: GenerationRequest):
    if not request.prompt.strip():
        raise HTTPException(
            status_code=422,
            detail="Prompt must contain text.",
        )

    payload = {
        "model": MODEL,
        "system": "Answer clearly and concisely.",
        "prompt": request.prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_ctx": 4096,
            "num_predict": 256,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        answer = data["response"]

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Invalid model response.")

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Local model request timed out.",
        ) from None

    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Could not obtain a valid local model response.",
        ) from None

    return GenerationResponse(
        model=MODEL,
        answer=answer.strip(),
    )


@app.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    principal: Principal = Depends(get_principal),
):
    if not request.question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question must contain text.",
        )

    try:
        return answer_question(request.question, principal)

    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Document access denied.",
        ) from None

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Local RAG request timed out.",
        ) from None

    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        logger.exception("Local RAG query failed.")

        raise HTTPException(
            status_code=502,
            detail="Could not complete the local RAG request.",
        ) from None
