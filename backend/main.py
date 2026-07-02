from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from rag_pipeline import main_chain

app = FastAPI(title="VERITAS RAG API")


@app.get("/", include_in_schema=False)
def root():
    # This is an API, not a webpage -- send anyone who opens it in a
    # browser to the interactive docs instead of a bare 404.
    return RedirectResponse(url="/docs")

# Tighten allow_origins to your actual deployed frontend domain before
# sharing this link publicly -- "*" is fine for local dev only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    # Local/Ollama mode was removed from the UI for now -- this pipeline only
    # runs the Gemini cloud chain. Re-add a model_mode field here (and a
    # branch below) once a local chain actually exists in rag_pipeline.py.


@app.post("/ask")
def ask(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = main_chain.invoke(query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {exc}")

    return {"answer": result["answer"], "sources": result["sources"]}


@app.get("/health")
def health():
    return {"status": "ok"}