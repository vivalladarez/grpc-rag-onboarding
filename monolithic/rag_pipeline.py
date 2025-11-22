"""
Pipeline RAG Monolítico
Tudo em um único processo
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.embeddings import EmbeddingModel
from shared.vectordb import VectorDB
from shared.llm import OllamaLLM
from shared.ingest import process_documents_for_ingestion
from typing import List, Dict, Any
import os


class RAGMonolithicPipeline:
    """Pipeline RAG Monolítico - Tudo em um processo"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("🏗️  INICIALIZANDO PIPELINE MONOLÍTICO")
        print("="*60)
        
        self.embedding_model = EmbeddingModel()
        self.vector_db = VectorDB()
        self.llm = OllamaLLM()
        
        self.top_k = int(os.getenv('TOP_K_RESULTS', '5'))
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '2000'))
        
        print("="*60)
        print("✅ PIPELINE MONOLÍTICO PRONTO!")
        print("="*60 + "\n")
    
    def ingest_documents(self, file_paths: List[str] = None, 
                        directory_path: str = None) -> Dict[str, Any]:
        """Ingere documentos"""
        print("\n📥 Ingestão Monolítica")
        
        texts, metadatas = process_documents_for_ingestion(file_paths, directory_path)
        
        if not texts:
            return {"status": "error", "message": "Nenhum documento"}
        
        embeddings = self.embedding_model.embed_texts(texts)
        self.vector_db.add_documents(texts, embeddings, metadatas)
        
        return {
            "status": "success",
            "chunks_added": len(texts),
            "total_documents": self.vector_db.get_document_count()
        }
    
    def answer(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """Responde pergunta"""
        if top_k is None:
            top_k = self.top_k
        
        print("\n" + "="*60)
        print(f"💬 QUERY MONOLÍTICA: {query}")
        print("="*60)
        
        # 1. Gerar embedding da query
        query_embedding = self.embedding_model.embed_query(query)
        
        # 2. Buscar documentos
        results = self.vector_db.query(query_embedding, top_k)
        
        documents = []
        if results['documents'] and len(results['documents']) > 0:
            docs = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
            distances = results['distances'][0] if results['distances'] else [0] * len(docs)
            
            for i, doc in enumerate(docs):
                documents.append({
                    'text': doc,
                    'metadata': metadatas[i],
                    'score': 1 - distances[i],
                    'rank': i + 1
                })
        
        if not documents:
            return {
                "query": query,
                "answer": "Nenhum documento encontrado",
                "sources": [],
                "context_used": 0,
                "mode": "monolithic"
            }
        
        # 3. Construir prompt
        context_parts = []
        for doc in documents:
            source = doc['metadata'].get('source', 'Desconhecido')
            context_parts.append(f"[Fonte: {source}]\n{doc['text']}")
        
        context = "\n\n---\n\n".join(context_parts)
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "..."
        
        prompt = f"""Você é um assistente de onboarding corporativo.

CONTEXTO:
{context}

PERGUNTA: {query}

INSTRUÇÕES:
- Use APENAS as informações do contexto
- Seja claro e objetivo
- Cite as fontes

RESPOSTA:"""
        
        # 4. Gerar resposta
        answer_text = self.llm.generate(prompt)
        
        # 5. Preparar resposta
        sources = []
        for doc in documents:
            sources.append({
                'source': doc['metadata'].get('source', 'Desconhecido'),
                'score': round(doc['score'], 4),
                'excerpt': doc['text'][:150] + "..."
            })
        
        print("="*60)
        print("✅ RESPOSTA GERADA (MONOLÍTICO)")
        print("="*60 + "\n")
        
        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "context_used": len(documents),
            "mode": "monolithic",
            "architecture": "monolithic"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        return {
            "total_documents": self.vector_db.get_document_count(),
            "embedding_model": self.embedding_model.model_name,
            "llm_model": self.llm.model,
            "mode": "monolithic"
        }
    
    def reset(self) -> Dict[str, Any]:
        """Reseta banco"""
        self.vector_db.reset_collection()
        return {"status": "success", "message": "Resetado"}


# Singleton
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGMonolithicPipeline()
    return _pipeline

