"""
Módulo de Embeddings - Código Compartilhado
"""

from sentence_transformers import SentenceTransformer
from typing import List
import os


class EmbeddingModel:
    """Classe para gerar embeddings usando SentenceTransformer"""
    
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-small')
        
        print(f"📦 Carregando modelo: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print("✅ Modelo carregado!")
    
    def embed_query(self, query: str) -> List[float]:
        """Gera embedding para query"""
        if 'e5' in self.model_name.lower():
            query = f"query: {query}"
        return self.model.encode(query, convert_to_tensor=False).tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos textos"""
        if 'e5' in self.model_name.lower():
            texts = [f"passage: {text}" for text in texts]
        embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]
    
    def get_dimension(self) -> int:
        """Retorna dimensão dos embeddings"""
        return self.model.get_sentence_embedding_dimension()

