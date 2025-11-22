"""
API FastAPI Monolítica
Porta: 8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path

# Adicionar path para acessar módulo shared
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_pipeline import get_pipeline
from shared.path_utils import resolve_directory_path

app = FastAPI(title="RAG Monolithic API", version="1.0.0")


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class IngestRequest(BaseModel):
    directory_path: str


@app.get("/")
def root():
    return {"message": "RAG Monolithic API", "mode": "monolithic"}


@app.get("/health")
def health():
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "mode": "monolithic",
        "documents": pipeline.vector_db.get_document_count(),
        "ollama": pipeline.llm.check_connection()
    }


@app.post("/query")
def query(request: QueryRequest):
    try:
        pipeline = get_pipeline()
        result = pipeline.answer(request.query, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
def ingest(request: IngestRequest):
    try:
        pipeline = get_pipeline()
        directory = resolve_directory_path(request.directory_path)
        result = pipeline.ingest_documents(directory_path=str(directory))
        return result
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
def reset():
    try:
        pipeline = get_pipeline()
        result = pipeline.reset()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    pipeline = get_pipeline()
    return pipeline.get_stats()


if __name__ == "__main__":
    import uvicorn
    print("\nIniciando API Monolítica na porta 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)

