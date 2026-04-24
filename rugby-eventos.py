import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Configuração da página
st.set_page_config(
    page_title="BIG Report - Rugby | Catapult Sports",
    page_icon="🏉",
    layout="wide"
)

# Estilo CSS para replicar a interface
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f3b73;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c5aa0;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
st.markdown("---")

# ==================== SEÇÃO 1: Conexão API Catapult ====================
@st.cache_data(ttl=300)
def connect_catapult_api():
    """
    Conexão com a API da Catapult Sports
    Você precisa configurar as credenciais no .streamlit/secrets.toml
    """
    try:
        # Configuração de autenticação
        api_key = st.secrets["CATAPULT_API_KEY"]
        base_url = st.secrets.get("CATAPULT_BASE_URL", "https://api.catapult.com/v1")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        return base_url, headers
    except:
        st.warning("⚠️ Credenciais da API não configuradas. Usando dados de exemplo.")
        return None, None

# ==================== SEÇÃO 2: Seleção de Dados ====================
st.sidebar.markdown("## 📂 Selección de Datos")

# 1. Seleção de arquivo/clube (simulado por enquanto)
st.sidebar.markdown("### 1. Archivo / Club")
arquivos = [
    "Club Estudiantes de La Plata - D...",
    "CUBA (ID: b5dbe5fe-ea47-452d-...)",
    "CULP (ID: c71f3d9b-688a-42d2-...)",
    "Demo Futbol (ID: 8a9bfd0a-786-...)",
    "DEMO General (ID: 75ffa20c-c10-...)"
]
selected_file = st.sidebar.selectbox("Seleccionar archivo", arquivos)

# 2. Seleção de atividade
st.sidebar.markdown("### 2. Seleccionar Actividad")
dias_mostrar = st.sidebar.slider("Mostrar actividades de los últimos días:", 7, 90, 90)

# Botão carregar atividades
if st.sidebar.button("🔄 Cargar Actividades"):
    st.sidebar.success("Actividades cargadas!")

# Lista de atividades (baseada nos prints)
atividades = [
    "Choiques Acel - 08/03/2026 14:2...",
    "Activity 20250813142416 - 13/0...",
    "Activity 20250813142307 - 13/0...",
    "Activity 20250813142304 - 13/0...",
    "Activity 20250813125720 - 13/08/2025 15:57",
    "Act. de anotación del año"
]
selected_activity = st.sidebar.selectbox("Seleccionar actividad", atividades)

# 3. Seleção de atleta
st.sidebar.markdown("### 3. Seleccionar Atleta")
if st.sidebar.button("👥 Cargar Atletas de la Actividad"):
    st.sidebar.info("Atletas cargados!")

# Lista de atletas (baseada nos prints)
atletas = {
    "Agustin Dublo - #010": "ID: 825...",
    "Ignacio Diaz - #005": "ID: b46cb...",
    "Ignacio Fadul - #012": "ID: 684...",
    "Juan Martin Godoy - #009": "ID: ...",
    "Juan Pedro Ramognino - #004": "ID: ...",
    "Leonardo Gallardo - #000": "ID: ...",
    "Mateo Cechi - #008": "ID: a9420...",
    "Guido DE GENARO - #*24": "ID: ..."
}

selected_atleta = st.sidebar.selectbox("Seleccione un atleta:", list(atletas.keys()))

# ==================== SEÇÃO 3: Dados de Exemplo ====================
# Criando dados similares aos prints
@st.cache_data
def load_sample_data():
    """Dados de exemplo replicando a estrutura dos prints"""
    
    # Dados dos eventos (baseado no print)
    eventos_data = {
        "tipo_evento": ["Contact"] * 10,
        "end_time": [1648924488.68, 1648924631.92, 1648924694.87, 1648924821.9, 
                     1648924925.61, 1648924987.08, 1648925082.09, 1648925108.44, 
                     1648925126.22, 1649024730.50],
        "start_time": [1648924487.66, 1648924616.96, 1648924687.29, 1648924819.64, 
                       1648924922.5, 1648924981.61, 1648925079.88, 1648925106.12, 
                       1648925110.49, 1649024732.52],
        "duration_min": [0.0172, 0.2495, 0.1265, 0.0378, 0.052, 0.0913, 0.037, 0.0388, 0.2623, 0.1057],
        "back_in_game_min": [2.138, 0.9228, 2.0795, 1.6767, 0.9333, 1.5467, 0.4005, 0.0342, 5.7857, 0.541],
        "confidence": [0.978, 1, 1, 0.98, 0.996, 0.998, 1, 0.974, 0.97, 0.974]
    }
    
    df_eventos = pd.DataFrame(eventos_data)
    
    # Calcular métricas resumidas
    total_eventos = len(df_eventos)
    tempo_medio_entre = df_eventos["back_in_game_min"].mean()
    duracao_media = df_eventos["duration_min"].mean()
    carga_total = df_eventos["duration_min"].sum()
    
    return df_eventos, total_eventos, tempo_medio_entre, duracao_media, carga_total

df_eventos, total_eventos, tempo_medio, duracao_media, carga_total = load_sample_data()

# ==================== SEÇÃO 4: Dashboard Principal ====================
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="sub-header">📊 Back in Game</div>', unsafe_allow_html=True)
    
    # Métricas principais
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    
    with col_metric1:
        st.metric("Total eventos BIG", total_eventos)
    with col_metric2:
        st.metric("Tiempo medio entre eventos (min)", f"{tempo_medio:.2f}")
    with col_metric3:
        st.metric("Duración media por evento (min)", f"{duracao_media:.2f}")
    with col_metric4:
        st.metric("Carga total de actividad (min)", f"{carga_total:.2f}")

with col2:
    st.markdown('<div class="sub-header">📞 Contacto</div>', unsafe_allow_html=True)
    st.info("**Juan Calvo**\ncalvoj550@gmail.com")

# ==================== SEÇÃO 5: Campo de Rugby (Heatmap) ====================
st.markdown('<div class="sub-header">🏟️ Mapa de Actividad en Campo</div>', unsafe_allow_html=True)

# Criando visualização do campo de rugby
fig_campo = go.Figure()

# Adicionar linha do campo (70m de largura)
campo_width = 70
campo_height = 100

# Linhas do campo
# Linha de touch (laterais)
fig_campo.add_shape(type="line", x0=0, x1=0, y0=0, y1=campo_height, line=dict(color="white", width=2))
fig_campo.add_shape(type="line", x0=campo_width, x1=campo_width, y0=0, y1=campo_height, line=dict(color="white", width=2))

# Linha de 22m
fig_campo.add_shape(type="line", x0=22, x1=22, y0=0, y1=campo_height, line=dict(color="yellow", width=2, dash="dash"))
fig_campo.add_shape(type="line", x0=campo_width-22, x1=campo_width-22, y0=0, y1=campo_height, line=dict(color="yellow", width=2, dash="dash"))

# Mitad de cancha
fig_campo.add_shape(type="line", x0=campo_width/2, x1=campo_width/2, y0=0, y1=campo_height, line=dict(color="red", width=3, dash="dash"))

# Dados simulados de calor (posições dos eventos)
import numpy as np
np.random.seed(42)
n_eventos_heatmap = 50
x_positions = np.random.uniform(0, campo_width, n_eventos_heatmap)
y_positions = np.random.uniform(0, campo_height, n_eventos_heatmap)

fig_campo.add_trace(go.Scatter(
    x=x_positions,
    y=y_positions,
    mode='markers',
    marker=dict(
        size=8,
        color=np.random.uniform(0, 1, n_eventos_heatmap),
        colorscale='Hot',
        showscale=True,
        colorbar=dict(title="Intensidad")
    ),
    name='Eventos'
))

fig_campo.update_layout(
    plot_bgcolor='green',
    paper_bgcolor='lightgray',
    xaxis=dict(range=[-5, campo_width+5], title="Ancho del campo (m)", showgrid=False),
    yaxis=dict(range=[-5, campo_height+5], title="Largo del campo (m)", showgrid=False),
    height=500,
    title="Línea de touch (ancho: 70m) | Línea de 22m | Mitad de cancha"
)

# Adicionar anotações das linhas
fig_campo.add_annotation(x=11, y=-3, text="Línea de 22m", showarrow=False, font=dict(size=10, color="white"))
fig_campo.add_annotation(x=campo_width/2, y=-3, text="Mitad de cancha", showarrow=False, font=dict(size=10, color="white"))
fig_campo.add_annotation(x=campo_width-11, y=-3, text="Línea de 22m", showarrow=False, font=dict(size=10, color="white"))

st.plotly_chart(fig_campo, use_container_width=True)

# ==================== SEÇÃO 6: Detalle de Eventos ====================
st.markdown('<div class="sub-header">📋 Detalle de eventos</div>', unsafe_allow_html=True)

# Formatar dataframe para exibição
df_display = df_eventos.copy()
df_display["end_time"] = pd.to_datetime(df_display["end_time"], unit='s')
df_display["start_time"] = pd.to_datetime(df_display["start_time"], unit='s')
df_display["duration_min"] = df_display["duration_min"].round(4)
df_display["back_in_game_min"] = df_display["back_in_game_min"].round(4)
df_display["confidence"] = df_display["confidence"].round(3)

st.dataframe(
    df_display,
    use_container_width=True,
    column_config={
        "tipo_evento": "Tipo de Evento",
        "end_time": "Fin del Evento",
        "start_time": "Inicio del Evento", 
        "duration_min": "Duración (min)",
        "back_in_game_min": "Back in Game (min)",
        "confidence": "Confianza"
    }
)

# ==================== SEÇÃO 7: Gráficos Adicionais ====================
st.markdown('<div class="sub-header">📈 Análisis de Eventos</div>', unsafe_allow_html=True)

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Gráfico de duração dos eventos
    fig_duration = px.bar(
        x=range(len(df_eventos)), 
        y=df_eventos["duration_min"],
        title="Duración por Evento (minutos)",
        labels={"x": "Número de Evento", "y": "Duración (min)"}
    )
    fig_duration.update_traces(marker_color='steelblue')
    st.plotly_chart(fig_duration, use_container_width=True)

with col_graf2:
    # Gráfico de tempo entre eventos (back in game)
    fig_big = px.line(
        x=range(len(df_eventos)),
        y=df_eventos["back_in_game_min"],
        title="Tiempo entre Eventos - Back in Game",
        labels={"x": "Evento", "y": "Tiempo (min)"}
    )
    fig_big.update_traces(line=dict(color='orange', width=2))
    st.plotly_chart(fig_big, use_container_width=True)

# ==================== SEÇÃO 8: Footer ====================
st.markdown("---")
st.caption("📡 Datos obtenidos via API de Catapult Sports | Dashboard BIG Report - Análisis de Retorno a la Actividad")

# ==================== CONEXÃO REAL COM API CATAPULT ====================
def get_real_catapult_data(athlete_id, activity_id):
    """
    Função para buscar dados reais da API da Catapult
    Documentação: https://developer.catapultsports.com/
    """
    base_url, headers = connect_catapult_api()
    
    if base_url and headers:
        try:
            # Endpoints comuns da API Catapult
            # Endpoint para métricas de jogador
            athlete_endpoint = f"{base_url}/athletes/{athlete_id}/metrics"
            
            # Buscar dados do atleta
            response = requests.get(athlete_endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Processar dados conforme necessidade
                return data
            else:
                st.error(f"Erro na API: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Erro de conexão: {str(e)}")
            return None
    
    return None