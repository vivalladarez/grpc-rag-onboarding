"""
Módulo LLM - Código Compartilhado
"""

import requests
import os
from typing import Optional


class OllamaLLM:
    """Classe para interagir com Ollama"""
    
    def __init__(self, base_url: str = None, model: str = None):
        if base_url is None:
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        if model is None:
            model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        
        print(f"Ollama endpoint: {self.base_url}")
        print(f"Modelo carregado: {self.model}")
    
    def check_connection(self) -> bool:
        """Verifica se Ollama está acessível"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Gera resposta"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        try:
            print("Gerando resposta com o LLM...")
            response = requests.post(self.generate_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            generated_text = result.get('response', '')
            print(f"Resposta gerada ({len(generated_text)} caracteres)")
            return generated_text
        except Exception as e:
            error_msg = f"Erro ao gerar resposta: {str(e)}"
            print(error_msg)
            return error_msg

