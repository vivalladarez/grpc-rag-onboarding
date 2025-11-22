"""
Módulo de Vector Database - Código Compartilhado
"""

import chromadb
from typing import List, Dict, Any
import os


class VectorDB:
    """Classe para gerenciar ChromaDB"""
    
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = os.getenv('CHROMA_PERSIST_DIR', './chroma_store')
        
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        print(f"Inicializando ChromaDB em {persist_directory}")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="onboarding_docs",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"ChromaDB pronto. Documentos: {self.collection.count()}")
    
    def add_documents(self, texts: List[str], embeddings: List[List[float]], 
                     metadatas: List[Dict[str, Any]] = None) -> None:
        """Adiciona documentos"""
        import time
        timestamp = int(time.time() * 1000)
        ids = [f"doc_{timestamp}_{i}" for i in range(len(texts))]
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        print(f"Adicionando {len(texts)} documentos ao ChromaDB...")
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("Documentos adicionados com sucesso.")
    
    def query(self, query_embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """Busca vetorial"""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
    
    def get_document_count(self) -> int:
        """Retorna número de documentos"""
        return self.collection.count()
    
    def reset_collection(self) -> None:
        """Reseta coleção"""
        print("Resetando coleção do ChromaDB...")
        self.client.delete_collection(name="onboarding_docs")
        self.collection = self.client.get_or_create_collection(
            name="onboarding_docs",
            metadata={"hnsw:space": "cosine"}
        )
        print("Coleção resetada.")

