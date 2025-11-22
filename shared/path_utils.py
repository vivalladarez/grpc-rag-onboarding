"""
Utilitários para resolver caminhos relativos ao diretório do projeto.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(path_str: str) -> Path:
    """
    Resolve um caminho (relativo ou absoluto) para Path absoluto.
    """
    if not path_str:
        raise ValueError("Caminho não pode ser vazio")

    path = Path(path_str)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def resolve_directory_path(path_str: str) -> Path:
    """
    Resolve um caminho e garante que seja um diretório existente.
    """
    path = resolve_path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"O caminho não é um diretório: {path}")
    return path


