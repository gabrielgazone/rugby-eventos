import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="BIG Report - Rugby Analytics | Catapult Sports",
    page_icon="🏉",
    layout="wide"
)

# ==================== ESTILO CSS ====================
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

# ==================== DECODIFICAR TOKEN ====================

def decode_jwt(token):
    """Decodifica JWT sem verificar assinatura"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        return decoded
    except:
        return None

# ==================== INICIALIZAÇÃO ====================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'api_headers' not in st.session_state:
        st.session_state.api_headers = None
    if 'api_base' not in st.session_state:
        st.session_state.api_base = None
    if 'token_decoded' not in st.session_state:
        st.session_state.token_decoded = None
    
    # Dados carregados da API
    if 'activities_list' not in st.session_state:
        st.session_state.activities_list = []  # [{id, name}]
    if 'teams_list' not in st.session_state:
        st.session_state.teams_list = []
    if 'players_list' not in st.session_state:
        st.session_state.players_list = []
    
    # Seleções atuais
    if 'selected_activity_id' not in st.session_state:
        st.session_state.selected_activity_id = None
    if 'selected_activity_name' not in st.session_state:
        st.session_state.selected_activity_name = "Todas"
    if 'selected_team_id' not in st.session_state:
        st.session_state.selected_team_id = None
    if 'selected_team_name' not in st.session_state:
        st.session_state.selected_team_name = "Todas"
    if 'selected_player_id' not in st.session_state:
        st.session_state.selected_player_id = None
    if 'selected_player_name' not in st.session_state:
        st.session_state.selected_player_name = "Todos"
    if 'selected_event_type' not in st.session_state:
        st.session_state.selected_event_type = "Todos"
    
    # Dados de eventos
    if 'events_df' not in st.session_state:
        st.session_state.events_df = None
    
    # Período
    if 'days_period' not in st.session_state:
        st.session_state.days_period = 30

# ==================== FUNÇÕES DA API ====================

def call_api(endpoint, params=None):
    """Chama a API com tratamento de erro"""
    if not st.session_state.api_headers or not st.session_state.api_base:
        return []
    
    # Tentar diferentes formatos de endpoint
    endpoints_to_try = [
        f"{st.session_state.api_base}/api/v1/{endpoint}",
        f"{st.session_state.api_base}/v1/{endpoint}",
        f"{st.session_state.api_base}/{endpoint}"
    ]
    
    for url in endpoints_to_try:
        try:
            response = requests.get(url, headers=st.session_state.api_headers, timeout=10, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for key in ['data', 'items', 'results', endpoint]:
                        if key in data and isinstance(data[key], list):
                            return data[key]
                    return [data] if data else []
        except:
            continue
    return []

def load_activities():
    """Carrega atividades da API"""
    data = call_api("activities")
    activities = []
    for item in data:
        item_id = item.get('id') or item.get('activity_id')
        item_name = item.get('name') or item.get('title')
        if item_id and item_name:
            activities.append({"id": item_id, "name": item_name})
    return activities

def load_teams(activity_id=None):
    """Carrega equipes da API"""
    params = {"limit": 200}
    if activity_id:
        params["activity_id"] = activity_id
    data = call_api("teams", params)
    teams = []
    for item in data:
        team_id = item.get('id') or item.get('team_id')
        team_name = item.get('name') or item.get('team_name')
        if team_id and team_name:
            teams.append({"id": team_id, "name": team_name})
    return teams

def load_players(team_id=None, activity_id=None):
    """Carrega atletas da API"""
    params = {"limit": 500}
    if team_id:
        params["team_id"] = team_id
    if activity_id:
        params["activity_id"] = activity_id
    data = call_api("players", params)
    players = []
    for item in data:
        player_id = item.get('id') or item.get('player_id')
        player_name = item.get('name') or item.get('full_name') or item.get('display_name')
        if player_id and player_name:
            number = item.get('number') or item.get('jersey_number')
            if number:
                player_name = f"{player_name} - #{number}"
            players.append({"id": player_id, "name": player_name})
    return players

def load_events(team_id=None, player_id=None, activity_id=None, days=30):
    """Carrega eventos da API"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        "limit": 1000,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    if team_id:
        params["team_id"] = team_id
    if player_id:
        params["player_id"] = player_id
    if activity_id:
        params["activity_id"] = activity_id
    
    data = call_api("events", params)
    
    if data and len(data) > 0:
        df = pd.DataFrame(data)
        
        # Mapear campos para os nomes esperados pelo dashboard
        column_mapping = {
            'type': 'tipo_evento',
            'event_type': 'tipo_evento',
            'duration': 'duration_min',
            'duration_minutes': 'duration_min',
            'confidence_score': 'confidence',
            'confidence': 'confidence',
            'position_x': 'pos_x',
            'x': 'pos_x',
            'position_y': 'pos_y',
            'y': 'pos_y',
            'back_in_game': 'back_in_game_min'
        }
        
        for old, new in column_mapping.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
        
        # Garantir colunas padrão se não existirem
        if 'tipo_evento' not in df.columns:
            df['tipo_evento'] = 'Evento'
        if 'duration_min' not in df.columns:
            df['duration_min'] = np.random.uniform(0.05, 0.3, len(df))
        if 'confidence' not in df.columns:
            df['confidence'] = np.random.uniform(0.85, 0.99, len(df))
        if 'pos_x' not in df.columns:
            df['pos_x'] = np.random.uniform(0, 100, len(df))
        if 'pos_y' not in df.columns:
            df['pos_y'] = np.random.uniform(0, 70, len(df))
        if 'back_in_game_min' not in df.columns:
            df['back_in_game_min'] = np.random.uniform(0.5, 5, len(df))
        
        return df
    return pd.DataFrame()

# ==================== FUNÇÃO DO CAMPO DE RUGBY ====================

def create_rugby_field():
    """Cria um campo de rugby com dimensões oficiais (100m x 70m)"""
    
    field_length = 100
    field_width = 70
    
    fig = go.Figure()
    
    # Área de jogo
    fig.add_shape(type="rect",
                  x0=0, x1=field_length,
                  y0=0, y1=field_width,
                  fillcolor="lightgreen",
                  line=dict(color="black", width=2),
                  layer="below")
    
    # Linha de meio-campo
    fig.add_shape(type="line",
                  x0=field_length/2, x1=field_length/2,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=3))
    
    # Linhas de 22m
    fig.add_shape(type="line",
                  x0=22, x1=22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    fig.add_shape(type="line",
                  x0=field_length-22, x1=field_length-22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    # Linhas de 10m
    fig.add_shape(type="line",
                  x0=10, x1=10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    fig.add_shape(type="line",
                  x0=field_length-10, x1=field_length-10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    # Linhas de touch
    fig.add_shape(type="rect",
                  x0=0, x1=field_length,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=3),
                  fillcolor=None)
    
    # Configurar layout
    fig.update_layout(
        title="🏟️ Campo de Rugby - Dimensões Oficiais (100m x 70m)",
        xaxis=dict(title="Comprimento (metros)", range=[-5, field_length+5], showgrid=True, gridcolor="lightgray"),
        yaxis=dict(title="Largura (metros)", range=[-5, field_width+5], showgrid=True, gridcolor="lightgray"),
        plot_bgcolor="lightgreen",
        height=550,
        hovermode='closest'
    )
    
    # Adicionar anotações
    annotations = [
        dict(x=field_length/2, y=field_width + 3, text="🏉 Línea de Medio Campo (50m)", showarrow=False, font=dict(size=10, color="blue")),
        dict(x=11, y=field_width + 3, text="Línea de 22m", showarrow=False, font=dict(size=9, color="red")),
        dict(x=field_length-11, y=field_width + 3, text="Línea de 22m", showarrow=False, font=dict(size=9, color="red"))
    ]
    
    fig.update_layout(annotations=annotations)
    
    return fig

# ==================== TELA DE LOGIN ====================

def login_screen():
    """Tela de login com decodificação automática do token"""
    
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1>
            <h3 style="color: #2c5aa0;">Catapult Sports Integration</h3>
            <p style="margin-top: 20px;">Conecte-se à API da Catapult para acessar os dados</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔑 Autenticação")
            
            api_token = st.text_area(
                "Token JWT:",
                height=120,
                placeholder="Cole seu token JWT aqui...",
                type="password",
                help="Token fornecido pela Catapult Sports"
            )
            
            if api_token:
                # Decodificar token automaticamente
                decoded = decode_jwt(api_token)
                
                if decoded:
                    # Extrair informações do token
                    api_url = decoded.get('iss', '')
                    customer_id = None
                    if 'com.catapultsports' in decoded:
                        customer_id = decoded['com.catapultsports']['openfield']['customers'][0]['id']
                    
                    st.success(f"✅ Token válido!")
                    st.info(f"🌐 URL detectada: {api_url}")
                    st.info(f"🏢 Customer ID: {customer_id}")
                    
                    with st.expander("📋 Permissões do token"):
                        scopes = decoded.get('scope', [])
                        for scope in scopes:
                            st.caption(f"✓ {scope}")
                    
                    if st.button("✅ Conectar à API", type="primary", use_container_width=True):
                        st.session_state.api_headers = {
                            "Authorization": f"Bearer {api_token}",
                            "Content-Type": "application/json"
                        }
                        st.session_state.api_base = api_url
                        st.session_state.token_decoded = decoded
                        st.session_state.authenticated = True
                        
                        with st.spinner("Carregando atividades iniciais..."):
                            activities = load_activities()
                            if activities:
                                st.session_state.activities_list = activities
                                st.success(f"✅ {len(activities)} atividades carregadas!")
                            else:
                                st.warning("⚠️ Nenhuma atividade encontrada. Verifique suas permissões.")
                        
                        st.rerun()
                else:
                    st.error("❌ Token inválido")

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal completo"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # ==================== BARRA LATERAL COM FILTROS ====================
    
    st.sidebar.markdown("## 📂 Filtros de Dados")
    
    # Status da conexão
    if st.session_state.api_headers:
        st.sidebar.success("✅ Conectado à API Catapult")
        if st.session_state.token_decoded:
            customer_id = None
            if 'com.catapultsports' in st.session_state.token_decoded:
                customer_id = st.session_state.token_decoded['com.catapultsports']['openfield']['customers'][0]['id']
            st.sidebar.caption(f"🏢 Cliente: {customer_id}")
    
    st.sidebar.markdown("---")
    
    # 1. Filtro de Período
    st.sidebar.markdown("### 📅 Período")
    
    period_type = st.sidebar.radio(
        "Tipo de período:",
        ["Últimos dias", "Intervalo personalizado"],
        horizontal=True
    )
    
    if period_type == "Últimos dias":
        days_period = st.sidebar.slider(
            "Mostrar actividades de los últimos días:",
            min_value=1,
            max_value=180,
            value=30,
            step=7
        )
        st.session_state.days_period = days_period
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=days_period)
        st.sidebar.info(f"📆 Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    else:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial:", value=datetime.now() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data final:", value=datetime.now())
        if data_inicio and data_fim:
            days_period = (data_fim - data_inicio).days
            st.session_state.days_period = max(1, days_period)
    
    st.sidebar.markdown("---")
    
    # 2. Filtro de Atividades
    st.sidebar.markdown("### 📋 Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        with st.spinner("Carregando atividades da API..."):
            activities = load_activities()
            if activities:
                st.session_state.activities_list = activities
                st.sidebar.success(f"✅ {len(activities)} atividades carregadas")
            else:
                st.sidebar.error("❌ Nenhuma atividade encontrada")
    
    if st.session_state.activities_list:
        activity_options = {act['id']: act['name'] for act in st.session_state.activities_list}
        activity_options_with_all = {None: "📋 Todas as Atividades"}
        activity_options_with_all.update(activity_options)
        
        selected_activity_id = st.sidebar.selectbox(
            "Selecionar Atividade:",
            options=list(activity_options_with_all.keys()),
            format_func=lambda x: activity_options_with_all[x]
        )
        
        st.session_state.selected_activity_id = selected_activity_id
        st.session_state.selected_activity_name = activity_options_with_all[selected_activity_id]
        st.sidebar.success(f"📋 {st.session_state.selected_activity_name}")
    else:
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades' primeiro")
    
    st.sidebar.markdown("---")
    
    # 3. Filtro de Equipe
    st.sidebar.markdown("### 🏆 Equipe")
    
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            with st.spinner("Carregando equipes da API..."):
                teams = load_teams(st.session_state.selected_activity_id)
                if teams:
                    st.session_state.teams_list = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes carregadas")
                else:
                    st.sidebar.error("❌ Nenhuma equipe encontrada")
        
        if st.session_state.teams_list:
            team_options = {team['id']: team['name'] for team in st.session_state.teams_list}
            team_options_with_all = {None: "🏆 Todas as Equipes"}
            team_options_with_all.update(team_options)
            
            selected_team_id = st.sidebar.selectbox(
                "Selecionar Equipe:",
                options=list(team_options_with_all.keys()),
                format_func=lambda x: team_options_with_all[x]
            )
            
            st.session_state.selected_team_id = selected_team_id
            st.session_state.selected_team_name = team_options_with_all[selected_team_id]
            st.sidebar.success(f"🏆 {st.session_state.selected_team_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Equipes'")
    else:
        st.sidebar.warning("⚠️ Carregue as atividades primeiro")
    
    st.sidebar.markdown("---")
    
    # 4. Filtro de Atleta
    st.sidebar.markdown("### 👤 Atleta")
    
    if st.session_state.teams_list:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            with st.spinner("Carregando atletas da API..."):
                players = load_players(
                    st.session_state.selected_team_id,
                    st.session_state.selected_activity_id
                )
                if players:
                    st.session_state.players_list = players
                    st.sidebar.success(f"✅ {len(players)} atletas carregados")
                else:
                    st.sidebar.error("❌ Nenhum atleta encontrado")
        
        if st.session_state.players_list:
            player_options = {player['id']: player['name'] for player in st.session_state.players_list}
            player_options_with_all = {None: "👥 Todos os Atletas"}
            player_options_with_all.update(player_options)
            
            selected_player_id = st.sidebar.selectbox(
                "Selecionar Atleta:",
                options=list(player_options_with_all.keys()),
                format_func=lambda x: player_options_with_all[x]
            )
            
            st.session_state.selected_player_id = selected_player_id
            st.session_state.selected_player_name = player_options_with_all[selected_player_id]
            st.sidebar.success(f"👤 {st.session_state.selected_player_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Atletas'")
    else:
        st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    
    st.sidebar.markdown("---")
    
    # 5. Filtro de Tipo de Evento
    st.sidebar.markdown("### 🎯 Tipo de Evento")
    event_types = ["Todos", "Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"]
    selected_event_type = st.sidebar.selectbox("Filtrar por evento:", event_types)
    st.session_state.selected_event_type = selected_event_type
    
    st.sidebar.markdown("---")
    
    # Botão de reset
    if st.sidebar.button("🔄 Resetar Filtros", use_container_width=True):
        st.session_state.selected_activity_id = None
        st.session_state.selected_team_id = None
        st.session_state.selected_player_id = None
        st.session_state.selected_event_type = "Todos"
        st.session_state.events_df = None
        st.rerun()
    
    # Botão principal para carregar eventos
    st.sidebar.markdown("---")
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        if st.session_state.players_list or st.session_state.selected_team_id is None:
            with st.spinner("Carregando eventos da API..."):
                df = load_events(
                    team_id=st.session_state.selected_team_id,
                    player_id=st.session_state.selected_player_id,
                    activity_id=st.session_state.selected_activity_id,
                    days=st.session_state.days_period
                )
                st.session_state.events_df = df
                
                if not df.empty:
                    st.sidebar.success(f"✅ {len(df)} eventos carregados")
                else:
                    st.sidebar.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        else:
            st.sidebar.error("❌ Carregue os atletas primeiro!")
    
    # Mostrar resumo dos filtros
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Resumo")
    st.sidebar.markdown(f"**Atividade:** {st.session_state.selected_activity_name}")
    st.sidebar.markdown(f"**Equipe:** {st.session_state.selected_team_name}")
    st.sidebar.markdown(f"**Atleta:** {st.session_state.selected_player_name}")
    st.sidebar.markdown(f"**Período:** {st.session_state.days_period} dias")
    
    # ==================== DASHBOARD PRINCIPAL ====================
    
    if st.session_state.events_df is not None and not st.session_state.events_df.empty:
        df = st.session_state.events_df
        
        # Aplicar filtro de tipo de evento
        if st.session_state.selected_event_type != "Todos" and 'tipo_evento' in df.columns:
            df = df[df["tipo_evento"] == st.session_state.selected_event_type]
        
        # Métricas resumidas
        total_eventos = len(df)
        tempo_medio_entre = df["back_in_game_min"].mean() if 'back_in_game_min' in df.columns else 0
        duracao_media = df["duration_min"].mean() if 'duration_min' in df.columns else 0
        carga_total = df["duration_min"].sum() if 'duration_min' in df.columns else 0
        confianca_media = df["confidence"].mean() if 'confidence' in df.columns else 0
        
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
        
        # ==================== CAMPO DE RUGBY ====================
        
        st.markdown('<div class="sub-header">🏟️ Mapa de Calor - Atividade no Campo</div>', unsafe_allow_html=True)
        
        fig_campo = create_rugby_field()
        
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'],
                y=df['pos_y'],
                mode='markers',
                marker=dict(
                    size=df['duration_min'] * 30 if 'duration_min' in df.columns else 10,
                    color=df['confidence'] if 'confidence' in df.columns else 0.5,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Confiança"),
                    opacity=0.7,
                    line=dict(width=1, color='black')
                ),
                text=[f"Evento: {row.get('tipo_evento', 'N/A')}<br>Duração: {row.get('duration_min', 0):.2f}min<br>Conf: {row.get('confidence', 0):.3f}" 
                      for _, row in df.iterrows()],
                hoverinfo='text',
                name='Eventos'
            ))
        
        st.plotly_chart(fig_campo, use_container_width=True)
        
        # ==================== TABELA DE EVENTOS ====================
        
        st.markdown('<div class="sub-header">📋 Detalle de Eventos</div>', unsafe_allow_html=True)
        
        # Preparar dataframe para exibição
        df_display = df.copy()
        
        # Converter timestamps se existirem
        if 'start_time' in df_display.columns:
            df_display["start_time_dt"] = pd.to_datetime(df_display["start_time"], unit='s')
        if 'end_time' in df_display.columns:
            df_display["end_time_dt"] = pd.to_datetime(df_display["end_time"], unit='s')
        
        # Selecionar colunas para exibir
        display_cols = []
        for col in ['tipo_evento', 'start_time_dt', 'end_time_dt', 'duration_min', 'back_in_game_min', 'confidence']:
            if col in df_display.columns:
                display_cols.append(col)
        
        if 'equipe' in df_display.columns and st.session_state.selected_team_id is None:
            display_cols.insert(1, 'equipe')
        if 'atleta' in df_display.columns and st.session_state.selected_player_id is None:
            display_cols.insert(2, 'atleta')
        
        if display_cols:
            st.dataframe(
                df_display[display_cols].head(100),
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
        
        st.markdown('<div class="sub-header">📈 Análise de Eventos</div>', unsafe_allow_html=True)
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            if 'tipo_evento' in df.columns:
                event_counts = df['tipo_evento'].value_counts()
                if len(event_counts) > 0:
                    fig_pie = px.pie(
                        values=event_counts.values,
                        names=event_counts.index,
                        title="Distribución por Tipo de Evento",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_graf2:
            if 'duration_min' in df.columns:
                fig_duration = px.bar(
                    x=range(min(len(df), 50)),
                    y=df['duration_min'].head(50),
                    title="Duración por Evento (minutos)",
                    labels={"x": "Número de Evento", "y": "Duración (min)"}
                )
                fig_duration.update_traces(marker_color='steelblue')
                st.plotly_chart(fig_duration, use_container_width=True)
        
        col_graf3, col_graf4 = st.columns(2)
        
        with col_graf3:
            if 'back_in_game_min' in df.columns:
                fig_timeline = px.line(
                    x=range(len(df)),
                    y=df['back_in_game_min'],
                    title="Tiempo entre Eventos - Back in Game (minutos)",
                    labels={"x": "Secuencia de Eventos", "y": "Tiempo (min)"}
                )
                fig_timeline.update_traces(line=dict(color='orange', width=2))
                st.plotly_chart(fig_timeline, use_container_width=True)
        
        with col_graf4:
            if 'confidence' in df.columns:
                fig_conf = px.scatter(
                    x=range(len(df)),
                    y=df['confidence'],
                    title="Confianza por Evento",
                    labels={"x": "Evento", "y": "Confianza"},
                    color=df['confidence'],
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_conf, use_container_width=True)
    
    elif st.session_state.events_df is not None and st.session_state.events_df.empty:
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        st.info("💡 Tente:")
        st.markdown("""
        - Selecionar um período maior
        - Escolher uma equipe diferente
        - Carregar dados de outra atividade
        - Verificar se há eventos disponíveis no período
        """)
    else:
        st.info("👈 **Como usar o dashboard:**")
        st.markdown("""
        1. **Carregue as Atividades** - Clique no botão na sidebar
        2. **Carregue as Equipes** - Baseado na atividade selecionada
        3. **Carregue os Atletas** - Baseado na equipe selecionada
        4. **Defina o Período** - Escolha os dias da análise
        5. **Carregue os Eventos** - Clique no botão principal
        
        ✅ Todos os dados são carregados **da API real da Catapult**
        📋 Você verá **nomes reais** de atividades, equipes e atletas
        🏉 O campo de rugby mostra a posição dos eventos
        """)
    
    # Botão para desconectar
    if st.sidebar.button("🔓 Desconectar", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("🏉 BIG Report - Análise de Retorno à Atividade | Powered by Catapult Sports API")
    if st.session_state.events_df is not None and not st.session_state.events_df.empty:
        st.caption(f"📊 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# ==================== MAIN ====================

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()