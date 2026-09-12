import os
import sys
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Let uvicorn find retriever and verifier when launched from the project root.
sys.path.insert(0, str(Path(__file__).parent))

from retriever import retrieve
from verifier import verify

app = FastAPI(
    title="SGSITS Rulebook Auditor",
    description="Tri-state academic regulation Q&A engine for SGSITS Indore",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent
if (FRONTEND_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 8


class QueryResponse(BaseModel):
    state: str
    answer: str
    citations: list
    conflict_details: Optional[dict]
    confidence: float
    retrieved_passages: list
    question: str


@app.get("/")
async def serve_frontend():
    frontend_path = Path(__file__).parent.parent / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    return {"message": "SGSITS Rulebook Auditor API", "docs": "/docs"}


@app.post("/query", response_model=QueryResponse)
async def query_rulebook(req: QueryRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 chars).")

    passages = retrieve(question, top_k=req.top_k)
    result = verify(question, passages)

    return QueryResponse(
        state=result.get("state", "ERROR"),
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        conflict_details=result.get("conflict_details"),
        confidence=result.get("confidence", 0.0),
        retrieved_passages=[
            {
                "source": p["source"],
                "section": p.get("section_hint", ""),
                "score": p.get("relevance_score", 0),
                "text": p["text"][:400],
            }
            for p in passages
        ],
        question=question,
    )


@app.get("/health")
async def health_check():
    index_path = Path(__file__).parent.parent / "data" / "corpus_index.json"
    index_exists = index_path.exists()
    chunk_count = 0
    if index_exists:
        with open(index_path) as f:
            chunk_count = len(json.load(f))
    return {
        "status": "ok",
        "index_built": index_exists,
        "chunk_count": chunk_count,
        "gemini_api_key_set": bool(os.environ.get("GEMINI_API_KEY")),
    }


@app.get("/corpus")
async def list_corpus():
    rulebook_dir = Path(__file__).parent.parent / "rulebook"
    docs = [
        {"filename": f.name, "size_bytes": f.stat().st_size, "extension": f.suffix}
        for f in sorted(rulebook_dir.glob("*")) if f.is_file()
    ]
    return {"documents": docs, "count": len(docs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
