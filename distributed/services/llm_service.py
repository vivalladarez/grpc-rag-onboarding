"""
LLM Service gRPC
Porta: 50053
"""

import grpc
from concurrent import futures
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "generated"))

from generated import llm_service_pb2, llm_service_pb2_grpc
from shared.llm import OllamaLLM


class LLMServicer(llm_service_pb2_grpc.LLMServiceServicer):
    def __init__(self):
        self.llm = OllamaLLM()
        print("LLM Service inicializado.")
    
    def Generate(self, request, context):
        try:
            print(f"Generate solicitado com {len(request.prompt)} caracteres")
            temp = request.temperature if request.temperature > 0 else 0.7
            text = self.llm.generate(request.prompt, temp)
            return llm_service_pb2.GenerateResponse(text=text)
        except Exception as e:
            print(f"Erro durante Generate: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return llm_service_pb2.GenerateResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    llm_service_pb2_grpc.add_LLMServiceServicer_to_server(
        LLMServicer(), server
    )
    server.add_insecure_port('[::]:50053')
    server.start()
    
    print("\n" + "="*60)
    print("LLM Service rodando (gRPC)")
    print("="*60)
    print("   Porta: 50053")
    print("="*60 + "\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nParando LLM Service...")


if __name__ == '__main__':
    serve()

