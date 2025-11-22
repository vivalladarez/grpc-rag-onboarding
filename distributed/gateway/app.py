"""
API FastAPI Gateway Distribuído
Porta: 8002
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from rag_client import get_client

app = FastAPI(title="RAG Distributed Gateway", version="1.0.0")


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class IngestRequest(BaseModel):
    directory_path: str


@app.get("/")
def root():
    return {"message": "RAG Distributed Gateway", "mode": "distributed"}


@app.get("/health")
def health():
    try:
        client = get_client()
        stats = client.get_stats()
        return {
            "status": "healthy",
            "mode": "distributed",
            "documents": stats.get("total_documents", 0)
        }
    except:
        return {"status": "unhealthy", "mode": "distributed"}


@app.post("/query")
def query(request: QueryRequest):
    try:
        client = get_client()
        result = client.answer(request.query, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
def ingest(request: IngestRequest):
    try:
        client = get_client()
        result = client.ingest_documents(directory_path=request.directory_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    client = get_client()
    return client.get_stats()


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando Gateway Distribuído na porta 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)

