# RAG (Retrieval-Augmented Generation): Monolítico vs Distribuído (gRPC)

Sistema RAG (Retrieval-Augmented Generation) para onboarding corporativo com **duas arquiteturas** para comparação de desempenho:
- **Monolítico**: Tudo em um processo
- **Distribuído**: Microserviços com gRPC

## Arquiteturas
<div align="center">
  <img width="553" height="389" alt="image" src="https://github.com/user-attachments/assets/4a5e5d36-767e-451b-8d56-73562ea8045c" />
</div>

## Estrutura do Projeto

```
grpc-rag-onboarding/
│
├── monolithic/                # Sistema Monolítico
│   ├── app.py                # FastAPI :8001
│   └── rag_pipeline.py       # Pipeline RAG completo
│
├── distributed/               # Sistema Distribuído
│   ├── services/             # Microserviços gRPC
│   │   ├── embedding_service.py  # :50051
│   │   ├── vector_service.py     # :50052
│   │   └── llm_service.py        # :50053
│   ├── gateway/              # Gateway FastAPI
│   │   ├── app.py           # :8002
│   │   └── rag_client.py    # Cliente gRPC
│   ├── protos/               # Protocol Buffers
│   │   ├── embedding_service.proto
│   │   ├── vector_service.proto
│   │   └── llm_service.proto
│   ├── generated/            # Código gerado (auto)
│   └── generate_protos.py   # Script para gerar .proto
│
├── shared/                    # Código compartilhado
│   ├── embeddings.py         # Modelo de embeddings
│   ├── vectordb.py           # ChromaDB
│   ├── llm.py                # Ollama LLM
│   └── ingest.py             # Processamento de docs
│
├── docs_onboarding/           # Documentos para RAG
│   ├── ferias_e_pontos.txt
│   ├── beneficios.txt
│   └── ...
│
├── streamlit_app.py           # Interface comparativa
│
├── requirements.txt
└── README.md
```

## Tecnologias

- **FastAPI**: APIs REST
- **gRPC + Protocol Buffers**: Comunicação entre microserviços
- **ChromaDB**: Banco de dados vetorial
- **Sentence Transformers**: Embeddings (E5 multilingual)
- **Ollama**: LLM local (Llama 3.2)
- **Streamlit**: Interface web comparativa

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
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

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

> **Dica**: Você pode executar ambos sistemas (monolítico E distribuído) simultaneamente para comparação em tempo real!

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

## Comparação de Desempenho

| Critério | Monolítico | Distribuído (gRPC) |
|----------|------------|--------------------|
| **Latência** | Baixa (~2-3s) | Média (~3-5s) |
| **Overhead** | Zero | Rede + Serialização |
| **Escalabilidade** | Vertical | Horizontal |
| **Complexidade** | Simples | Moderada |
| **Desenvolvimento** | Rápido | Moderado |
| **Produção** | Limitado | Recomendado |
| **Isolamento** | Não | Sim |
| **Deployment** | Fácil | Requer orquestração |

### Quando Usar Cada Um?

**Use Monolítico quando:**
- Desenvolvimento rápido / POC
- Volumes baixos (< 100 req/s)
- Latência é crítica
- Equipe pequena
- Orçamento limitado

**Use Distribuído quando:**
- Produção de larga escala
- Alta disponibilidade (99.9%+)
- Volumes altos (> 1000 req/s)
- Necessidade de escalar componentes independentemente
- Equipe com expertise DevOps

## Troubleshooting

### "Ollama não conectado"
```bash
# Verificar se Ollama está rodando
ollama list

# Se não, inicie:
ollama serve
# Em outro terminal:
ollama run llama3.2:3b
```

### "gRPC Error: UNAVAILABLE"
**Causa:** Serviços gRPC não estão rodando

**Solução:**
Inicie todos os serviços gRPC manualmente (consulte seção "Iniciar Sistema Distribuído")

### "No module named 'generated'"
**Causa:** Código dos .proto não foi gerado

**Solução:**
```bash
cd distributed
python generate_protos.py
```

### API Monolítico/Distribuído offline no Streamlit
**Causa:** APIs não foram iniciadas

**Solução:**
- **Monolítico**: `cd monolithic && python app.py`
- **Distribuído**: Inicie os 5 serviços conforme seção "Iniciar Sistema Distribuído"

## Testar via API

### API Monolítico (porta 8001)

```bash
# Health Check
curl http://localhost:8001/health

# Query
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Como solicitar férias?\", \"top_k\": 5}"

# Ingerir documentos
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d "{\"directory_path\": \"./docs_onboarding\"}"
```

### API Distribuído (porta 8002)

```bash
# Health Check
curl http://localhost:8002/health

# Query
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Como solicitar férias?\", \"top_k\": 5}"
```

## Exemplos de Queries

- "Como solicitar férias?"
- "Quais são os benefícios da empresa?"
- "Como acessar os sistemas internos?"
- "Qual é a política de trabalho remoto?"
- "Como funciona o reembolso de despesas?"

## Workflow Típico

1. **Iniciar Ollama**
   ```bash
   ollama serve
   ```

2. **Escolher e iniciar arquitetura**
   
   **Monolítico:**
   ```bash
   cd monolithic
   python app.py
   ```
   
   **OU Distribuído (em 5 terminais):**
   ```bash
   # Terminal 1
   cd distributed && python generate_protos.py
   
   # Terminal 2
   cd distributed && python services/embedding_service.py
   
   # Terminal 3
   cd distributed && python services/vector_service.py
   
   # Terminal 4
   cd distributed && python services/llm_service.py
   
   # Terminal 5
   cd distributed && python gateway/app.py
   ```

3. **Iniciar Streamlit**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Ingerir documentos** (primeira vez)
   - Na sidebar do Streamlit → "Ingerir Documentos"
   - Ou via API (consulte seção "Testar via API")

5. **Testar e Comparar**
   - Use o botão "Comparar Ambos"
   - Analise as métricas na aba "Métricas de Performance"

## Documentação das APIs

- **Monolítico**: http://localhost:8001/docs
- **Distribuído**: http://localhost:8002/docs

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit (`git commit -am 'Adiciona funcionalidade'`)
4. Push (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

MIT License

## Próximos Passos

- [ ] Adicionar autenticação
- [ ] Implementar rate limiting
- [ ] Adicionar monitoring (Prometheus)
- [ ] Deploy com Docker/Kubernetes
- [ ] Implementar caching
- [ ] Testes automatizados
- [ ] Suporte a mais formatos de documentos
- [ ] Service mesh (Istio)

---

**Desenvolvido para demonstrar e comparar arquiteturas RAG**

**GitHub**: https://github.com/vivalladarez/grpc-rag-onboarding

