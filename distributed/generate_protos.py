"""
Script para gerar código Python dos arquivos .proto
Execute: python generate_protos.py
"""

import subprocess
from pathlib import Path

PROTO_DIR = Path("protos")
OUTPUT_DIR = Path("generated")

OUTPUT_DIR.mkdir(exist_ok=True)

proto_files = ["embedding_service.proto", "vector_service.proto", "llm_service.proto"]

print("🔧 Gerando código Python dos .proto...")

for proto_file in proto_files:
    proto_path = PROTO_DIR / proto_file
    print(f"   Processando {proto_file}...")
    
    cmd = [
        "python", "-m", "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUTPUT_DIR}",
        f"--grpc_python_out={OUTPUT_DIR}",
        str(proto_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ {proto_file} gerado")
    else:
        print(f"   ❌ Erro: {result.stderr}")

(OUTPUT_DIR / "__init__.py").touch()

print("\n✅ Geração concluída!")

