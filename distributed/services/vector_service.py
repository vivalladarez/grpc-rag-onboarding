"""
Vector Service gRPC
Porta: 50052
"""

import grpc
from concurrent import futures
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "generated"))

from generated import vector_service_pb2, vector_service_pb2_grpc
from shared.vectordb import VectorDB


class VectorServicer(vector_service_pb2_grpc.VectorServiceServicer):
    def __init__(self):
        self.vector_db = VectorDB()
        print("Vector Service inicializado.")
    
    def Search(self, request, context):
        try:
            query_embedding = list(request.query_embedding)
            top_k = request.top_k if request.top_k > 0 else 5
            
            print(f"Search solicitado com top_k={top_k}")
            results = self.vector_db.query(query_embedding, top_k)
            
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
                distances = results['distances'][0] if results['distances'] else [0] * len(docs)
                
                for i, doc in enumerate(docs):
                    documents.append(vector_service_pb2.Document(
                        text=doc,
                        metadata=metadatas[i],
                        score=1 - distances[i]
                    ))
            
            return vector_service_pb2.SearchResponse(documents=documents)
        except Exception as e:
            print(f"Erro durante Search: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return vector_service_pb2.SearchResponse()
    
    def AddDocuments(self, request, context):
        try:
            texts = list(request.texts)
            embeddings = [list(emb.values) for emb in request.embeddings]
            metadatas = [dict(meta.data) for meta in request.metadatas]
            
            print(f"AddDocuments recebido com {len(texts)} documentos")
            self.vector_db.add_documents(texts, embeddings, metadatas)
            
            return vector_service_pb2.AddDocumentsResponse(
                documents_added=len(texts),
                total_documents=self.vector_db.get_document_count()
            )
        except Exception as e:
            print(f"Erro durante AddDocuments: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return vector_service_pb2.AddDocumentsResponse()
    
    def GetCount(self, request, context):
        try:
            count = self.vector_db.get_document_count()
            return vector_service_pb2.CountResponse(count=count)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return vector_service_pb2.CountResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vector_service_pb2_grpc.add_VectorServiceServicer_to_server(
        VectorServicer(), server
    )
    server.add_insecure_port('[::]:50052')
    server.start()
    
    print("\n" + "="*60)
    print("Vector Service rodando (gRPC)")
    print("="*60)
    print("   Porta: 50052")
    print("="*60 + "\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nParando Vector Service...")


if __name__ == '__main__':
    serve()

