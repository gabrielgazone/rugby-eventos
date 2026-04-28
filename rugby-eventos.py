import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import numpy as np
import sys

st.set_page_config(page_title="BIG Report - Rugby Analytics", page_icon="🏉", layout="wide")

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
            {"id": 1, "name": "Treino Tática - Quarta"},
            {"id": 2, "name": "Jogo Treino - Sábado"},
            {"id": 3, "name": "Recuperação Física - Segunda"},
            {"id": 4, "name": "Análise de Vídeo - Sexta"},
            {"id": 5, "name": "Treino Força - Terça"}
        ]
    result = []
    for item in data:
        item_id = item.get('id')
        if not item_id:
            item_id = item.get('activity_id')
        item_name = item.get('name')
        if not item_name:
            item_name = item.get('title')
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
            {"id": 1, "name": "Estudiantes de La Plata"},
            {"id": 2, "name": "CUBA"},
            {"id": 3, "name": "CULP"},
            {"id": 4, "name": "Selección Argentina"},
            {"id": 5, "name": "Los Pumas 7's"}
        ]
    result = []
    for item in data:
        team_id = item.get('id')
        if not team_id:
            team_id = item.get('team_id')
        team_name = item.get('name')
        if not team_name:
            team_name = item.get('team_name')
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
            1: ["Agustin Dublo - #010", "Ignacio Diaz - #005", "Ignacio Fadul - #012", "Juan Martin Godoy - #009"],
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
        player_id = item.get('id')
        if not player_id:
            player_id = item.get('player_id')
        player_name = item.get('name')
        if not player_name:
            player_name = item.get('full_name')
        if player_id and player_name:
            number = item.get('number')
            if not number:
                number = item.get('jersey_number')
            if number:
                player_name = player_name + " - #" + str(number)
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
    data_inicio = datetime.now() - timedelta(days=np.random.randint(1, days))
    start_times = []
    current_time = data_inicio
    for i in range(n_events):
        start_times.append(current_time.timestamp())
        current_time = current_time + timedelta(seconds=np.random.randint(30, 300))
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
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, x1=100, y0=0, y1=70, fillcolor="lightgreen", line=dict(color="black", width=2), layer="below")
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=70, line=dict(color="white", width=3))
    fig.add_shape(type="line", x0=22, x1=22, y0=0, y1=70, line=dict(color="red", width=2, dash="dash"))
    fig.add_shape(type="line", x0=78, x1=78, y0=0, y1=70, line=dict(color="red", width=2, dash="dash"))
    fig.add_shape(type="line", x0=10, x1=10, y0=0, y1=70, line=dict(color="white", width=1, dash="dot"))
    fig.add_shape(type="line", x0=90, x1=90, y0=0, y1=70, line=dict(color="white", width=1, dash="dot"))
    fig.update_layout(
        title="Campo de Rugby (100m x 70m)",
        xaxis=dict(title="Comprimento (m)", range=[-5, 105]),
        yaxis=dict(title="Largura (m)", range=[-5, 75]),
        plot_bgcolor="lightgreen",
        height=550
    )
    return fig

# LOGIN
if st.session_state.step == 'login':
    st.title("BIG Report - Catapult Sports")
    
    with st.form(key="login_form"):
        token_input = st.text_input("Token JWT", type="password")
        submit_button = st.form_submit_button(label="Conectar")
        
        if submit_button:
            if token_input:
                decoded = decode_jwt(token_input)
                if decoded:
                    api_url = decoded.get('iss', 'https://backend-us.openfield.catapultsports.com')
                    st.success("Token valido")
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
                    st.error("Token invalido")
            else:
                st.warning("Digite o token")

# DASHBOARD
elif st.session_state.step == 'dashboard':
    st.markdown('<div class="main-header">BIG Report - Analisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    
    if st.session_state.use_mock:
        st.warning("Modo de demonstracao ativado - Dados simulados")
    
    st.sidebar.header("Filtros")
    
    if st.sidebar.button("Atualizar Atividades"):
        with st.spinner("Carregando..."):
            st.session_state.activities_list = load_activities()
            st.sidebar.success(str(len(st.session_state.activities_list)) + " atividades")
    
    if st.session_state.activities_list:
        opts = {"None": "Todas"}
        for a in st.session_state.activities_list:
            opts[str(a['id'])] = a['name']
        sel = st.sidebar.selectbox("Atividade", list(opts.keys()), format_func=lambda x: opts[x])
        if sel != "None":
            st.session_state.selected_activity_id = int(sel)
            st.session_state.selected_activity_name = opts[sel]
        else:
            st.session_state.selected_activity_id = None
            st.session_state.selected_activity_name = "Todas"
    
    if st.sidebar.button("Atualizar Equipes"):
        with st.spinner("Carregando..."):
            st.session_state.teams_list = load_teams(st.session_state.selected_activity_id)
            st.sidebar.success(str(len(st.session_state.teams_list)) + " equipes")
    
    if st.session_state.teams_list:
        opts = {"None": "Todas"}
        for t in st.session_state.teams_list:
            opts[str(t['id'])] = t['name']
        sel = st.sidebar.selectbox("Equipe", list(opts.keys()), format_func=lambda x: opts[x])
        if sel != "None":
            st.session_state.selected_team_id = int(sel)
            st.session_state.selected_team_name = opts[sel]
        else:
            st.session_state.selected_team_id = None
            st.session_state.selected_team_name = "Todas"
    
    if st.sidebar.button("Atualizar Atletas"):
        with st.spinner("Carregando..."):
            st.session_state.players_list = load_players(st.session_state.selected_team_id, st.session_state.selected_activity_id)
            st.sidebar.success(str(len(st.session_state.players_list)) + " atletas")
    
    if st.session_state.players_list:
        opts = {"None": "Todos"}
        for p in st.session_state.players_list:
            opts[str(p['id'])] = p['name']
        sel = st.sidebar.selectbox("Atleta", list(opts.keys()), format_func=lambda x: opts[x])
        if sel != "None":
            st.session_state.selected_player_id = int(sel)
            st.session_state.selected_player_name = opts[sel]
        else:
            st.session_state.selected_player_id = None
            st.session_state.selected_player_name = "Todos"
    
    days = st.sidebar.slider("Ultimos dias", 1, 180, 30)
    st.session_state.days_period = days
    
    event_types = ["Todos", "Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"]
    selected_event_type = st.sidebar.selectbox("Tipo de Evento", event_types)
    
    if st.sidebar.button("CARREGAR EVENTOS", type="primary"):
        with st.spinner("Carregando eventos..."):
            df = load_events(
                team_id=st.session_state.selected_team_id,
                player_id=st.session_state.selected_player_id,
                activity_id=st.session_state.selected_activity_id,
                days=days
            )
            st.session_state.events_df = df
            st.sidebar.success(str(len(df)) + " eventos")
    
    if st.sidebar.button("Resetar Filtros"):
        st.session_state.selected_activity_id = None
        st.session_state.selected_team_id = None
        st.session_state.selected_player_id = None
        st.session_state.events_df = None
        st.rerun()
    
    if st.sidebar.button("Desconectar"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.write("**Atividade:** " + st.session_state.selected_activity_name)
    st.sidebar.write("**Equipe:** " + st.session_state.selected_team_name)
    st.sidebar.write("**Atleta:** " + st.session_state.selected_player_name)
    
    if st.session_state.events_df is not None and not st.session_state.events_df.empty:
        df = st.session_state.events_df.copy()
        
        if selected_event_type != "Todos" and 'tipo_evento' in df.columns:
            df = df[df['tipo_evento'] == selected_event_type]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Eventos", len(df))
        col2.metric("Duracao Media", f"{df['duration_min'].mean():.2f} min")
        col3.metric("Carga Total", f"{df['duration_min'].sum():.2f} min")
        col4.metric("Confianca Media", f"{df['confidence'].mean():.3f}")
        col5.metric("Intervalo Medio", f"{df['back_in_game_min'].mean():.2f} min")
        
        st.subheader("Mapa de Atividade no Campo")
        fig = create_rugby_field()
        fig.add_trace(go.Scatter(
            x=df['pos_x'], y=df['pos_y'], mode='markers',
            marker=dict(size=df['duration_min']*30, color=df['confidence'], colorscale='Viridis', showscale=True, opacity=0.7),
            text=[f"Tipo: {row['tipo_evento']}<br>Duracao: {row['duration_min']:.2f}min" for _, row in df.iterrows()],
            hoverinfo='text'
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detalhe dos Eventos")
        cols = ['tipo_evento', 'duration_min', 'back_in_game_min', 'confidence']
        if 'equipe' in df.columns:
            cols.insert(1, 'equipe')
        if 'atleta' in df.columns:
            cols.insert(2, 'atleta')
        st.dataframe(df[cols].head(100), use_container_width=True)
        
        st.subheader("Analise de Eventos")
        col1, col2 = st.columns(2)
        with col1:
            counts = df['tipo_evento'].value_counts()
            fig_pie = px.pie(values=counts.values, names=counts.index, title="Distribuicao por Tipo")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(x=range(min(50, len(df))), y=df['duration_min'].head(50), title="Duracao dos Eventos")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        col3, col4 = st.columns(2)
        with col3:
            fig_line = px.line(x=range(len(df)), y=df['back_in_game_min'], title="Tempo entre Eventos")
            st.plotly_chart(fig_line, use_container_width=True)
        with col4:
            fig_scatter = px.scatter(x=range(len(df)), y=df['confidence'], title="Confianca por Evento", color=df['confidence'])
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    elif st.session_state.events_df is not None:
        st.warning("Nenhum evento encontrado para os filtros selecionados")
    else:
        st.info("Selecione os filtros na barra lateral e clique em CARREGAR EVENTOS")
    
    st.caption("BIG Report - Catapult Sports API")