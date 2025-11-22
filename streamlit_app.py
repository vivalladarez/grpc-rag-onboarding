"""
Interface Streamlit Comparativa
Compara Monolítico vs Distribuído (gRPC)
"""

import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="RAG Comparison",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URLs das APIs
MONOLITHIC_URL = "http://localhost:8001"
DISTRIBUTED_URL = "http://localhost:8002"

# Session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'performance_data' not in st.session_state:
    st.session_state.performance_data = []

# CSS
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .mono-badge { background: #1f77b4; color: white; padding: 5px 10px; border-radius: 5px; }
    .dist-badge { background: #ff7f0e; color: white; padding: 5px 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)


def check_api(url, name):
    """Verifica se API está online"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def query_api(url, query_text, top_k=5):
    """Faz query e mede tempo"""
    start = time.time()
    try:
        response = requests.post(
            f"{url}/query",
            json={"query": query_text, "top_k": top_k},
            timeout=60
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            return result, elapsed, None
        else:
            return None, elapsed, response.text
    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, str(e)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("RAG Comparison")
    st.markdown("**Monolítico vs Distribuído**")
    st.markdown("---")
    
    # Status das APIs
    st.subheader("Status dos Sistemas")
    
    mono_online = check_api(MONOLITHIC_URL, "Monolítico")
    dist_online = check_api(DISTRIBUTED_URL, "Distribuído")
    
    col1, col2 = st.columns(2)
    with col1:
        if mono_online:
            st.success("Monolítico OK")
        else:
            st.error("Monolítico OFF")
    
    with col2:
        if dist_online:
            st.success("Distribuído OK")
        else:
            st.error("Distribuído OFF")
    
    st.markdown("---")
    
    # Ingestão
    st.subheader("Gerenciar Documentos")
    
    with st.expander("Ingerir Documentos"):
        folder_path = st.text_input("Caminho:", value="./docs_onboarding")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ingerir Mono"):
                try:
                    with st.spinner("Processando..."):
                        response = requests.post(
                            f"{MONOLITHIC_URL}/ingest",
                            json={"directory_path": folder_path},
                            timeout=300
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"{result.get('chunks_added', 0)} chunks ingeridos.")
                        else:
                            st.error("Erro")
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        with col2:
            if st.button("Ingerir Dist"):
                try:
                    with st.spinner("Processando..."):
                        response = requests.post(
                            f"{DISTRIBUTED_URL}/ingest",
                            json={"directory_path": folder_path},
                            timeout=300
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"{result.get('chunks_added', 0)} chunks ingeridos.")
                        else:
                            st.error("Erro")
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    st.markdown("---")
    st.caption("Desenvolvido para comparar arquiteturas RAG")


# ============================================================================
# PÁGINA PRINCIPAL
# ============================================================================

st.title("Comparação: Monolítico vs Distribuído (gRPC)")

tab1, tab2, tab3 = st.tabs(["Chat & Comparação", "Métricas de Performance", "Sobre"])

# ============================================================================
# TAB 1: CHAT & COMPARAÇÃO
# ============================================================================

with tab1:
    query = st.text_area(
        "Faça sua pergunta:",
        placeholder="Ex: Como solicitar férias?",
        height=100
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        top_k = st.slider("Documentos (top_k):", 1, 10, 5)
    
    with col2:
        st.markdown("**Ações:**")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            compare_btn = st.button("Comparar Ambos", type="primary", use_container_width=True)
        with col_b:
            mono_btn = st.button("Monolítico", use_container_width=True)
        with col_c:
            dist_btn = st.button("Distribuído", use_container_width=True)
    
    # Comparar ambos
    if compare_btn and query:
        st.markdown("---")
        st.markdown("### Comparação Lado a Lado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Monolítico")
            if mono_online:
                with st.spinner("Processando..."):
                    result_mono, time_mono, error_mono = query_api(MONOLITHIC_URL, query, top_k)
                    
                    if result_mono:
                        st.metric("Tempo", f"{time_mono:.3f}s")
                        st.success(f"{result_mono.get('context_used', 0)} documentos")
                        with st.expander("Ver resposta"):
                            st.write(result_mono.get('answer', ''))
                        
                        # Salvar métrica
                        st.session_state.performance_data.append({
                            'mode': 'monolithic',
                            'time': time_mono,
                            'query': query,
                            'timestamp': datetime.now()
                        })
                    else:
                        st.error(f"Erro: {error_mono}")
            else:
                st.warning("API Monolítico offline")
        
        with col2:
            st.markdown("#### Distribuído (gRPC)")
            if dist_online:
                with st.spinner("Processando..."):
                    result_dist, time_dist, error_dist = query_api(DISTRIBUTED_URL, query, top_k)
                    
                    if result_dist:
                        st.metric("Tempo", f"{time_dist:.3f}s")
                        st.success(f"{result_dist.get('context_used', 0)} documentos")
                        with st.expander("Ver resposta"):
                            st.write(result_dist.get('answer', ''))
                        
                        # Salvar métrica
                        st.session_state.performance_data.append({
                            'mode': 'distributed',
                            'time': time_dist,
                            'query': query,
                            'timestamp': datetime.now()
                        })
                    else:
                        st.error(f"Erro: {error_dist}")
            else:
                st.warning("API Distribuído offline")
        
        # Comparação visual
        if mono_online and dist_online and result_mono and result_dist:
            st.markdown("---")
            st.markdown("### Comparação de Tempo")
            
            df_comp = pd.DataFrame([
                {"Modo": "Monolítico", "Tempo (s)": time_mono},
                {"Modo": "Distribuído", "Tempo (s)": time_dist}
            ])
            
            fig = px.bar(df_comp, x="Modo", y="Tempo (s)", color="Modo",
                        title="Tempo de Resposta",
                        color_discrete_map={"Monolítico": "#1f77b4", "Distribuído": "#ff7f0e"})
            st.plotly_chart(fig, use_container_width=True)
            
            # Diferença percentual
            diff = ((time_dist - time_mono) / time_mono) * 100
            if diff > 0:
                st.warning(f"Distribuído foi {diff:.1f}% mais lento (overhead de rede gRPC)")
            else:
                st.success(f"Distribuído foi {abs(diff):.1f}% mais rápido")
    
    # Query individual Monolítico
    if mono_btn and query:
        st.markdown("---")
        st.markdown("### Resultado Monolítico")
        
        if mono_online:
            with st.spinner("Processando..."):
                result, elapsed, error = query_api(MONOLITHIC_URL, query, top_k)
                
                if result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tempo", f"{elapsed:.3f}s")
                    with col2:
                        st.metric("Documentos", result.get('context_used', 0))
                    with col3:
                        st.metric("Modo", "Monolítico")
                    
                    st.markdown("#### Resposta:")
                    st.info(result.get('answer', ''))
                    
                    if result.get('sources'):
                        with st.expander("Ver Fontes"):
                            for i, src in enumerate(result['sources'], 1):
                                st.markdown(f"**{i}. {src['source']}** (score: {src['score']})")
                                st.text(src['excerpt'])
                else:
                    st.error(f"Erro: {error}")
        else:
            st.error("API Monolítico offline")
    
    # Query individual Distribuído
    if dist_btn and query:
        st.markdown("---")
        st.markdown("### Resultado Distribuído (gRPC)")
        
        if dist_online:
            with st.spinner("Processando via gRPC..."):
                result, elapsed, error = query_api(DISTRIBUTED_URL, query, top_k)
                
                if result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tempo", f"{elapsed:.3f}s")
                    with col2:
                        st.metric("Documentos", result.get('context_used', 0))
                    with col3:
                        st.metric("Modo", "gRPC")
                    
                    st.markdown("#### Resposta:")
                    st.info(result.get('answer', ''))
                    
                    if result.get('sources'):
                        with st.expander("Ver Fontes"):
                            for i, src in enumerate(result['sources'], 1):
                                st.markdown(f"**{i}. {src['source']}** (score: {src['score']})")
                                st.text(src['excerpt'])
                else:
                    st.error(f"Erro: {error}")
        else:
            st.error("API Distribuído offline. Certifique-se de que os serviços gRPC estão rodando!")


# ============================================================================
# TAB 2: MÉTRICAS
# ============================================================================

with tab2:
    st.markdown("### Análise de Performance")
    
    if not st.session_state.performance_data:
        st.info("ℹ️ Execute algumas queries para ver as métricas!")
    else:
        # Separar dados
        mono_data = [d for d in st.session_state.performance_data if d['mode'] == 'monolithic']
        dist_data = [d for d in st.session_state.performance_data if d['mode'] == 'distributed']
        
        # Métricas agregadas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if mono_data:
                avg_mono = sum(d['time'] for d in mono_data) / len(mono_data)
                st.metric("Média Monolítico", f"{avg_mono:.3f}s", 
                         help=f"{len(mono_data)} queries")
        
        with col2:
            if dist_data:
                avg_dist = sum(d['time'] for d in dist_data) / len(dist_data)
                st.metric("Média Distribuído", f"{avg_dist:.3f}s",
                         help=f"{len(dist_data)} queries")
        
        with col3:
            if mono_data and dist_data:
                diff = ((avg_dist - avg_mono) / avg_mono) * 100
                st.metric("Diferença", f"{diff:+.1f}%")
        
        with col4:
            st.metric("Total Queries", len(st.session_state.performance_data))
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Distribuição de Tempos")
            if mono_data or dist_data:
                times_df = []
                for d in mono_data:
                    times_df.append({"Modo": "Monolítico", "Tempo (s)": d['time']})
                for d in dist_data:
                    times_df.append({"Modo": "Distribuído", "Tempo (s)": d['time']})
                
                times_df = pd.DataFrame(times_df)
                fig = px.box(times_df, x="Modo", y="Tempo (s)", color="Modo",
                            color_discrete_map={"Monolítico": "#1f77b4", "Distribuído": "#ff7f0e"})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Evolução no Tempo")
            if mono_data or dist_data:
                evolution_df = []
                for i, d in enumerate(mono_data, 1):
                    evolution_df.append({"Query": i, "Modo": "Monolítico", "Tempo (s)": d['time']})
                for i, d in enumerate(dist_data, 1):
                    evolution_df.append({"Query": i, "Modo": "Distribuído", "Tempo (s)": d['time']})
                
                evolution_df = pd.DataFrame(evolution_df)
                fig = px.line(evolution_df, x="Query", y="Tempo (s)", color="Modo", markers=True,
                             color_discrete_map={"Monolítico": "#1f77b4", "Distribuído": "#ff7f0e"})
                st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de dados
        st.markdown("---")
        st.markdown("#### Dados Detalhados")
        
        df_all = pd.DataFrame(st.session_state.performance_data)
        df_all['timestamp'] = df_all['timestamp'].dt.strftime('%H:%M:%S')
        df_all = df_all.rename(columns={
            'mode': 'Modo',
            'time': 'Tempo (s)',
            'query': 'Query',
            'timestamp': 'Horário'
        })
        st.dataframe(df_all, use_container_width=True)
        
        # Download CSV
        csv = df_all.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            f"rag_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


# ============================================================================
# TAB 3: SOBRE
# ============================================================================

with tab3:
    st.markdown("""
    ## Sistema RAG Comparativo
    
    Esta interface compara duas arquiteturas:
    
    ### Arquitetura Monolítica
    - **Porta:** 8001
    - **Características:** Tudo em um processo Python
    - **Vantagens:** Baixa latência, simples
    - **Desvantagens:** Escalabilidade limitada
    
    ### 🌐 Arquitetura Distribuída (gRPC)
    - **Porta:** 8002
    - **Serviços gRPC:**
      - Embedding Service (50051)
      - Vector Service (50052)
      - LLM Service (50053)
    - **Vantagens:** Escalabilidade horizontal, isolamento
    - **Desvantagens:** Overhead de rede, mais complexo
    
    ---
    
    ### Como Usar
    
    **1. Iniciar Monolítico:**
    ```bash
    cd monolithic
    python app.py
    ```
    
    **2. Iniciar Distribuído:**
    ```bash
    cd distributed
    python generate_protos.py
    python services/embedding_service.py  # Terminal 1
    python services/vector_service.py     # Terminal 2
    python services/llm_service.py        # Terminal 3
    python gateway/app.py                 # Terminal 4
    ```
    
    **3. Iniciar Streamlit:**
    ```bash
    streamlit run streamlit_app.py
    ```
    
    ---
    
    ### Comparação
    
    Use o botão "Comparar Ambos" para testar ambas as arquiteturas
    simultaneamente e visualizar métricas de performance!
    """)

st.markdown("---")
st.caption("2025 - Sistema RAG Comparativo")

