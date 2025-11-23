"""
Interface Streamlit Comparativa
Compara Monolítico vs Distribuído (gRPC)
"""

import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import statistics
import psutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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
if 'last_ingest_mono' not in st.session_state:
    st.session_state.last_ingest_mono = None
if 'last_ingest_dist' not in st.session_state:
    st.session_state.last_ingest_dist = None
if 'last_ingest_mono_error' not in st.session_state:
    st.session_state.last_ingest_mono_error = None
if 'last_ingest_dist_error' not in st.session_state:
    st.session_state.last_ingest_dist_error = None
if 'last_ingest_mono_raw' not in st.session_state:
    st.session_state.last_ingest_mono_raw = None
if 'last_ingest_dist_raw' not in st.session_state:
    st.session_state.last_ingest_dist_raw = None
if 'failure_log' not in st.session_state:
    st.session_state.failure_log = []
if 'quality_log' not in st.session_state:
    st.session_state.quality_log = []
if 'resource_history' not in st.session_state:
    st.session_state.resource_history = []
if 'net_io_snapshot' not in st.session_state:
    st.session_state.net_io_snapshot = psutil.net_io_counters()
if 'load_test_results' not in st.session_state:
    st.session_state.load_test_results = []

# CSS
st.markdown("""
<style>
    div[data-testid="metric-container"],
    section[data-testid="block"] div[data-testid="metric-container"],
    div[data-testid="stMetricValue"] > div {
        background-color: #f5f6fa !important;
        padding: 10px 12px !important;
        border-radius: 12px !important;
        border: 1px solid #d9d9d9 !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
    }
    div[data-testid="metric-container"] label {
        color: #333 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="metric-container"] p {
        font-size: 1.35rem !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }
    .mono-badge { background: #1f77b4; color: white; padding: 5px 10px; border-radius: 5px; }
    .dist-badge { background: #ff7f0e; color: white; padding: 5px 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)


def record_failure(architecture: str, operation: str, detail: str):
    """Registra falhas para análise de resiliência"""
    st.session_state.failure_log.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "architecture": architecture,
        "operation": operation,
        "detail": detail
    })
    # Mantém histórico enxuto
    st.session_state.failure_log = st.session_state.failure_log[-100:]


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((pct / 100) * (len(ordered) - 1)))
    index = max(0, min(index, len(ordered) - 1))
    return ordered[index]


def latency_summary(entries, architecture_label: str):
    times = [
        entry['time'] for entry in entries
        if entry['mode'] == architecture_label and entry.get('time') is not None
    ]
    if not times:
        return None
    return {
        "count": len(times),
        "avg": statistics.mean(times),
        "p95": percentile(times, 95),
        "min": min(times),
        "max": max(times)
    }


def build_cumulative_latency_df(entries):
    counters = {"monolithic": [], "distributed": []}
    records = []
    for entry in entries:
        mode = entry.get('mode')
        latency = entry.get('time')
        if mode not in counters or latency is None:
            continue
        counters[mode].append(latency)
        cumulative_avg = sum(counters[mode]) / len(counters[mode])
        records.append({
            "Execução": len(counters[mode]),
            "Modo": "Monolítico" if mode == "monolithic" else "Distribuído",
            "Latência (s)": latency,
            "Média acumulada (s)": cumulative_avg
        })
    return pd.DataFrame(records)


@st.cache_data(show_spinner=False)
def cached_latency_df(entries):
    return build_cumulative_latency_df(entries)


def quality_summary(log):
    if not log:
        return None
    mapping = {"Excelente": 4, "Boa": 3, "Regular": 2, "Ruim": 1}
    scores = [mapping.get(item["rating"], 0) for item in log]
    if not scores:
        return None
    avg_score = sum(scores) / len(scores)
    label = "Excelente" if avg_score >= 3.5 else "Boa" if avg_score >= 2.5 else "Regular" if avg_score >= 1.5 else "Ruim"
    return {
        "count": len(log),
        "avg_score": avg_score,
        "label": label
    }


def quality_summary_by_arch(log, arch_label: str):
    subset = [entry for entry in log if entry.get("architecture") == arch_label]
    return quality_summary(subset)


def latest_throughput_result(arch_label: str):
    for entry in reversed(st.session_state.load_test_results):
        if entry.get("architecture") == arch_label:
            return entry
    return None


def failure_count_by_arch(log, arch_label: str):
    return sum(1 for entry in log if entry.get("architecture") == arch_label)


def sample_resource_usage():
    """Coleta CPU, memória e rede do sistema"""
    cpu = psutil.cpu_percent(interval=0.05)
    memory = psutil.virtual_memory()
    net = psutil.net_io_counters()
    prev_net = st.session_state.net_io_snapshot
    delta_sent = net.bytes_sent - prev_net.bytes_sent
    delta_recv = net.bytes_recv - prev_net.bytes_recv
    st.session_state.net_io_snapshot = net
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "net_sent_kb": round(delta_sent / 1024, 2),
        "net_recv_kb": round(delta_recv / 1024, 2)
    }
    st.session_state.resource_history.append(entry)
    st.session_state.resource_history = st.session_state.resource_history[-50:]
    return entry


def render_architecture_metrics(
    label: str,
    data: list,
    color: str,
    last_ingest=None,
    quality=None,
    throughput=None,
    failure_total: int = 0
):
    st.markdown(
        f'<div class="arch-legend" style="color:{color}; font-weight:700; font-size:1.1rem; margin-bottom:0.2rem;">{label}</div>',
        unsafe_allow_html=True
    )
    if not data:
        st.info("Nenhuma query registrada ainda.")
        return

    latencies = [d['time'] for d in data if d.get('time') is not None]
    if not latencies:
        st.info("Sem tempos registrados.")
        return

    timestamps = [d['timestamp'].strftime("%H:%M:%S") for d in data if d.get('time') is not None]
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    p95_latency = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 20 else max_latency

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Consultas", len(latencies))
    with metric_cols[1]:
        st.metric("Média (s)", f"{avg_latency:.3f}")
    with metric_cols[2]:
        st.metric("p95 (s)", f"{p95_latency:.3f}")
    with metric_cols[3]:
        st.metric("Máx (s)", f"{max_latency:.3f}")

    extra_cols = st.columns(3)
    with extra_cols[0]:
        ingest_label = f"{last_ingest} chunks" if last_ingest is not None else "Sem dados"
        st.metric("Última ingestão", ingest_label)
    with extra_cols[1]:
        if quality:
            st.metric("Qualidade", quality['label'], delta=f"{quality['count']} avaliações")
        else:
            st.metric("Qualidade", "Sem avaliações")
    with extra_cols[2]:
        if throughput:
            st.metric(
                "Throughput (req/s)",
                f"{throughput['throughput_rps']:.2f}",
                help=f"{throughput['success']}/{throughput['requests']} req • {throughput['concurrency']} threads"
            )
        else:
            st.metric("Throughput (req/s)", "Sem testes")

    st.caption(f"Falhas registradas: {failure_total}")

    chart_df = pd.DataFrame({
        "Horário": timestamps,
        "Tempo (s)": latencies
    })
    chart_df.set_index("Horário", inplace=True)
    st.line_chart(chart_df, height=220)


def run_load_test(base_url: str, arch_label: str, total_requests: int, concurrency: int, query_text: str, top_k: int = 5):
    """Executa teste simples de throughput"""
    start_batch = time.time()
    results = []
    errors = []

    def worker():
        single_start = time.time()
        try:
            response = requests.post(
                f"{base_url}/query",
                json={"query": query_text, "top_k": top_k},
                timeout=60
            )
            elapsed = time.time() - single_start
            if response.status_code == 200:
                return True, elapsed, None
            else:
                return False, elapsed, response.text
        except Exception as e:
            return False, time.time() - single_start, str(e)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker) for _ in range(total_requests)]
        for fut in as_completed(futures):
            success, elapsed, err = fut.result()
            results.append(elapsed)
            if not success:
                errors.append(err)
                record_failure(arch_label, "load_test", err or "erro desconhecido")

    total_time = time.time() - start_batch
    success_count = total_requests - len(errors)
    throughput = total_requests / total_time if total_time > 0 else 0

    return {
        "architecture": arch_label,
        "requests": total_requests,
        "concurrency": concurrency,
        "success": success_count,
        "failures": len(errors),
        "avg_latency": statistics.mean(results) if results else 0,
        "throughput_rps": throughput,
        "errors": errors[:5],  # limitar exibição
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def check_api(url, name):
    """Verifica se API está online e retorna mensagem de erro detalhada"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            return True, None
        return False, f"{name}: status {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"{name}: {e}"


def query_api(url, query_text, top_k=5, arch_label="monolithic"):
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
            record_failure(arch_label, "query", response.text)
            return None, elapsed, response.text
    except Exception as e:
        elapsed = time.time() - start
        record_failure(arch_label, "query", str(e))
        return None, elapsed, str(e)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("RAG Onboarding")
    st.markdown("**Monolítico vs Distribuído**")
    st.markdown("---")
    
    # Status das APIs
    st.subheader("Status dos Sistemas")
    
    mono_online, mono_error = check_api(MONOLITHIC_URL, "Monolítico")
    dist_online, dist_error = check_api(DISTRIBUTED_URL, "Distribuído")
    
    col1, col2 = st.columns(2)
    with col1:
        if mono_online:
            st.success("Monolítico OK")
        else:
            st.error("Monolítico OFF")
            if mono_error:
                st.caption(mono_error)
    
    with col2:
        if dist_online:
            st.success("Distribuído OK")
        else:
            st.error("Distribuído OFF")
            if dist_error:
                st.caption(dist_error)
    
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
                            st.session_state.last_ingest_mono = (
                                result.get('chunks_added')
                                or result.get('documents_added')
                                or result.get('total_chunks')
                                or 0
                            )
                            st.session_state.last_ingest_mono_error = None
                            st.session_state.last_ingest_mono_raw = result
                        else:
                            st.session_state.last_ingest_mono = None
                            st.session_state.last_ingest_mono_error = response.text
                            st.session_state.last_ingest_mono_raw = None
                            st.error("Erro ao ingerir no monolítico")
                            record_failure("monolithic", "ingest", response.text)
                except Exception as e:
                    st.session_state.last_ingest_mono = None
                    st.session_state.last_ingest_mono_error = str(e)
                    st.session_state.last_ingest_mono_raw = None
                    st.error(f"Erro: {e}")
                    record_failure("monolithic", "ingest", str(e))
        
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
                            st.session_state.last_ingest_dist = (
                                result.get('chunks_added')
                                or result.get('documents_added')
                                or result.get('total_chunks')
                                or 0
                            )
                            st.session_state.last_ingest_dist_error = None
                            st.session_state.last_ingest_dist_raw = result
                        else:
                            st.session_state.last_ingest_dist = None
                            st.session_state.last_ingest_dist_error = response.text
                            st.session_state.last_ingest_dist_raw = None
                            st.error("Erro ao ingerir no distribuído")
                            record_failure("distributed", "ingest", response.text)
                except Exception as e:
                    st.session_state.last_ingest_dist = None
                    st.session_state.last_ingest_dist_error = str(e)
                    st.session_state.last_ingest_dist_raw = None
                    st.error(f"Erro: {e}")
                    record_failure("distributed", "ingest", str(e))

        if st.session_state.last_ingest_mono is not None:
            st.success(f"Última ingestão monolítica: {st.session_state.last_ingest_mono} chunks.")
        elif st.session_state.last_ingest_mono_error:
            st.warning(f"Monolítico: {st.session_state.last_ingest_mono_error}")

        if st.session_state.last_ingest_dist is not None:
            st.success(f"Última ingestão distribuída: {st.session_state.last_ingest_dist} chunks.")
        elif st.session_state.last_ingest_dist_error:
            st.warning(f"Distribuído: {st.session_state.last_ingest_dist_error}")

        if st.checkbox("Mostrar resposta bruta da ingestão", value=False):
            st.write("Monolítico:", st.session_state.get('last_ingest_mono_raw'))
            st.write("Distribuído:", st.session_state.get('last_ingest_dist_raw'))
    
    st.markdown("---")
    st.caption("Desenvolvido para comparar arquiteturas RAG")


# ============================================================================
# PÁGINA PRINCIPAL
# ============================================================================

st.title("Comparação: Monolítico vs Distribuído (gRPC)")

tab_operations, tab_analytics, tab_about = st.tabs([
    "Operações",
    "Analytics",
    "Sobre"
])

# ============================================================================
# TAB OPERATIONS
# ============================================================================

with tab_operations:
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
                    result_mono, time_mono, error_mono = query_api(MONOLITHIC_URL, query, top_k, "monolithic")
                    
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
                    result_dist, time_dist, error_dist = query_api(DISTRIBUTED_URL, query, top_k, "distributed")
                    
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
                result, elapsed, error = query_api(MONOLITHIC_URL, query, top_k, "monolithic")
                
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
                result, elapsed, error = query_api(DISTRIBUTED_URL, query, top_k, "distributed")
                
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
# TAB ANALYTICS
# ============================================================================

with tab_analytics:
    st.markdown("### Indicadores por Arquitetura")
    perf_window = st.session_state.performance_data[-200:]
    mono_entries = [entry for entry in perf_window if entry.get("mode") == "monolithic"]
    dist_entries = [entry for entry in perf_window if entry.get("mode") == "distributed"]
    mono_quality = quality_summary_by_arch(st.session_state.quality_log, "monolithic")
    dist_quality = quality_summary_by_arch(st.session_state.quality_log, "distributed")
    mono_throughput = latest_throughput_result("monolithic")
    dist_throughput = latest_throughput_result("distributed")
    mono_failures = failure_count_by_arch(st.session_state.failure_log, "monolithic")
    dist_failures = failure_count_by_arch(st.session_state.failure_log, "distributed")

    col_arch_mono, col_arch_dist = st.columns(2)
    with col_arch_mono:
        render_architecture_metrics(
            "Monolítico",
            mono_entries,
            "#1f77b4",
            last_ingest=st.session_state.last_ingest_mono,
            quality=mono_quality,
            throughput=mono_throughput,
            failure_total=mono_failures
        )
    with col_arch_dist:
        render_architecture_metrics(
            "Distribuído",
            dist_entries,
            "#ff7f0e",
            last_ingest=st.session_state.last_ingest_dist,
            quality=dist_quality,
            throughput=dist_throughput,
            failure_total=dist_failures
        )

    st.markdown("---")
    st.subheader("Latência end-to-end")
    latency_df = cached_latency_df(st.session_state.performance_data)
    if latency_df.empty:
        st.info("Ainda não há dados de latência. Execute algumas consultas primeiro.")
    else:
        fig_cum = px.line(
            latency_df,
            x="Execução",
            y="Média acumulada (s)",
            color="Modo",
            markers=True,
            title="Média acumulada por arquitetura"
        )
        st.plotly_chart(fig_cum, use_container_width=True)
        fig_raw = px.scatter(
            latency_df,
            x="Execução",
            y="Latência (s)",
            color="Modo",
            title="Latências individuais"
        )
        st.plotly_chart(fig_raw, use_container_width=True)

        df_all = pd.DataFrame(st.session_state.performance_data)
        df_all['timestamp'] = df_all['timestamp'].dt.strftime('%H:%M:%S')
        df_all = df_all.rename(columns={
            'mode': 'Modo',
            'time': 'Tempo (s)',
            'query': 'Query',
            'timestamp': 'Horário'
        })
        st.dataframe(df_all, use_container_width=True)
        csv = df_all.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            f"rag_latency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )

    st.markdown("---")
    st.subheader("Avaliação de Qualidade")
    st.subheader("Avaliação de Qualidade Manual")
    with st.form("quality_form"):
        arch_choice = st.selectbox(
            "Arquitetura avaliada",
            options=["monolithic", "distributed"],
            format_func=lambda x: "Monolítico" if x == "monolithic" else "Distribuído"
        )
        rating = st.select_slider(
            "Qualidade da resposta",
            options=["Excelente", "Boa", "Regular", "Ruim"]
        )
        notes = st.text_area("Observações", placeholder="Contexto utilizado, pontos fortes, lacunas...")
        submitted_quality = st.form_submit_button("Registrar avaliação")
        if submitted_quality:
            st.session_state.quality_log.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "architecture": arch_choice,
                "rating": rating,
                "notes": notes
            })
            st.success("Avaliação registrada.")

    if st.session_state.quality_log:
        st.markdown("#### Histórico de avaliações")
        st.dataframe(pd.DataFrame(st.session_state.quality_log))
    else:
        st.info("Nenhuma avaliação registrada ainda.")

    st.markdown("---")
    st.subheader("Resiliência e Falhas Registradas")
    if st.session_state.failure_log:
        st.dataframe(pd.DataFrame(st.session_state.failure_log))
    else:
        st.success("Até agora nenhuma falha registrada.")

    st.markdown("---")
    st.subheader("Consumo de Recursos do Host (ambas as arquiteturas)")
    st.caption("Os gráficos abaixo refletem o host compartilhado. Use-os para observar o impacto agregado das execuções do modo Monolítico e Distribuído.")

    if st.button("Atualizar métricas de recursos"):
        metrics = sample_resource_usage()
        st.success(
            f"Medição registrada • CPU {metrics['cpu_percent']}% • "
            f"RAM {metrics['memory_percent']}% ({metrics['memory_used_gb']} GB) • "
            f"Rede +{metrics['net_sent_kb']} KB / -{metrics['net_recv_kb']} KB"
        )

    if st.session_state.resource_history:
        res_df = pd.DataFrame(st.session_state.resource_history[-200:])
        perf_df = res_df.melt(
            id_vars="timestamp",
            value_vars=["cpu_percent", "memory_percent"],
            var_name="Métrica",
            value_name="Percentual"
        )
        perf_df["Métrica"] = perf_df["Métrica"].map({
            "cpu_percent": "CPU do host",
            "memory_percent": "Memória do host"
        })
        fig_perf = px.line(
            perf_df,
            x="timestamp",
            y="Percentual",
            color="Métrica",
            markers=True,
            title="CPU e Memória do host"
        )
        fig_perf.update_layout(
            legend=dict(title="Métrica (aplica às duas arquiteturas)")
        )
        st.plotly_chart(fig_perf, use_container_width=True)

        net_df = res_df.melt(
            id_vars="timestamp",
            value_vars=["net_sent_kb", "net_recv_kb"],
            var_name="Fluxo",
            value_name="KB"
        )
        net_df["Fluxo"] = net_df["Fluxo"].map({
            "net_sent_kb": "Envio (KB)",
            "net_recv_kb": "Recebimento (KB)"
        })
        fig_net = px.line(
            net_df,
            x="timestamp",
            y="KB",
            color="Fluxo",
            markers=True,
            title="Tráfego de rede do host"
        )
        fig_net.update_layout(
            legend=dict(title="Fluxo (host compartilhado)")
        )
        st.plotly_chart(fig_net, use_container_width=True)
    else:
        st.info("Capture as métricas para visualizar histórico de recursos.")

    st.markdown("---")
    st.subheader("Teste de Throughput")
    with st.form("load_test_form"):
        load_arch = st.selectbox("Arquitetura alvo do teste", ["Monolítico", "Distribuído"])
        total_requests = st.number_input("Número total de requisições", min_value=5, max_value=200, value=20, step=5)
        concurrency = st.slider("Concorrência (threads)", min_value=1, max_value=20, value=5)
        sample_question = st.text_input("Pergunta usada no teste", "Quais são os benefícios oferecidos?")
        submitted_load = st.form_submit_button("Executar teste")
        if submitted_load:
            target_url = MONOLITHIC_URL if load_arch == "Monolítico" else DISTRIBUTED_URL
            result = run_load_test(
                target_url,
                "monolithic" if load_arch == "Monolítico" else "distributed",
                total_requests,
                concurrency,
                sample_question
            )
            st.session_state.load_test_results.append(result)
            st.success(f"Teste concluído com throughput {result['throughput_rps']:.2f} req/s.")

    if st.session_state.load_test_results:
        st.markdown("#### Resultados recentes")
        st.dataframe(pd.DataFrame(st.session_state.load_test_results))
    else:
        st.info("Execute um teste para registrar resultados.")

# ============================================================================
# TAB SOBRE
# ============================================================================

with tab_about:
    st.markdown("""
    ## Sistema RAG Comparativo
    
    Esta interface compara duas arquiteturas:
    
    ### Arquitetura Monolítica
    - **Porta:** 8001
    - **Características:** Tudo em um processo Python
    - **Vantagens:** Baixa latência, simples
    - **Desvantagens:** Escalabilidade limitada
    
    ### Arquitetura Distribuída (gRPC)
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

