"""
Cliente gRPC para RAG Distribuído
"""

import grpc
import sys
from pathlib import Path
from typing import List, Dict, Any
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "generated"))

from generated import (
    embedding_service_pb2, embedding_service_pb2_grpc,
    vector_service_pb2, vector_service_pb2_grpc,
    llm_service_pb2, llm_service_pb2_grpc
)
from shared.ingest import process_documents_for_ingestion
from shared.path_utils import resolve_directory_path


class RAGDistributedClient:
    """Cliente para pipeline RAG distribuído via gRPC"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("INICIALIZANDO CLIENTE gRPC DISTRIBUÍDO")
        print("="*60)
        
        # Conectar aos serviços gRPC
        self.embedding_channel = grpc.insecure_channel('localhost:50051')
        self.vector_channel = grpc.insecure_channel('localhost:50052')
        self.llm_channel = grpc.insecure_channel('localhost:50053')
        
        self.embedding_stub = embedding_service_pb2_grpc.EmbeddingServiceStub(self.embedding_channel)
        self.vector_stub = vector_service_pb2_grpc.VectorServiceStub(self.vector_channel)
        self.llm_stub = llm_service_pb2_grpc.LLMServiceStub(self.llm_channel)
        
        self.top_k = int(os.getenv('TOP_K_RESULTS', '5'))
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '2000'))
        
        print("   Embedding Service: localhost:50051")
        print("   Vector Service: localhost:50052")
        print("   LLM Service: localhost:50053")
        print("="*60)
        print("CLIENTE gRPC PRONTO!")
        print("="*60 + "\n")
    
    def ingest_documents(self, file_paths: List[str] = None, 
                        directory_path: str = None) -> Dict[str, Any]:
        """Ingere documentos via gRPC"""
        print("\nIngestão Distribuída (gRPC)")
        
        resolved_directory = None
        if directory_path:
            try:
                resolved_directory = str(resolve_directory_path(directory_path))
            except (FileNotFoundError, NotADirectoryError, ValueError) as e:
                return {"status": "error", "message": str(e)}
        
        texts, metadatas = process_documents_for_ingestion(file_paths, resolved_directory)
        
        if not texts:
            return {"status": "error", "message": "Nenhum documento"}
        
        try:
            # 1. Gerar embeddings via gRPC
            print(f"[gRPC] Gerando embeddings...")
            embed_request = embedding_service_pb2.EmbedTextsRequest(texts=texts)
            embed_response = self.embedding_stub.EmbedTexts(embed_request)
            embeddings = [list(emb.values) for emb in embed_response.embeddings]
            print(f"   {len(embeddings)} embeddings recebidos")
            
            # 2. Adicionar ao vector store via gRPC
            print(f"[gRPC] Adicionando ao vector store...")
            
            embedding_messages = [vector_service_pb2.Embedding(values=emb) for emb in embeddings]
            metadata_messages = [vector_service_pb2.Metadata(data=meta) for meta in metadatas]
            
            add_request = vector_service_pb2.AddDocumentsRequest(
                texts=texts,
                embeddings=embedding_messages,
                metadatas=metadata_messages
            )
            add_response = self.vector_stub.AddDocuments(add_request)
            
            print(f"   {add_response.documents_added} documentos adicionados")
            
            return {
                "status": "success",
                "chunks_added": add_response.documents_added,
                "total_documents": add_response.total_documents
            }
        except grpc.RpcError as e:
            return {"status": "error", "message": f"gRPC Error: {e.code()}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def answer(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """Responde pergunta via gRPC"""
        if top_k is None:
            top_k = self.top_k
        
        print("\n" + "="*60)
        print(f"QUERY DISTRIBUÍDA (gRPC): {query}")
        print("="*60)
        
        try:
            # 1. Gerar embedding da query via gRPC
            print(f"[gRPC] Gerando embedding...")
            embed_request = embedding_service_pb2.EmbedQueryRequest(text=query)
            embed_response = self.embedding_stub.EmbedQuery(embed_request)
            query_embedding = list(embed_response.embedding)
            print(f"   Embedding gerado")
            
            # 2. Buscar documentos via gRPC
            print(f"[gRPC] Buscando documentos...")
            search_request = vector_service_pb2.SearchRequest(
                query_embedding=query_embedding,
                top_k=top_k
            )
            search_response = self.vector_stub.Search(search_request)
            
            documents = []
            for doc in search_response.documents:
                documents.append({
                    'text': doc.text,
                    'metadata': dict(doc.metadata),
                    'score': doc.score
                })
            
            print(f"   {len(documents)} documentos encontrados")
            
            if not documents:
                return {
                    "query": query,
                    "answer": "Nenhum documento encontrado",
                    "sources": [],
                    "context_used": 0,
                    "mode": "distributed"
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
            
            # 4. Gerar resposta via gRPC
            print(f"[gRPC] Gerando resposta...")
            generate_request = llm_service_pb2.GenerateRequest(
                prompt=prompt,
                temperature=0.7
            )
            generate_response = self.llm_stub.Generate(generate_request)
            answer_text = generate_response.text
            print(f"   Resposta gerada")
            
            # 5. Preparar resposta
            sources = []
            for doc in documents:
                sources.append({
                    'source': doc['metadata'].get('source', 'Desconhecido'),
                    'score': round(doc['score'], 4),
                    'excerpt': doc['text'][:150] + "..."
                })
            
            print("="*60)
            print("RESPOSTA GERADA (DISTRIBUÍDO - gRPC)")
            print("="*60 + "\n")
            
            return {
                "query": query,
                "answer": answer_text,
                "sources": sources,
                "context_used": len(documents),
                "mode": "distributed",
                "architecture": "microservices (gRPC)"
            }
        
        except grpc.RpcError as e:
            return {
                "query": query,
                "answer": f"Erro gRPC: {e.code()}",
                "sources": [],
                "context_used": 0,
                "mode": "distributed"
            }
        except Exception as e:
            return {
                "query": query,
                "answer": f"Erro: {str(e)}",
                "sources": [],
                "context_used": 0,
                "mode": "distributed"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas via gRPC"""
        try:
            count_request = vector_service_pb2.CountRequest()
            count_response = self.vector_stub.GetCount(count_request)
            
            return {
                "total_documents": count_response.count,
                "mode": "distributed (gRPC)"
            }
        except:
            return {"total_documents": 0, "mode": "distributed (gRPC - error)"}
    
    def close(self):
        """Fecha canais gRPC"""
        self.embedding_channel.close()
        self.vector_channel.close()
        self.llm_channel.close()


# Singleton
_client = None

def get_client():
    global _client
    if _client is None:
        _client = RAGDistributedClient()
    return _client

