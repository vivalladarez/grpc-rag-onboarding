"""
Embedding Service gRPC
Porta: 50051
"""

import grpc
from concurrent import futures
import sys
from pathlib import Path

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "generated"))

from generated import embedding_service_pb2, embedding_service_pb2_grpc
from shared.embeddings import EmbeddingModel


class EmbeddingServicer(embedding_service_pb2_grpc.EmbeddingServiceServicer):
    def __init__(self):
        self.model = EmbeddingModel()
        print(f"✅ Embedding Service pronto!")
    
    def EmbedQuery(self, request, context):
        try:
            print(f"📡 EmbedQuery: {request.text[:50]}...")
            embedding = self.model.embed_query(request.text)
            return embedding_service_pb2.EmbedQueryResponse(embedding=embedding)
        except Exception as e:
            print(f"❌ Erro: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return embedding_service_pb2.EmbedQueryResponse()
    
    def EmbedTexts(self, request, context):
        try:
            texts = list(request.texts)
            print(f"📡 EmbedTexts: {len(texts)} textos")
            embeddings = self.model.embed_texts(texts)
            
            embedding_messages = [
                embedding_service_pb2.Embedding(values=emb)
                for emb in embeddings
            ]
            
            return embedding_service_pb2.EmbedTextsResponse(embeddings=embedding_messages)
        except Exception as e:
            print(f"❌ Erro: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return embedding_service_pb2.EmbedTextsResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    embedding_service_pb2_grpc.add_EmbeddingServiceServicer_to_server(
        EmbeddingServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    
    print("\n" + "="*60)
    print("🟢 EMBEDDING SERVICE RODANDO (gRPC)")
    print("="*60)
    print("   Porta: 50051")
    print("="*60 + "\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n🛑 Parando Embedding Service...")


if __name__ == '__main__':
    serve()

