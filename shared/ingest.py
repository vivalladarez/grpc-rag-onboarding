"""
Módulo de Ingestão de Documentos - Código Compartilhado
"""

import os
from pathlib import Path
from typing import List, Tuple, Dict, Any


def read_text_file(file_path: str) -> str:
    """Lê arquivo de texto"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Divide texto em chunks"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start += chunk_size - overlap
    
    return chunks


def process_documents_for_ingestion(
    file_paths: List[str] = None,
    directory_path: str = None
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Processa documentos para ingestão"""
    
    all_texts = []
    all_metadatas = []
    
    # Coletar arquivos
    files_to_process = []
    
    if file_paths:
        files_to_process.extend(file_paths)
    
    if directory_path:
        directory = Path(directory_path)
        if directory.exists() and directory.is_dir():
            files_to_process.extend([
                str(f) for f in directory.glob('*.txt')
            ])
    
    if not files_to_process:
        print("⚠️  Nenhum arquivo encontrado")
        return [], []
    
    print(f"📂 Processando {len(files_to_process)} arquivos...")
    
    for file_path in files_to_process:
        try:
            # Ler arquivo
            content = read_text_file(file_path)
            
            # Dividir em chunks
            chunks = chunk_text(content)
            
            # Adicionar chunks e metadados
            file_name = Path(file_path).name
            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadatas.append({
                    'source': file_name,
                    'chunk_id': i
                })
            
            print(f"   ✅ {file_name}: {len(chunks)} chunks")
        
        except Exception as e:
            print(f"   ❌ Erro em {file_path}: {e}")
    
    print(f"📊 Total: {len(all_texts)} chunks de {len(files_to_process)} arquivos")
    return all_texts, all_metadatas

