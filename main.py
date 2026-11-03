from fastapi import FastAPI

app = FastAPI(
    title="Local RAG Security Lab",
    description="A local lab for evaluating RAG security controls.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}