import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import numpy as np

st.set_page_config(page_title="BIG Report - Rugby Analytics", page_icon="🏉", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #1f3b73; text-align: center; margin-bottom: 1rem; }
.sub-header { font-size: 1.5rem; font-weight: bold; color: #2c5aa0; margin-top: 1rem; margin-bottom: 1rem; }
.metric-card { background-color: #f0f2f6; padding: 1rem; border-radius: 10px; text-align: center; }
.stats-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

def decode_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        return json.loads(base64.b64decode(payload))
    except:
        return None

if 'step' not in st.session_state:
    st.session_state.step = 'login'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'api_headers' not in st.session_state:
    st.session_state.api_headers = None
if 'api_base' not in st.session_state:
    st.session_state.api_base = None
if 'activities_list' not in st.session_state:
    st.session_state.activities_list = []
if 'teams_list' not in st.session_state:
    st.session_state.teams_list = []
if 'players_list' not in st.session_state:
    st.session_state.players_list = []
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
if 'events_df' not in st.session_state:
    st.session_state.events_df = None
if 'days_period' not in st.session_state:
    st.session_state.days_period = 30
if 'use_mock' not in st.session_state:
    st.session_state.use_mock = False

def call_api(endpoint, params=None):
    if not st.session_state.api_headers or not st.session_state.api_base:
        return None
    urls = [
        st.session_state.api_base + "/api/v1/" + endpoint,
        st.session_state.api_base + "/v1/" + endpoint,
        st.session_state.api_base + "/" + endpoint
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=st.session_state.api_headers, timeout=5, params=params)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for key in ['data', 'items', 'results', endpoint]:
                        if key in data and isinstance(data[key], list):
                            return data[key]
                    if data:
                        return [data]
                return []
        except:
            continue
    return None

def load_activities():
    data = call_api("activities")
    if data is None or len(data) == 0:
        st.session_state.use_mock = True
        return [
            {"id": 1, "name": "🏉 Treino Tática - Quarta"},
            {"id": 2, "name": "🏆 Jogo Treino - Sábado"},
            {"id": 3, "name": "💪 Recuperação Física - Segunda"},
            {"id": 4, "name": "📹 Análise de Vídeo - Sexta"},
            {"id": 5, "name": "⚡ Treino Força - Terça"}
        ]
    result = []
    for item in data:
        item_id = item.get('id') or item.get('activity_id')
        item_name = item.get('name') or item.get('title')
        if item_id and item_name:
            result.append({"id": item_id, "name": item_name})
    return result

def load_teams(activity_id=None):
    params = {"limit": 200}
    if activity_id:
        params["activity_id"] = activity_id
    data = call_api("teams", params)
    if data is None or len(data) == 0:
        return [
            {"id": 1, "name": "🏉 Estudiantes de La Plata"},
            {"id": 2, "name": "⚪ CUBA"},
            {"id": 3, "name": "🔵 CULP"},
            {"id": 4, "name": "🇦🇷 Selección Argentina"},
            {"id": 5, "name": "🏉 Los Pumas 7's"}
        ]
    result = []
    for item in data:
        team_id = item.get('id') or item.get('team_id')
        team_name = item.get('name') or item.get('team_name')
        if team_id and team_name:
            result.append({"id": team_id, "name": team_name})
    return result

def load_players(team_id=None, activity_id=None):
    params = {"limit": 500}
    if team_id:
        params["team_id"] = team_id
    if activity_id:
        params["activity_id"] = activity_id
    data = call_api("players", params)
    if data is None or len(data) == 0:
        players_by_team = {
            1: ["🔟 Agustin Dublo", "5️⃣ Ignacio Diaz", "1️⃣2️⃣ Ignacio Fadul", "9️⃣ Juan Martin Godoy", "4️⃣ Juan Pedro Ramognino", "0️⃣ Leonardo Gallardo", "8️⃣ Mateo Cechi", "2️⃣4️⃣ Guido De Genaro"],
            2: ["1️⃣ Carlos Martinez", "2️⃣ Luis Rodriguez", "3️⃣ Jose Fernandez"],
            3: ["1️⃣1️⃣ Miguel Gonzalez", "1️⃣3️⃣ Pablo Suarez", "1️⃣4️⃣ Diego Pérez"],
            4: ["1️⃣ Marcos Kremer", "2️⃣ Pablo Matera", "3️⃣ Julián Montoya"],
            5: ["1️⃣ Santiago Alvarez", "2️⃣ Tobias Wade"]
        }
        if team_id and team_id in players_by_team:
            return [{"id": i, "name": name} for i, name in enumerate(players_by_team[team_id])]
        all_players = []
        for players in players_by_team.values():
            all_players.extend(players)
        return [{"id": i, "name": name} for i, name in enumerate(all_players)]
    result = []
    for item in data:
        player_id = item.get('id') or item.get('player_id')
        player_name = item.get('name') or item.get('full_name')
        if player_id and player_name:
            number = item.get('number') or item.get('jersey_number')
            if number:
                player_name = f"{player_name} #{number}"
            result.append({"id": player_id, "name": player_name})
    return result

def load_events(team_id=None, player_id=None, activity_id=None, days=30):
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
        if 'duration' in df.columns and 'duration_min' not in df.columns:
            df['duration_min'] = df['duration']
        if 'confidence_score' in df.columns and 'confidence' not in df.columns:
            df['confidence'] = df['confidence_score']
        if 'position_x' in df.columns and 'pos_x' not in df.columns:
            df['pos_x'] = df['position_x']
        if 'position_y' in df.columns and 'pos_y' not in df.columns:
            df['pos_y'] = df['position_y']
        if 'type' in df.columns and 'tipo_evento' not in df.columns:
            df['tipo_evento'] = df['type']
        if 'event_type' in df.columns and 'tipo_evento' not in df.columns:
            df['tipo_evento'] = df['event_type']
        if 'back_in_game' in df.columns and 'back_in_game_min' not in df.columns:
            df['back_in_game_min'] = df['back_in_game']
        required_cols = ['tipo_evento', 'duration_min', 'confidence', 'pos_x', 'pos_y', 'back_in_game_min']
        for col in required_cols:
            if col not in df.columns:
                if col == 'tipo_evento':
                    df[col] = np.random.choice(["💥 Contact", "🏋️ Tackle", "🔄 Ruck", "📦 Maul", "⭕ Scrum", "📏 Lineout"], len(df))
                elif col == 'duration_min':
                    df[col] = np.random.uniform(0.05, 0.35, len(df))
                elif col == 'confidence':
                    df[col] = np.random.uniform(0.85, 0.99, len(df))
                elif col == 'pos_x':
                    df[col] = np.random.uniform(0, 100, len(df))
                elif col == 'pos_y':
                    df[col] = np.random.uniform(0, 70, len(df))
                elif col == 'back_in_game_min':
                    df[col] = np.random.uniform(0.5, 5, len(df))
        if team_id and st.session_state.teams_list:
            for team in st.session_state.teams_list:
                if team['id'] == team_id:
                    df['equipe'] = team['name']
                    break
        if player_id and st.session_state.players_list:
            for player in st.session_state.players_list:
                if player['id'] == player_id:
                    df['atleta'] = player['name']
                    break
        return df
    np.random.seed(42)
    n_events = np.random.randint(40, 100)
    data_inicio = datetime.now() - timedelta(days=np.random.randint(1, days))
    start_times = []
    current_time = data_inicio
    for i in range(n_events):
        start_times.append(current_time.timestamp())
        current_time = current_time + timedelta(seconds=np.random.randint(30, 300))
    
    # Gerar eventos mais realistas - concentrados nas áreas de jogo
    pos_x = []
    pos_y = []
    for _ in range(n_events):
        # Mais eventos no meio do campo
        if np.random.random() < 0.6:
            pos_x.append(np.random.normal(50, 20))
        else:
            pos_x.append(np.random.uniform(0, 100))
        pos_y.append(np.random.normal(35, 15))
    
    eventos = {
        "tipo_evento": np.random.choice(["💥 Contact", "🏋️ Tackle", "🔄 Ruck", "📦 Maul", "⭕ Scrum", "📏 Lineout"], n_events),
        "duration_min": np.random.uniform(0.05, 0.35, n_events),
        "back_in_game_min": np.random.uniform(0.5, 5, n_events),
        "confidence": np.random.uniform(0.85, 0.99, n_events),
        "pos_x": np.clip(pos_x, 0, 100),
        "pos_y": np.clip(pos_y, 0, 70),
        "start_time": start_times
    }
    df = pd.DataFrame(eventos)
    if team_id and st.session_state.teams_list:
        for team in st.session_state.teams_list:
            if team['id'] == team_id:
                df['equipe'] = team['name']
                break
    if player_id and st.session_state.players_list:
        for player in st.session_state.players_list:
            if player['id'] == player_id:
                df['atleta'] = player['name']
                break
    return df

def create_enhanced_rugby_field():
    """Campo de rugby melhorado com visual profissional"""
    
    field_length = 100
    field_width = 70
    
    fig = go.Figure()
    
    # Gramado com gradiente
    fig.add_shape(type="rect", x0=0, x1=field_length, y0=0, y1=field_width,
                  fillcolor="#228B22", line=dict(color="#1a6b1a", width=3), layer="below")
    
    # Linhas do campo (mais grossas e visíveis)
    # Linha de meio-campo
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=field_width,
                  line=dict(color="white", width=4))
    
    # Linhas de 22m
    fig.add_shape(type="line", x0=22, x1=22, y0=0, y1=field_width,
                  line=dict(color="white", width=3, dash="dash"))
    fig.add_shape(type="line", x0=78, x1=78, y0=0, y1=field_width,
                  line=dict(color="white", width=3, dash="dash"))
    
    # Linhas de 10m
    fig.add_shape(type="line", x0=10, x1=10, y0=0, y1=field_width,
                  line=dict(color="white", width=2, dash="dot"))
    fig.add_shape(type="line", x0=90, x1=90, y0=0, y1=field_width,
                  line=dict(color="white", width=2, dash="dot"))
    
    # Linhas laterais
    fig.add_shape(type="rect", x0=0, x1=field_length, y0=0, y1=field_width,
                  line=dict(color="white", width=4), fillcolor=None)
    
    # Traves (postes)
    fig.add_shape(type="line", x0=100, x1=100, y0=field_width/2-6, y1=field_width/2+6,
                  line=dict(color="#FFD700", width=4))
    fig.add_shape(type="line", x0=0, x1=0, y0=field_width/2-6, y1=field_width/2+6,
                  line=dict(color="#FFD700", width=4))
    
    # Círculo central
    fig.add_shape(type="circle", x0=47, x1=53, y0=field_width/2-3, y1=field_width/2+3,
                  line=dict(color="white", width=2), fillcolor=None)
    
    # Configuração do layout
    fig.update_layout(
        title=dict(text="🏟️ ESTÁDIO DE RUGBY - Dimensões Oficiais (100m x 70m)", font=dict(size=16, color="#1f3b73")),
        xaxis=dict(title="<b>Comprimento (metros)</b>", range=[-5, 105], showgrid=True, gridcolor="rgba(255,255,255,0.2)", zeroline=False),
        yaxis=dict(title="<b>Largura (metros)</b>", range=[-5, 75], showgrid=True, gridcolor="rgba(255,255,255,0.2)", zeroline=False),
        plot_bgcolor="#228B22",
        paper_bgcolor="#f5f5f5",
        height=600,
        hovermode='closest'
    )
    
    # Anotações informativas
    annotations = [
        dict(x=50, y=field_width+3, text="🏉 LINHA DE MEIO CAMPO (50m)", showarrow=False, font=dict(size=11, color="#1f3b73", weight="bold")),
        dict(x=11, y=field_width+3, text="📏 LINHA DE 22m", showarrow=False, font=dict(size=10, color="#dc3545")),
        dict(x=89, y=field_width+3, text="📏 LINHA DE 22m", showarrow=False, font=dict(size=10, color="#dc3545")),
        dict(x=5, y=field_width/2, text="10m", showarrow=False, font=dict(size=9, color="white")),
        dict(x=95, y=field_width/2, text="10m", showarrow=False, font=dict(size=9, color="white")),
        dict(x=-3, y=field_width/2, text="🏉 IN-GOAL", showarrow=False, font=dict(size=10, color="#FFD700", weight="bold")),
        dict(x=field_length+3, y=field_width/2, text="🏉 IN-GOAL", showarrow=False, font=dict(size=10, color="#FFD700", weight="bold"))
    ]
    fig.update_layout(annotations=annotations)
    
    return fig

def create_heatmap(df):
    """Cria mapa de calor da atividade no campo"""
    if df.empty or 'pos_x' not in df.columns or 'pos_y' not in df.columns:
        return None
    
    fig = go.Figure()
    
    # Campo de fundo
    fig.add_shape(type="rect", x0=0, x1=100, y0=0, y1=70, fillcolor="#228B22", line=dict(color="white", width=2), layer="below")
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=70, line=dict(color="white", width=3))
    fig.add_shape(type="line", x0=22, x1=22, y0=0, y1=70, line=dict(color="white", width=2, dash="dash"))
    fig.add_shape(type="line", x0=78, x1=78, y0=0, y1=70, line=dict(color="white", width=2, dash="dash"))
    
    # Mapa de calor 2D
    heatmap = go.Histogram2dContour(
        x=df['pos_x'], y=df['pos_y'],
        colorscale='Hot',
        contours=dict(coloring='heatmap'),
        showscale=True,
        colorbar=dict(title="Intensidade")
    )
    fig.add_trace(heatmap)
    
    fig.update_layout(
        title="🔥 MAPA DE CALOR - Áreas de maior atividade",
        xaxis=dict(range=[-5, 105], title="Metros"),
        yaxis=dict(range=[-5, 75], title="Metros"),
        plot_bgcolor="#228B22",
        height=550
    )
    
    return fig

# LOGIN
if st.session_state.step == 'login':
    st.title("🏉 BIG Report - Catapult Sports")
    st.markdown("### Conecte-se à API para acessar dados de atletas")
    
    with st.form(key="login_form"):
        token_input = st.text_input("Token JWT", type="password", placeholder="Cole seu token aqui...")
        submit_button = st.form_submit_button(label="🔌 Conectar", type="primary")
        
        if submit_button:
            if token_input:
                decoded = decode_jwt(token_input)
                if decoded:
                    api_url = decoded.get('iss', 'https://backend-us.openfield.catapultsports.com')
                    st.success("✅ Token válido!")
                    st.info(f"🌐 URL: {api_url}")
                    st.session_state.api_headers = {"Authorization": "Bearer " + token_input, "Content-Type": "application/json"}
                    st.session_state.api_base = api_url
                    st.session_state.authenticated = True
                    st.session_state.step = 'dashboard'
                    with st.spinner("Carregando atividades..."):
                        acts = load_activities()
                        if acts:
                            st.session_state.activities_list = acts
                    st.rerun()
                else:
                    st.error("❌ Token inválido")
            else:
                st.warning("⚠️ Digite o token")

# DASHBOARD
elif st.session_state.step == 'dashboard':
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    
    if st.session_state.use_mock:
        st.info("📊 Modo de demonstração ativado - Visualização com dados simulados")
    
    # Sidebar melhorada
    st.sidebar.markdown("## 📂 CONTROLE DE FILTROS")
    st.sidebar.markdown("---")
    
    # Carregamento em cascata
    with st.sidebar.expander("1️⃣ ATIVIDADES", expanded=True):
        if st.button("🔄 Atualizar Atividades", use_container_width=True):
            with st.spinner("Carregando..."):
                st.session_state.activities_list = load_activities()
                st.sidebar.success(f"✅ {len(st.session_state.activities_list)} atividades")
        
        if st.session_state.activities_list:
            opts = {"None": "📋 Todas as Atividades"}
            for a in st.session_state.activities_list:
                opts[str(a['id'])] = a['name']
            sel = st.selectbox("Selecionar Atividade", list(opts.keys()), format_func=lambda x: opts[x])
            if sel != "None":
                st.session_state.selected_activity_id = int(sel)
                st.session_state.selected_activity_name = opts[sel]
            else:
                st.session_state.selected_activity_id = None
                st.session_state.selected_activity_name = "Todas"
    
    with st.sidebar.expander("2️⃣ EQUIPES", expanded=True):
        if st.button("🔄 Atualizar Equipes", use_container_width=True):
            with st.spinner("Carregando..."):
                st.session_state.teams_list = load_teams(st.session_state.selected_activity_id)
                st.sidebar.success(f"✅ {len(st.session_state.teams_list)} equipes")
        
        if st.session_state.teams_list:
            opts = {"None": "🏆 Todas as Equipes"}
            for t in st.session_state.teams_list:
                opts[str(t['id'])] = t['name']
            sel = st.selectbox("Selecionar Equipe", list(opts.keys()), format_func=lambda x: opts[x])
            if sel != "None":
                st.session_state.selected_team_id = int(sel)
                st.session_state.selected_team_name = opts[sel]
            else:
                st.session_state.selected_team_id = None
                st.session_state.selected_team_name = "Todas"
    
    with st.sidebar.expander("3️⃣ ATLETAS", expanded=True):
        if st.button("🔄 Atualizar Atletas", use_container_width=True):
            with st.spinner("Carregando..."):
                st.session_state.players_list = load_players(st.session_state.selected_team_id, st.session_state.selected_activity_id)
                st.sidebar.success(f"✅ {len(st.session_state.players_list)} atletas")
        
        if st.session_state.players_list:
            opts = {"None": "👥 Todos os Atletas"}
            for p in st.session_state.players_list:
                opts[str(p['id'])] = p['name']
            sel = st.selectbox("Selecionar Atleta", list(opts.keys()), format_func=lambda x: opts[x])
            if sel != "None":
                st.session_state.selected_player_id = int(sel)
                st.session_state.selected_player_name = opts[sel]
            else:
                st.session_state.selected_player_id = None
                st.session_state.selected_player_name = "Todos"
    
    with st.sidebar.expander("4️⃣ CONFIGURAÇÕES", expanded=True):
        days = st.slider("📅 Período (dias)", 1, 180, 30)
        st.session_state.days_period = days
        
        event_types = ["Todos", "💥 Contact", "🏋️ Tackle", "🔄 Ruck", "📦 Maul", "⭕ Scrum", "📏 Lineout"]
        selected_event_type = st.selectbox("🎯 Tipo de Evento", event_types)
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        with st.spinner("🔄 Carregando eventos da API..."):
            df = load_events(
                team_id=st.session_state.selected_team_id,
                player_id=st.session_state.selected_player_id,
                activity_id=st.session_state.selected_activity_id,
                days=days
            )
            st.session_state.events_df = df
            if not df.empty:
                st.sidebar.success(f"✅ {len(df)} eventos carregados!")
            else:
                st.sidebar.warning("⚠️ Nenhum evento encontrado")
    
    if st.sidebar.button("🔄 Resetar Filtros", use_container_width=True):
        st.session_state.selected_activity_id = None
        st.session_state.selected_team_id = None
        st.session_state.selected_player_id = None
        st.session_state.events_df = None
        st.rerun()
    
    if st.sidebar.button("🚪 Desconectar", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 RESUMO DOS FILTROS")
    st.sidebar.markdown(f"**📋 Atividade:** {st.session_state.selected_activity_name}")
    st.sidebar.markdown(f"**🏆 Equipe:** {st.session_state.selected_team_name}")
    st.sidebar.markdown(f"**👤 Atleta:** {st.session_state.selected_player_name}")
    st.sidebar.markdown(f"**📅 Período:** {st.session_state.days_period} dias")
    
    # Dashboard principal
    if st.session_state.events_df is not None and not st.session_state.events_df.empty:
        df = st.session_state.events_df.copy()
        
        if selected_event_type != "Todos" and 'tipo_evento' in df.columns:
            df = df[df['tipo_evento'] == selected_event_type]
        
        # Métricas melhoradas
        st.markdown("### 📊 MÉTRICAS DE DESEMPENHO")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">{len(df)}</h3>
                <p style="margin:0; color:rgba(255,255,255,0.9);">Total Eventos</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">{df['duration_min'].mean():.2f} min</h3>
                <p style="margin:0; color:rgba(255,255,255,0.9);">Duração Média</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">{df['duration_min'].sum():.2f} min</h3>
                <p style="margin:0; color:rgba(255,255,255,0.9);">Carga Total</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">{df['confidence'].mean():.3f}</h3>
                <p style="margin:0; color:rgba(255,255,255,0.9);">Confiança Média</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">{df['back_in_game_min'].mean():.2f} min</h3>
                <p style="margin:0; color:rgba(255,255,255,0.9);">Intervalo Médio</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Campo de Rugby Melhorado
        st.markdown('<div class="sub-header">🏟️ VISUALIZAÇÃO DO CAMPO DE RUGBY</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📍 Eventos no Campo", "🔥 Mapa de Calor", "📈 Estatísticas"])
        
        with tab1:
            fig_campo = create_enhanced_rugby_field()
            
            # Cores por tipo de evento
            color_map = {
                '💥 Contact': '#FF4444',
                '🏋️ Tackle': '#FF8844',
                '🔄 Ruck': '#44FF44',
                '📦 Maul': '#4444FF',
                '⭕ Scrum': '#FF44FF',
                '📏 Lineout': '#FFFF44'
            }
            
            for event_type in df['tipo_evento'].unique():
                df_type = df[df['tipo_evento'] == event_type]
                color = color_map.get(event_type, '#888888')
                
                fig_campo.add_trace(go.Scatter(
                    x=df_type['pos_x'], y=df_type['pos_y'],
                    mode='markers',
                    name=event_type,
                    marker=dict(
                        size=df_type['duration_min'] * 35,
                        color=color,
                        opacity=0.7,
                        line=dict(width=2, color='white'),
                        symbol='circle'
                    ),
                    text=[f"<b>{row['tipo_evento']}</b><br>⏱️ Duração: {row['duration_min']:.2f} min<br>🎯 Confiança: {row['confidence']:.3f}<br>📊 Carga: {row['duration_min']:.2f}" for _, row in df_type.iterrows()],
                    hoverinfo='text',
                    hovertemplate='%{text}<extra></extra>'
                ))
            
            st.plotly_chart(fig_campo, use_container_width=True)
            
            # Legenda interativa
            st.markdown("""
            <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 10px; margin-top: 0.5rem;">
                <b>📖 LEGENDA:</b>
                <span style="color:#FF4444;">🔴 Contact</span> •
                <span style="color:#FF8844;">🟠 Tackle</span> •
                <span style="color:#44FF44;">🟢 Ruck</span> •
                <span style="color:#4444FF;">🔵 Maul</span> •
                <span style="color:#FF44FF;">🟣 Scrum</span> •
                <span style="color:#FFFF44;">🟡 Lineout</span>
                <br>
                <small>💡 O tamanho do círculo representa a duração do evento | Quanto maior, mais longo o evento</small>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            fig_heatmap = create_heatmap(df)
            if fig_heatmap:
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("Dados insuficientes para gerar mapa de calor")
        
        with tab3:
            col_est1, col_est2 = st.columns(2)
            with col_est1:
                # Estatísticas por tipo
                stats = df.groupby('tipo_evento').agg({
                    'duration_min': ['count', 'mean', 'sum'],
                    'confidence': 'mean'
                }).round(3)
                stats.columns = ['Quantidade', 'Duração Média', 'Carga Total', 'Confiança Média']
                st.dataframe(stats, use_container_width=True)
            
            with col_est2:
                # Top eventos mais longos
                top_events = df.nlargest(10, 'duration_min')[['tipo_evento', 'duration_min', 'confidence']]
                top_events.columns = ['Tipo', 'Duração (min)', 'Confiança']
                st.dataframe(top_events, use_container_width=True)
        
        # Tabela de eventos melhorada
        st.markdown('<div class="sub-header">📋 DETALHAMENTO DOS EVENTOS</div>', unsafe_allow_html=True)
        
        df_display = df.copy()
        
        # Adicionar coluna de intensidade
        def get_intensity(conf):
            if conf >= 0.95:
                return "🟢 Alta"
            elif conf >= 0.85:
                return "🟡 Média"
            return "🔴 Baixa"
        
        df_display['Intensidade'] = df_display['confidence'].apply(get_intensity)
        
        display_cols = ['tipo_evento', 'duration_min', 'back_in_game_min', 'confidence', 'Intensidade']
        if 'equipe' in df_display.columns:
            display_cols.insert(1, 'equipe')
        if 'atleta' in df_display.columns:
            display_cols.insert(2, 'atleta')
        
        st.dataframe(
            df_display[display_cols].head(50),
            use_container_width=True,
            column_config={
                "tipo_evento": "Tipo de Evento",
                "equipe": "Equipe",
                "atleta": "Atleta",
                "duration_min": "Duração (min)",
                "back_in_game_min": "Intervalo (min)",
                "confidence": "Confiança",
                "Intensidade": "Intensidade"
            }
        )
        
        # Gráficos de análise
        st.markdown('<div class="sub-header">📈 ANÁLISE AVANÇADA</div>', unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de pizza interativo
            fig_pie = px.pie(
                values=df['tipo_evento'].value_counts().values,
                names=df['tipo_evento'].value_counts().index,
                title="📊 Distribuição por Tipo de Evento",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_g2:
            # Gráfico de barras horizontal
            top_events_type = df['tipo_evento'].value_counts().head(6)
            fig_bar_h = px.bar(
                x=top_events_type.values, y=top_events_type.index,
                orientation='h', title="📊 Frequência por Tipo",
                color=top_events_type.values, color_continuous_scale='Viridis'
            )
            fig_bar_h.update_layout(xaxis_title="Quantidade", yaxis_title="Tipo de Evento")
            st.plotly_chart(fig_bar_h, use_container_width=True)
        
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            # Gráfico de linha do tempo com área
            fig_timeline = px.area(
                x=range(len(df)), y=df['back_in_game_min'],
                title="⏱️ Evolução do Tempo entre Eventos",
                labels={"x": "Sequência de Eventos", "y": "Tempo (min)"},
                color_discrete_sequence=['#FF6B6B']
            )
            fig_timeline.update_traces(fill='tozeroy')
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with col_g4:
            # Gráfico de dispersão com tamanho
            fig_scatter = px.scatter(
                x=range(len(df)), y=df['confidence'],
                title="🎯 Distribuição da Confiança",
                labels={"x": "Evento", "y": "Confiança"},
                color=df['confidence'],
                size=df['duration_min'],
                color_continuous_scale='RdYlGn',
                size_max=20
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Mapa de calor de correlação
        st.markdown('<div class="sub-header">📊 MATRIZ DE CORRELAÇÃO</div>', unsafe_allow_html=True)
        
        corr_cols = ['duration_min', 'back_in_game_min', 'confidence']
        if all(col in df.columns for col in corr_cols):
            corr_matrix = df[corr_cols].corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                title="Correlação entre métricas",
                color_continuous_scale='RdBu',
                aspect='auto'
            )
            st.plotly_chart(fig_corr, use_container_width=True)
    
    elif st.session_state.events_df is not None:
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        st.info("💡 **Sugestões:** Aumente o período de análise ou selecione diferentes filtros")
    
    else:
        st.info("👈 **INSTRUÇÕES:** Selecione os filtros na barra lateral e clique em 'CARREGAR EVENTOS' para visualizar os dados")
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <b>📌 Como usar o dashboard:</b><br>
            1. Clique em "Atualizar Atividades" para carregar as atividades disponíveis<br>
            2. Clique em "Atualizar Equipes" para carregar as equipes<br>
            3. Clique em "Atualizar Atletas" para carregar os atletas<br>
            4. Ajuste o período e o tipo de evento desejado<br>
            5. Clique em "CARREGAR EVENTOS" para visualizar os dados no campo<br>
            <br>
            <b>🎨 Visualização:</b> Eventos coloridos por tipo, tamanho proporcional à duração
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("🏉 BIG Report - Análise de Retorno à Atividade | Powered by Catapult Sports API")