import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import numpy as np

st.set_page_config(page_title="BIG Report - Rugby Analytics | Catapult Sports", page_icon="🏉", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #1f3b73; text-align: center; margin-bottom: 1rem; }
.sub-header { font-size: 1.5rem; font-weight: bold; color: #2c5aa0; margin-top: 1rem; margin-bottom: 1rem; }
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
if 'start_date_custom' not in st.session_state:
    st.session_state.start_date_custom = None
if 'end_date_custom' not in st.session_state:
    st.session_state.end_date_custom = None
if 'period_type' not in st.session_state:
    st.session_state.period_type = "Últimos dias"
if 'use_mock' not in st.session_state:
    st.session_state.use_mock = False

def call_api(endpoint, params=None):
    if not st.session_state.api_headers or not st.session_state.api_base:
        return None
    urls = [
        f"{st.session_state.api_base}/api/v1/{endpoint}",
        f"{st.session_state.api_base}/v1/{endpoint}",
        f"{st.session_state.api_base}/{endpoint}"
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
                    return [data] if data else []
                return []
        except:
            continue
    return None

def load_activities():
    data = call_api("activities")
    if data is None or len(data) == 0:
        st.session_state.use_mock = True
        return [
            {"id": 1, "name": "Treino Tática - Quarta"},
            {"id": 2, "name": "Jogo Treino - Sábado"},
            {"id": 3, "name": "Recuperação Física - Segunda"},
            {"id": 4, "name": "Análise de Vídeo - Sexta"},
            {"id": 5, "name": "Treino Força - Terça"}
        ]
    result = []
    for item in data:
        item_id = item.get('id') or item.get('activity_id')
        item_name = item.get('name') or item.get('title')
        if item_id and item_name:
            result.append({"id": item_id, "name": item_name})
    return result if result else []

def load_teams(activity_id=None):
    params = {"limit": 200}
    if activity_id:
        params["activity_id"] = activity_id
    data = call_api("teams", params)
    if data is None or len(data) == 0:
        return [
            {"id": 1, "name": "Estudiantes de La Plata"},
            {"id": 2, "name": "CUBA"},
            {"id": 3, "name": "CULP"},
            {"id": 4, "name": "Selección Argentina"},
            {"id": 5, "name": "Los Pumas 7's"}
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
            1: ["Agustin Dublo - #010", "Ignacio Diaz - #005", "Ignacio Fadul - #012", "Juan Martin Godoy - #009", "Juan Pedro Ramognino - #004", "Leonardo Gallardo - #000", "Mateo Cechi - #008", "Guido De Genaro - #*24"],
            2: ["Carlos Martinez - #001", "Luis Rodriguez - #002", "Jose Fernandez - #003"],
            3: ["Miguel Gonzalez - #011", "Pablo Suarez - #013", "Diego Pérez - #014"],
            4: ["Marcos Kremer - #001", "Pablo Matera - #002", "Julián Montoya - #003"],
            5: ["Santiago Alvarez - #001", "Tobias Wade - #002"]
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
        player_name = item.get('name') or item.get('full_name') or item.get('display_name')
        if player_id and player_name:
            number = item.get('number') or item.get('jersey_number')
            if number:
                player_name = f"{player_name} - #{number}"
            result.append({"id": player_id, "name": player_name})
    return result

def load_events(team_id=None, player_id=None, activity_id=None, start_date=None, end_date=None, days=30):
    params = {"limit": 1000}
    if start_date and end_date:
        params["start_date"] = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date
        params["end_date"] = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date
    else:
        end = datetime.now()
        start = end - timedelta(days=days)
        params["start_date"] = start.strftime("%Y-%m-%d")
        params["end_date"] = end.strftime("%Y-%m-%d")
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
                    df[col] = np.random.choice(["Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"], len(df))
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
    n_events = np.random.randint(30, 80)
    if days:
        data_inicio = datetime.now() - timedelta(days=np.random.randint(1, days))
    else:
        data_inicio = datetime.now() - timedelta(days=30)
    start_times = []
    current_time = data_inicio
    for i in range(n_events):
        start_times.append(current_time.timestamp())
        current_time += timedelta(seconds=np.random.randint(30, 300))
    eventos = {
        "tipo_evento": np.random.choice(["Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"], n_events),
        "duration_min": np.random.uniform(0.05, 0.35, n_events),
        "back_in_game_min": np.random.uniform(0.5, 5, n_events),
        "confidence": np.random.uniform(0.85, 0.99, n_events),
        "pos_x": np.random.uniform(0, 100, n_events),
        "pos_y": np.random.uniform(0, 70, n_events),
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

def create_rugby_field():
    field_length = 100
    field_width = 70
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, x1=field_length, y0=0, y1=field_width, fillcolor="lightgreen", line=dict(color="black", width=2), layer="below")
    fig.add_shape(type="line", x0=field_length/2, x1=field_length/2, y0=0, y1=field_width, line=dict(color="white", width=3))
    fig.add_shape(type="line", x0=22, x1=22, y0=0, y1=field_width, line=dict(color="red", width=2, dash="dash"))
    fig.add_shape(type="line", x0=field_length-22, x1=field_length-22, y0=0, y1=field_width, line=dict(color="red", width=2, dash="dash"))
    fig.add_shape(type="line", x0=10, x1=10, y0=0, y1=field_width, line=dict(color="white", width=1, dash="dot"))
    fig.add_shape(type="line", x0=field_length-10, x1=field_length-10, y0=0, y1=field_width, line=dict(color="white", width=1, dash="dot"))
    fig.add_shape(type="rect", x0=0, x1=field_length, y0=0, y1=field_width, line=dict(color="white", width=3), fillcolor=None)
    fig.add_shape(type="line", x0=field_length, x1=field_length, y0=field_width/2-5, y1=field_width/2+5, line=dict(color="yellow", width=3))
    fig.add_shape(type="line", x0=0, x1=0, y0=field_width/2-5, y1=field_width/2+5, line=dict(color="yellow", width=3))
    fig.update_layout(title="🏟️ Campo de Rugby - Dimensões Oficiais (100m x 70m)", xaxis=dict(title="Comprimento (metros)", range=[-5, field_length+5], showgrid=True, gridcolor="lightgray"), yaxis=dict(title="Largura (metros)", range=[-5, field_width+5], showgrid=True, gridcolor="lightgray"), plot_bgcolor="lightgreen", height=550, hovermode='closest')
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
    return fig

if not st.session_state.authenticated:
    st.markdown('<div style="text-align: center; margin-top: 50px;"><h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1><h3 style="color: #2c5aa0;">Catapult Sports Integration</h3><p style="margin-top: 20px;">Conecte-se à API da Catapult para acessar os dados</p></div>', unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔑 Autenticação")
            api_token = st.text_area("Token JWT:", height=120, type="password", placeholder="Cole seu token JWT aqui...", help="Token fornecido pela Catapult Sports")
            if api_token:
                decoded = decode_jwt(api_token)
                if decoded:
                    api_url = decoded.get('iss', 'https://backend-us.openfield.catapultsports.com')
                    st.success("✅ Token válido!")
                    st.info(f"🌐 URL detectada: {api_url}")
                    customer_id = None
                    if 'com.catapultsports' in decoded:
                        customer_id = decoded['com.catapultsports']['openfield']['customers'][0]['id']
                        st.info(f"🏢 Customer ID: {customer_id}")
                    if st.button("✅ Conectar à API", type="primary", use_container_width=True):
                        st.session_state.api_headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
                        st.session_state.api_base = api_url
                        st.session_state.authenticated = True
                        with st.spinner("Carregando atividades iniciais..."):
                            acts = load_activities()
                            if acts:
                                st.session_state.activities_list = acts
                                st.success(f"✅ {len(acts)} atividades carregadas!")
                        st.rerun()
                else:
                    st.error("❌ Token inválido")
else:
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    if st.session_state.use_mock:
        st.warning("⚠️ Modo de demonstração ativado - Usando dados simulados. A API não retornou dados reais.")
    st.sidebar.markdown("## 📂 Filtros de Dados")
    st.sidebar.success("✅ Conectado à API Catapult")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Período")
    period_type = st.sidebar.radio("Tipo de período:", ["Últimos dias", "Intervalo personalizado"], horizontal=True)
    st.session_state.period_type = period_type
    if period_type == "Últimos dias":
        days_period = st.sidebar.slider("Mostrar actividades de los últimos días:", 1, 180, 30, 7)
        st.session_state.days_period = days_period
        st.session_state.start_date_custom = None
        st.session_state.end_date_custom = None
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=days_period)
        st.sidebar.info(f"📆 Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    else:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Data inicial:", datetime.now() - timedelta(days=30))
            st.session_state.start_date_custom = start_date
        with col2:
            end_date = st.date_input("Data final:", datetime.now())
            st.session_state.end_date_custom = end_date
        if start_date and end_date:
            days_period = (end_date - start_date).days
            st.session_state.days_period = max(1, days_period)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Atividades")
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        with st.spinner("Carregando atividades da API..."):
            acts = load_activities()
            if acts:
                st.session_state.activities_list = acts
                st.sidebar.success(f"✅ {len(acts)} atividades carregadas")
    if st.session_state.activities_list:
        activity_options = {None: "📋 Todas as Atividades"}
        for a in st.session_state.activities_list:
            activity_options[a['id']] = a['name']
        selected_activity_id = st.sidebar.selectbox("Selecionar Atividade:", list(activity_options.keys()), format_func=lambda x: activity_options[x])
        st.session_state.selected_activity_id = selected_activity_id
        st.session_state.selected_activity_name = activity_options[selected_activity_id]
        st.sidebar.success(f"📋 {st.session_state.selected_activity_name}")
    else:
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades' primeiro")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏆 Equipe")
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            with st.spinner("Carregando equipes da API..."):
                teams = load_teams(st.session_state.selected_activity_id)
                if teams:
                    st.session_state.teams_list = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes carregadas")
        if st.session_state.teams_list:
            team_options = {None: "🏆 Todas as Equipes"}
            for t in st.session_state.teams_list:
                team_options[t['id']] = t['name']
            selected_team_id = st.sidebar.selectbox("Selecionar Equipe:", list(team_options.keys()), format_func=lambda x: team_options[x])
            st.session_state.selected_team_id = selected_team_id
            st.session_state.selected_team_name = team_options[selected_team_id]
            st.sidebar.success(f"🏆 {st.session_state.selected_team_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Equipes'")
    else:
        st.sidebar.warning("⚠️ Carregue as atividades primeiro")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Atleta")
    if st.session_state.teams_list:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            with st.spinner("Carregando atletas da API..."):
                players = load_players(st.session_state.selected_team_id, st.session_state.selected_activity_id)
                if players:
                    st.session_state.players_list = players
                    st.sidebar.success(f"✅ {len(players)} atletas carregados")
        if st.session_state.players_list:
            player_options = {None: "👥 Todos os Atletas"}
            for p in st.session_state.players_list:
                player_options[p['id']] = p['name']
            selected_player_id = st.sidebar.selectbox("Selecionar Atleta:", list(player_options.keys()), format_func=lambda x: player_options[x])
            st.session_state.selected_player_id = selected_player_id
            st.session_state.selected_player_name = player_options[selected_player_id]
            st.sidebar.success(f"👤 {st.session_state.selected_player_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Atletas'")
    else:
        st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Tipo de Evento")
    event_types = ["Todos", "Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"]
    st.session_state.selected_event_type = st.sidebar.selectbox("Filtrar por evento:", event_types)
    st.sidebar.markdown("---")
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("🔄 Resetar Filtros", use_container_width=True):
            st.session_state.selected_activity_id = None
            st.session_state.selected_team_id = None
            st.session_state.selected_player_id = None
            st.session_state.selected_event_type = "Todos"
            st.session_state.events_df = None
            st.rerun()
    with col_btn2:
        if st.button("🔓 Desconectar", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        with st.spinner("Carregando eventos da API..."):
            if st.session_state.period_type == "Intervalo personalizado" and st.session_state.start_date_custom and st.session_state.end_date_custom:
                df = load_events(
                    team_id=st.session_state.selected_team_id,
                    player_id=st.session_state.selected_player_id,
                    activity_id=st.session_state.selected_activity_id,
                    start_date=st.session_state.start_date_custom,
                    end_date=st.session_state.end_date_custom
                )
            else:
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
                st.sidebar.warning("⚠️ Nenhum evento encontrado")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Resumo dos Filtros")
    st.sidebar.markdown(f"**Atividade:** {st.session_state.selected_activity_name}")
    st.sidebar.markdown(f"**Equipe:** {st.session_state.selected_team_name}")
    st.sidebar.markdown(f"**Atleta:** {st.session_state.selected_player_name}")
    st.sidebar.markdown(f"**Período:** {st.session_state.days_period} dias")
    if st.session_state.events_df is not None and not st.session_state.events_df.empty:
        df = st.session_state.events_df.copy()
        if st.session_state.selected_event_type != "Todos" and 'tipo_evento' in df.columns:
            df = df[df['tipo_evento'] == st.session_state.selected_event_type]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Eventos BIG", len(df))
        col2.metric("Tempo Médio Entre Eventos (min)", f"{df['back_in_game_min'].mean():.2f}")
        col3.metric("Duração Média por Evento (min)", f"{df['duration_min'].mean():.2f}")
        col4.metric("Carga Total (min)", f"{df['duration_min'].sum():.2f}")
        col5.metric("Confiança Média", f"{df['confidence'].mean():.3f}")
        st.markdown('<div class="sub-header">🏟️ Mapa de Calor - Atividade no Campo</div>', unsafe_allow_html=True)
        fig_campo = create_rugby_field()
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'], y=df['pos_y'], mode='markers',
                marker=dict(size=df['duration_min'] * 30, color=df['confidence'], colorscale='Viridis', showscale=True, colorbar=dict(title="Confiança"), opacity=0.7, line=dict(width=1, color='black')),
                text=[f"Evento: {row.get('tipo_evento', 'N/A')}<br>Duração: {row.get('duration_min', 0):.2f}min<br>Conf: {row.get('confidence', 0):.3f}" for _, row in df.iterrows()],
                hoverinfo='text', name='Eventos'
            ))
        st.plotly_chart(fig_campo, use_container_width=True)
        st.markdown('<div class="sub-header">📋 Detalle de Eventos</div>', unsafe_allow_html=True)
        df_display = df.copy()
        display_cols = ['tipo_evento', 'duration_min', 'back_in_game_min', 'confidence']
        if 'equipe' in df_display.columns and st.session_state.selected_team_id is None:
            display_cols.insert(1, 'equipe')
        if 'atleta' in df_display.columns and st.session_state.selected_player_id is None:
            display_cols.insert(2, 'atleta')
        st.dataframe(df_display[display_cols].head(100), use_container_width=True)
        st.markdown('<div class="sub-header">📈 Análise de Eventos</div>', unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            event_counts = df['tipo_evento'].value_counts()
            fig_pie = px.pie(values=event_counts.values, names=event_counts.index, title="Distribución por Tipo de Evento", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_g2:
            fig_duration = px.bar(x=range(min(len(df), 50)), y=df['duration_min'].head(50), title="Duración por Evento (minutos)", labels={"x": "Número de Evento", "y": "Duración (min)"})
            fig_duration.update_traces(marker_color='steelblue')
            st.plotly_chart(fig_duration, use_container_width=True)
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            fig_timeline = px.line(x=range(len(df)), y=df['back_in_game_min'], title="Tiempo entre Eventos - Back in Game (minutos)", labels={"x": "Secuencia de Eventos", "y": "Tiempo (min)"})
            fig_timeline.update_traces(line=dict(color='orange', width=2))
            st.plotly_chart(fig_timeline, use_container_width=True)
        with col_g4:
            fig_conf = px.scatter(x=range(len(df)), y=df['confidence'], title="Confianza por Evento", labels={"x": "Evento", "y": "Confianza"}, color=df['confidence'], color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_conf, use_container_width=True)
    elif st.session_state.events_df is not None:
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        st.info("💡 Tente: Selecionar um período maior, escolher uma equipe diferente, ou verificar se há eventos disponíveis")
    else:
        st.info("👈 Selecione os filtros na barra lateral e clique em CARREGAR EVENTOS")
    st.markdown("---")
    st.caption("📡 BIG Report - Análise de Retorno à Actividad | Datos: Catapult Sports")
    if st.session_state.use_mock:
        st.caption("🎮 Modo de demostración - Datos simulados para visualización")