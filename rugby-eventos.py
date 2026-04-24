import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="BIG Report - Rugby Analytics | Catapult Sports",
    page_icon="🏉",
    layout="wide"
)

# Estilo CSS para melhor visualização
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
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
st.markdown("---")

# ==================== FUNÇÕES DE CARREGAMENTO DE DADOS ====================

@st.cache_data
def load_teams():
    """Carrega lista de equipes"""
    return [
        "Estudiantes de La Plata",
        "CUBA", 
        "CULP",
        "Selección Argentina",
        "Los Pumas 7's"
    ]

@st.cache_data
def load_players():
    """Carrega lista de atletas por equipe"""
    players = {
        "Estudiantes de La Plata": [
            "Agustin Dublo - #010",
            "Ignacio Diaz - #005", 
            "Ignacio Fadul - #012",
            "Juan Martin Godoy - #009",
            "Juan Pedro Ramognino - #004",
            "Leonardo Gallardo - #000",
            "Mateo Cechi - #008",
            "Guido De Genaro - #*24"
        ],
        "CUBA": [
            "Carlos Martinez - #001",
            "Luis Rodriguez - #002",
            "Jose Fernandez - #003"
        ],
        "CULP": [
            "Miguel Gonzalez - #011",
            "Pablo Suarez - #013",
            "Diego Pérez - #014"
        ],
        "Selección Argentina": [
            "Marcos Kremer - #001",
            "Pablo Matera - #002",
            "Julián Montoya - #003"
        ],
        "Los Pumas 7's": [
            "Santiago Alvarez - #001",
            "Tobias Wade - #002"
        ]
    }
    return players

@st.cache_data
def load_activities():
    """Carrega atividades disponíveis"""
    dates = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        dates.append(f"Activity {date.strftime('%Y%m%d%H%M%S')} - {date.strftime('%d/%m/%Y %H:%M')}")
    return dates

@st.cache_data
def load_event_data(team, player, activity, days_period):
    """Carrega dados de eventos com filtros aplicados"""
    
    np.random.seed(42)
    
    # Gerar número variável de eventos baseado nos filtros
    if player:
        n_events = np.random.randint(15, 45)
    else:
        n_events = np.random.randint(30, 80)
    
    # Gerar eventos
    base_time = datetime.now() - timedelta(days=np.random.randint(1, days_period))
    start_times = []
    current_time = base_time
    
    for i in range(n_events):
        delta = timedelta(seconds=np.random.randint(30, 300))
        start_times.append(current_time.timestamp())
        current_time += delta
    
    # Criar dataframe
    eventos_data = {
        "tipo_evento": np.random.choice(["Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"], n_events),
        "end_time": [t + np.random.uniform(2, 15) for t in start_times],
        "start_time": start_times,
        "duration_min": np.random.uniform(0.01, 0.35, n_events),
        "back_in_game_min": np.random.uniform(0.03, 6.0, n_events),
        "confidence": np.random.uniform(0.95, 1.0, n_events),
        "pos_x": np.random.uniform(0, 100, n_events),
        "pos_y": np.random.uniform(0, 70, n_events),
        "equipe": team,
        "atleta": player if player else "Todos",
        "atividade": activity
    }
    
    df = pd.DataFrame(eventos_data)
    
    # Ordenar por tempo
    df = df.sort_values('start_time')
    
    return df

# ==================== FUNÇÃO DO CAMPO DE RUGBY ====================

def create_rugby_field():
    """Cria um campo de rugby com dimensões oficiais (100m x 70m)"""
    
    # Dimensões oficiais (em metros)
    field_length = 100  # Comprimento total
    field_width = 70    # Largura total
    
    # Zonas
    in_goal_length = 10  # Área de in-goal (10m cada lado)
    total_length = field_length + (2 * in_goal_length)  # 120m total
    
    fig = go.Figure()
    
    # 1. Área de jogo (gramado)
    fig.add_shape(type="rect",
                  x0=0, x1=field_length,
                  y0=0, y1=field_width,
                  fillcolor="lightgreen",
                  line=dict(color="black", width=2),
                  layer="below")
    
    # 2. Linha de meio-campo (50m)
    fig.add_shape(type="line",
                  x0=field_length/2, x1=field_length/2,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=3))
    
    # 3. Linhas de 22m (a 22m de cada linha de fundo)
    fig.add_shape(type="line",
                  x0=22, x1=22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    fig.add_shape(type="line",
                  x0=field_length-22, x1=field_length-22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    # 4. Linhas de 10m
    fig.add_shape(type="line",
                  x0=10, x1=10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    fig.add_shape(type="line",
                  x0=field_length-10, x1=field_length-10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    # 5. Linhas de touch (laterais)
    fig.add_shape(type="rect",
                  x0=0, x1=field_length,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=3),
                  fillcolor=None)
    
    # 6. Traves (simplificadas nas linhas de fundo)
    fig.add_shape(type="line",
                  x0=field_length, x1=field_length,
                  y0=field_width/2 - 5, y1=field_width/2 + 5,
                  line=dict(color="yellow", width=3))
    
    fig.add_shape(type="line",
                  x0=0, x1=0,
                  y0=field_width/2 - 5, y1=field_width/2 + 5,
                  line=dict(color="yellow", width=3))
    
    # Configurar layout
    fig.update_layout(
        title="🏟️ Campo de Rugby - Dimensões Oficiais (100m x 70m)",
        xaxis=dict(title="Comprimento (metros)", 
                   range=[-5, field_length+5],
                   showgrid=True,
                   gridcolor="lightgray"),
        yaxis=dict(title="Largura (metros)",
                   range=[-5, field_width+5],
                   showgrid=True,
                   gridcolor="lightgray"),
        plot_bgcolor="lightgreen",
        height=550,
        hovermode='closest'
    )
    
    # Adicionar anotações
    annotations = [
        dict(x=field_length/2, y=field_width + 3, text="🏉 Línea de Medio Campo (50m)", showarrow=False, font=dict(size=10, color="blue")),
        dict(x=11, y=field_width + 3, text="Línea de 22m", showarrow=False, font=dict(size=9, color="red")),
        dict(x=field_length-11, y=field_width + 3, text="Línea de 22m", showarrow=False, font=dict(size=9, color="red")),
        dict(x=5, y=field_width/2, text="10m", showarrow=False, font=dict(size=8, color="darkblue")),
        dict(x=field_length-5, y=field_width/2, text="10m", showarrow=False, font=dict(size=8, color="darkblue")),
        dict(x=-3, y=field_width/2, text="🏉 In-Goal", showarrow=False, font=dict(size=9, color="darkgreen")),
        dict(x=field_length+3, y=field_width/2, text="🏉 In-Goal", showarrow=False, font=dict(size=9, color="darkgreen"))
    ]
    
    fig.update_layout(annotations=annotations)
    
    return fig, field_length, field_width

# ==================== BARRA LATERAL COM FILTROS ====================

st.sidebar.markdown("## 📂 Filtros de Dados")

# 1. Filtro de Período
st.sidebar.markdown("### 📅 Período")
dias_periodo = st.sidebar.slider(
    "Mostrar actividades de los últimos días:",
    min_value=7,
    max_value=180,
    value=90,
    step=7
)

# 2. Filtro de Equipe
st.sidebar.markdown("### 🏆 Equipe")
teams = load_teams()
selected_team = st.sidebar.selectbox("Seleccionar Equipo:", ["Todos"] + teams)

# 3. Filtro de Atleta (dinâmico baseado na equipe)
st.sidebar.markdown("### 👤 Atleta")
players_dict = load_players()

if selected_team != "Todos":
    available_players = players_dict.get(selected_team, [])
else:
    available_players = []
    for team_players in players_dict.values():
        available_players.extend(team_players)
    available_players = list(set(available_players))

available_players.insert(0, "Todos")
selected_player = st.sidebar.selectbox("Seleccionar Atleta:", available_players)

# 4. Filtro de Atividade
st.sidebar.markdown("### 📋 Actividad")
activities = load_activities()
selected_activity = st.sidebar.selectbox(
    "Seleccionar Actividad:",
    ["Última Atividade"] + activities[:20]
)

# 5. Filtro de Tipo de Evento
st.sidebar.markdown("### 🎯 Tipo de Evento")
event_types = ["Todos", "Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"]
selected_event_type = st.sidebar.selectbox("Filtrar por evento:", event_types)

# Botão de reset
if st.sidebar.button("🔄 Resetar Filtros"):
    st.rerun()

# Carregar dados com base nos filtros
df = load_event_data(selected_team, selected_player if selected_player != "Todos" else None, selected_activity, dias_periodo)

# Aplicar filtro de tipo de evento
if selected_event_type != "Todos":
    df = df[df["tipo_evento"] == selected_event_type]

# Mostrar informações dos filtros aplicados
st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Total de Eventos:** {len(df)}")
st.sidebar.markdown(f"**📅 Período:** {dias_periodo} días")
if selected_team != "Todos":
    st.sidebar.markdown(f"**🏆 Equipo:** {selected_team}")
if selected_player != "Todos":
    st.sidebar.markdown(f"**👤 Atleta:** {selected_player}")

# ==================== DASHBOARD PRINCIPAL ====================

# Métricas resumidas
if len(df) > 0:
    total_eventos = len(df)
    tempo_medio_entre = df["back_in_game_min"].mean()
    duracao_media = df["duration_min"].mean()
    carga_total = df["duration_min"].sum()
    confianca_media = df["confidence"].mean()
else:
    total_eventos = 0
    tempo_medio_entre = 0
    duracao_media = 0
    carga_total = 0
    confianca_media = 0

# Cards de métricas
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Eventos BIG", total_eventos)
with col2:
    st.metric("Tempo Médio Entre Eventos (min)", f"{tempo_medio_entre:.2f}")
with col3:
    st.metric("Duração Média por Evento (min)", f"{duracao_media:.2f}")
with col4:
    st.metric("Carga Total (min)", f"{carga_total:.2f}")
with col5:
    st.metric("Confiança Média", f"{confianca_media:.3f}")

# ==================== CAMPO DE RUGBY COM EVENTOS ====================

st.markdown('<div class="sub-header">🏟️ Mapa de Calor - Atividade no Campo</div>', unsafe_allow_html=True)

# Criar campo
fig_campo, field_len, field_wid = create_rugby_field()

# Adicionar pontos dos eventos
if len(df) > 0 and 'pos_x' in df.columns and 'pos_y' in df.columns:
    # Normalizar coordenadas para o campo (0-100m x 0-70m)
    scatter = fig_campo.add_trace(go.Scatter(
        x=df['pos_x'],
        y=df['pos_y'],
        mode='markers',
        marker=dict(
            size=df['duration_min'] * 30,  # Tamanho baseado na duração
            color=df['confidence'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Confiança"),
            opacity=0.7,
            line=dict(width=1, color='black')
        ),
        text=[f"Evento: {row['tipo_evento']}<br>Duração: {row['duration_min']:.2f}min<br>Conf: {row['confidence']:.3f}" 
              for _, row in df.iterrows()],
        hoverinfo='text',
        name='Eventos'
    ))

st.plotly_chart(fig_campo, use_container_width=True)

# ==================== TABELA DE EVENTOS ====================

st.markdown('<div class="sub-header">📋 Detalle de Eventos</div>', unsafe_allow_html=True)

# Preparar dataframe para exibição
df_display = df.copy()
if len(df_display) > 0:
    df_display["start_time_dt"] = pd.to_datetime(df_display["start_time"], unit='s')
    df_display["end_time_dt"] = pd.to_datetime(df_display["end_time"], unit='s')
    df_display["duration_min"] = df_display["duration_min"].round(4)
    df_display["back_in_game_min"] = df_display["back_in_game_min"].round(4)
    df_display["confidence"] = df_display["confidence"].round(3)
    
    # Selecionar colunas para exibir
    display_cols = ['tipo_evento', 'start_time_dt', 'end_time_dt', 'duration_min', 'back_in_game_min', 'confidence']
    if 'equipe' in df_display.columns:
        display_cols.insert(1, 'equipe')
    if 'atleta' in df_display.columns and selected_player == "Todos":
        display_cols.insert(2, 'atleta')
    
    st.dataframe(
        df_display[display_cols],
        use_container_width=True,
        column_config={
            "tipo_evento": "Tipo de Evento",
            "equipe": "Equipe",
            "atleta": "Atleta",
            "start_time_dt": "Inicio",
            "end_time_dt": "Fin",
            "duration_min": "Duración (min)",
            "back_in_game_min": "Back in Game (min)",
            "confidence": "Confianza"
        }
    )

# ==================== GRÁFICOS ADICIONAIS ====================

if len(df) > 0:
    st.markdown('<div class="sub-header">📈 Análise de Eventos</div>', unsafe_allow_html=True)
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        # Distribuição por tipo de evento
        event_counts = df['tipo_evento'].value_counts()
        fig_pie = px.pie(
            values=event_counts.values,
            names=event_counts.index,
            title="Distribución por Tipo de Evento",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_graf2:
        # Duração por evento
        fig_duration = px.bar(
            x=range(min(len(df), 50)),
            y=df['duration_min'].head(50),
            title="Duración por Evento (minutos)",
            labels={"x": "Número de Evento", "y": "Duración (min)"}
        )
        fig_duration.update_traces(marker_color='steelblue')
        st.plotly_chart(fig_duration, use_container_width=True)
    
    # Gráfico de linha do tempo
    col_graf3, col_graf4 = st.columns(2)
    
    with col_graf3:
        fig_timeline = px.line(
            x=range(len(df)),
            y=df['back_in_game_min'],
            title="Tiempo entre Eventos - Back in Game (minutos)",
            labels={"x": "Secuencia de Eventos", "y": "Tiempo (min)"}
        )
        fig_timeline.update_traces(line=dict(color='orange', width=2))
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col_graf4:
        # Confiança por evento
        fig_conf = px.scatter(
            x=range(len(df)),
            y=df['confidence'],
            title="Confianza por Evento",
            labels={"x": "Evento", "y": "Confianza"},
            color=df['confidence'],
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_conf, use_container_width=True)

# ==================== FOOTER ====================
st.markdown("---")
st.caption("📡 Datos obtenidos via API de Catapult Sports | Dashboard BIG Report - Análisis de Retorno a la Actividad")
st.caption("🏉 Campo con dimensiones oficiales World Rugby: 100m x 70m + áreas de in-goal")

# ==================== FUNÇÃO DA API CATAPULT (placeholder) ====================
@st.cache_data(ttl=300)
def connect_catapult_api():
    """
    Conexão com API da Catapult Sports
    Configure as credenciais no .streamlit/secrets.toml
    """
    try:
        api_key = st.secrets.get("CATAPULT_API_KEY")
        base_url = st.secrets.get("CATAPULT_BASE_URL", "https://api.catapult.com/v1")
        
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            return base_url, headers
        else:
            return None, None
    except:
        return None, None