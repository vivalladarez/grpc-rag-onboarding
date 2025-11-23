# RAG (Retrieval-Augmented Generation): Monolítico vs Distribuído (gRPC)

Sistema RAG (Retrieval-Augmented Generation) para onboarding corporativo com **duas arquiteturas** para comparação de desempenho:
- **Monolítico**: Tudo em um processo
- **Distribuído**: Microserviços com gRPC

## Arquiteturas
<div align="center">
  <img width="553" height="389" alt="image" src="https://github.com/user-attachments/assets/919dc353-7298-4d78-989b-7795f0c7a93b"/>
</div>

## Estrutura do Projeto

```
grpc-rag-onboarding/
│
├── monolithic/                        # Sistema Monolítico
│   ├── app.py                         # FastAPI :8001
│   └── rag_pipeline.py                # Pipeline RAG completo
│
├── distributed/                       # Sistema Distribuído
│   ├── services/                      # Microserviços gRPC
│   │   ├── embedding_service.py       # :50051
│   │   ├── vector_service.py          # :50052
│   │   └── llm_service.py             # :50053
│   ├── gateway/                       # Gateway FastAPI
│   │   ├── app.py                     # :8002
│   │   └── rag_client.py              # Cliente gRPC
│   ├── protos/                        # Protocol Buffers
│   │   ├── embedding_service.proto
│   │   ├── vector_service.proto
│   │   └── llm_service.proto
│   ├── generated/                     # Código gerado (auto)
│   └── generate_protos.py             # Script para gerar .proto
│
├── shared/                            # Código compartilhado
│   ├── embeddings.py                  # Modelo de embeddings
│   ├── vectordb.py                    # ChromaDB
│   ├── llm.py                         # Ollama LLM
│   └── ingest.py                      # Processamento de docs
│
├── docs_onboarding/                   # Documentos para RAG
│   ├── ferias_e_pontos.txt
│   ├── beneficios.txt
│   └── ...
│
├── streamlit_app.py                   # Interface Streamlit
│
├── requirements.txt
└── README.md
```

## Tecnologias

![FastAPI](https://img.shields.io/badge/FastAPI-000000?style=flat&logo=fastapi&logoColor=FFFFFF)
![gRPC](https://img.shields.io/badge/gRPC-000000?style=flat&logo=grpc&logoColor=FFFFFF)
![Protobuf](https://img.shields.io/badge/Protobuf-000000?style=flat&logo=google&logoColor=FFFFFF)
![ChromaDB](https://img.shields.io/badge/ChromaDB-000000?style=flat&logo=material-design&logoColor=FFFFFF)
![SentenceTransformers](https://img.shields.io/badge/SentenceTransformers-000000?style=flat&logo=python&logoColor=FFFFFF)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=FFFFFF)
![Streamlit](https://img.shields.io/badge/Streamlit-000000?style=flat&logo=streamlit&logoColor=FFFFFF)


## Instalação

### 1. Pré-requisitos

- **Python 3.9+**
- **Ollama** instalado e rodando:
```bash
  # Baixe em: https://ollama.ai
  ollama pull llama3.2:3b
  ollama serve
```

### 2. Instalar Dependências

```bash
# Clonar repositório
git clone https://github.com/vivalladarez/grpc-rag-onboarding.git
cd grpc-rag-onboarding

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  

# Instalar dependências
pip install -r requirements.txt
```

## Como Usar

### 1. Iniciar Sistema Monolítico

Abra um terminal e execute:

```bash
cd monolithic
python app.py
```

A API estará disponível em **http://localhost:8001**

---

### 2. Iniciar Sistema Distribuído (gRPC)

O sistema distribuído requer **5 terminais** rodando simultaneamente:

#### Terminal 1 - Gerar código dos .proto
```bash
cd distributed
python generate_protos.py
```

#### Terminal 2 - Embedding Service
```bash
cd distributed
python services/embedding_service.py
```
Rodando em `localhost:50051`

#### Terminal 3 - Vector Service
```bash
cd distributed
python services/vector_service.py
```
Rodando em `localhost:50052`

#### Terminal 4 - LLM Service
```bash
cd distributed
python services/llm_service.py
```
Rodando em `localhost:50053`

#### Terminal 5 - Gateway FastAPI
```bash
cd distributed
python gateway/app.py
```
API disponível em **http://localhost:8002**

---

### 3. Iniciar Interface Streamlit

Em um novo terminal:

```bash
streamlit run streamlit_app.py
```

Acesse: **http://localhost:8501**

## Interface Streamlit

A interface permite:

1. **Chat individual** com cada sistema
2. **Comparação lado a lado** (botão "Comparar Ambos")
3. **Métricas de performance** em tempo real
4. **Visualizações gráficas** (box plots, linha temporal)
5. **Export de dados** para CSV

### Funcionalidades

- Testar modo Monolítico
- Testar modo Distribuído (gRPC)
- Comparar ambos simultaneamente
- Visualizar métricas de tempo
- Analisar overhead de rede gRPC
- Ingerir novos documentos
- Download de dados em CSV

## Exemplos de Queries

- "Como solicitar férias?"
- "Quais são os benefícios da empresa?"
- "Como acessar os sistemas internos?"
- "Qual é a política de trabalho remoto?"
- "Como funciona o reembolso de despesas?"