import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

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
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin-bottom: 1rem;
    }
    .loading-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== INICIALIZAÇÃO ====================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'api_token' not in st.session_state:
        st.session_state.api_token = None
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "https://backend-us.openfield.catapultsports.com"
    if 'api_headers' not in st.session_state:
        st.session_state.api_headers = None
    
    # Dados com nomes e IDs
    if 'activities_list' not in st.session_state:
        st.session_state.activities_list = []  # Lista de dicts {id, name}
    if 'teams_list' not in st.session_state:
        st.session_state.teams_list = []      # Lista de dicts {id, name}
    if 'players_list' not in st.session_state:
        st.session_state.players_list = []    # Lista de dicts {id, name, number}
    
    # Seleções atuais (guardando IDs)
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
    
    # Dados de eventos
    if 'events_data' not in st.session_state:
        st.session_state.events_data = None
    
    # Estados de carregamento
    if 'loading_activities' not in st.session_state:
        st.session_state.loading_activities = False
    if 'loading_teams' not in st.session_state:
        st.session_state.loading_teams = False
    if 'loading_players' not in st.session_state:
        st.session_state.loading_players = False
    if 'loading_events' not in st.session_state:
        st.session_state.loading_events = False

# ==================== FUNÇÕES DA API ====================

def test_api_connection(token, base_url):
    """Testa a conexão com a API"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Testar com endpoint correto
        response = requests.get(
            f"{base_url}/api/v1/activities",
            headers=headers,
            timeout=10,
            params={"limit": 1}
        )
        
        if response.status_code == 200:
            return True, "Conexão realizada com sucesso!"
        elif response.status_code == 401:
            return False, "Token inválido ou expirado"
        elif response.status_code == 403:
            return False, "Token sem permissão"
        else:
            # Tentar sem o /api/v1
            response2 = requests.get(
                f"{base_url}/activities",
                headers=headers,
                timeout=10,
                params={"limit": 1}
            )
            if response2.status_code == 200:
                return True, "Conexão realizada (endpoint alternativo)"
            else:
                return False, f"Erro {response.status_code}: Não foi possível conectar"
            
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def load_activities_from_api():
    """Carrega atividades e retorna lista com {id, name}"""
    if not st.session_state.api_headers:
        return []
    
    try:
        # Tentar diferentes endpoints
        endpoints_to_try = [
            f"{st.session_state.api_url}/api/v1/activities",
            f"{st.session_state.api_url}/v1/activities",
            f"{st.session_state.api_url}/activities"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers=st.session_state.api_headers,
                    timeout=15,
                    params={"limit": 200}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extrair lista de atividades com nome e ID
                    activities = []
                    
                    if isinstance(data, list):
                        for item in data:
                            act_id = item.get('id') or item.get('activity_id')
                            act_name = item.get('name') or item.get('title') or item.get('description')
                            if act_id and act_name:
                                activities.append({"id": act_id, "name": act_name})
                    
                    elif isinstance(data, dict):
                        # Tentar encontrar a lista em campos comuns
                        for key in ['data', 'items', 'results', 'activities']:
                            if key in data and isinstance(data[key], list):
                                for item in data[key]:
                                    act_id = item.get('id') or item.get('activity_id')
                                    act_name = item.get('name') or item.get('title')
                                    if act_id and act_name:
                                        activities.append({"id": act_id, "name": act_name})
                                break
                    
                    if activities:
                        return activities
            except:
                continue
        
        return []
            
    except Exception as e:
        st.error(f"Erro ao carregar atividades: {str(e)}")
        return []

def load_teams_from_api(activity_id=None):
    """Carrega equipes e retorna lista com {id, name}"""
    if not st.session_state.api_headers:
        return []
    
    try:
        endpoints_to_try = [
            f"{st.session_state.api_url}/api/v1/teams",
            f"{st.session_state.api_url}/v1/teams",
            f"{st.session_state.api_url}/teams"
        ]
        
        params = {"limit": 200}
        if activity_id:
            params["activity_id"] = activity_id
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers=st.session_state.api_headers,
                    timeout=15,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    teams = []
                    
                    if isinstance(data, list):
                        for item in data:
                            team_id = item.get('id') or item.get('team_id')
                            team_name = item.get('name') or item.get('team_name')
                            if team_id and team_name:
                                teams.append({"id": team_id, "name": team_name})
                    
                    elif isinstance(data, dict):
                        for key in ['data', 'items', 'results', 'teams']:
                            if key in data and isinstance(data[key], list):
                                for item in data[key]:
                                    team_id = item.get('id') or item.get('team_id')
                                    team_name = item.get('name') or item.get('team_name')
                                    if team_id and team_name:
                                        teams.append({"id": team_id, "name": team_name})
                                break
                    
                    if teams:
                        return teams
            except:
                continue
        
        return []
            
    except Exception as e:
        st.error(f"Erro ao carregar equipes: {str(e)}")
        return []

def load_players_from_api(team_id=None, activity_id=None):
    """Carrega atletas e retorna lista com {id, name, number}"""
    if not st.session_state.api_headers:
        return []
    
    try:
        endpoints_to_try = [
            f"{st.session_state.api_url}/api/v1/players",
            f"{st.session_state.api_url}/v1/players",
            f"{st.session_state.api_url}/players"
        ]
        
        params = {"limit": 500}
        if team_id:
            params["team_id"] = team_id
        if activity_id:
            params["activity_id"] = activity_id
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers=st.session_state.api_headers,
                    timeout=15,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    players = []
                    
                    if isinstance(data, list):
                        for item in data:
                            player_id = item.get('id') or item.get('player_id')
                            player_name = item.get('name') or item.get('full_name') or item.get('first_name')
                            if player_id and player_name:
                                # Adicionar número se disponível
                                number = item.get('number') or item.get('jersey_number')
                                if number:
                                    player_name = f"{player_name} (#{number})"
                                players.append({"id": player_id, "name": player_name})
                    
                    elif isinstance(data, dict):
                        for key in ['data', 'items', 'results', 'players']:
                            if key in data and isinstance(data[key], list):
                                for item in data[key]:
                                    player_id = item.get('id') or item.get('player_id')
                                    player_name = item.get('name') or item.get('full_name')
                                    if player_id and player_name:
                                        number = item.get('number') or item.get('jersey_number')
                                        if number:
                                            player_name = f"{player_name} (#{number})"
                                        players.append({"id": player_id, "name": player_name})
                                break
                    
                    if players:
                        return players
            except:
                continue
        
        return []
            
    except Exception as e:
        st.error(f"Erro ao carregar atletas: {str(e)}")
        return []

def load_events_from_api(team_id=None, player_id=None, activity_id=None, start_date=None, end_date=None):
    """Carrega eventos da API com todos os filtros"""
    if not st.session_state.api_headers:
        return pd.DataFrame()
    
    try:
        endpoints_to_try = [
            f"{st.session_state.api_url}/api/v1/events",
            f"{st.session_state.api_url}/v1/events",
            f"{st.session_state.api_url}/events"
        ]
        
        params = {"limit": 1000}
        
        if team_id:
            params["team_id"] = team_id
        if player_id:
            params["player_id"] = player_id
        if activity_id:
            params["activity_id"] = activity_id
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers=st.session_state.api_headers,
                    timeout=20,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    events = []
                    
                    if isinstance(data, list):
                        events = data
                    elif isinstance(data, dict):
                        for key in ['data', 'items', 'results', 'events']:
                            if key in data and isinstance(data[key], list):
                                events = data[key]
                                break
                    
                    if events:
                        df = pd.DataFrame(events)
                        
                        # Mapear campos para nomes amigáveis
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
                            'player_name': 'atleta',
                            'team_name': 'equipe',
                            'activity_name': 'atividade'
                        }
                        
                        for old, new in column_mapping.items():
                            if old in df.columns and new not in df.columns:
                                df[new] = df[old]
                        
                        # Adicionar nomes amigáveis se disponíveis
                        if 'atleta' not in df.columns and player_id:
                            # Buscar nome do atleta selecionado
                            for player in st.session_state.players_list:
                                if player['id'] == player_id:
                                    df['atleta'] = player['name']
                                    break
                        
                        if 'equipe' not in df.columns and team_id:
                            for team in st.session_state.teams_list:
                                if team['id'] == team_id:
                                    df['equipe'] = team['name']
                                    break
                        
                        if 'atividade' not in df.columns and activity_id:
                            for activity in st.session_state.activities_list:
                                if activity['id'] == activity_id:
                                    df['atividade'] = activity['name']
                                    break
                        
                        return df
            except:
                continue
        
        return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar eventos: {str(e)}")
        return pd.DataFrame()

# ==================== FUNÇÃO DO CAMPO DE RUGBY ====================

def create_rugby_field():
    """Cria um campo de rugby"""
    field_length = 100
    field_width = 70
    
    fig = go.Figure()
    
    fig.add_shape(type="rect",
                  x0=0, x1=field_length,
                  y0=0, y1=field_width,
                  fillcolor="lightgreen",
                  line=dict(color="black", width=2),
                  layer="below")
    
    fig.add_shape(type="line",
                  x0=field_length/2, x1=field_length/2,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=3))
    
    fig.add_shape(type="line",
                  x0=22, x1=22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    fig.add_shape(type="line",
                  x0=field_length-22, x1=field_length-22,
                  y0=0, y1=field_width,
                  line=dict(color="red", width=2, dash="dash"))
    
    fig.add_shape(type="line",
                  x0=10, x1=10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    fig.add_shape(type="line",
                  x0=field_length-10, x1=field_length-10,
                  y0=0, y1=field_width,
                  line=dict(color="white", width=1, dash="dot"))
    
    fig.update_layout(
        title="🏟️ Campo de Rugby - Dimensões Oficiais (100m x 70m)",
        xaxis=dict(title="Comprimento (metros)", range=[-5, field_length+5], showgrid=True),
        yaxis=dict(title="Largura (metros)", range=[-5, field_width+5], showgrid=True),
        plot_bgcolor="lightgreen",
        height=550,
        hovermode='closest'
    )
    
    return fig

# ==================== TELA DE LOGIN ====================

def login_screen():
    """Tela de login"""
    
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1>
            <h3 style="color: #2c5aa0;">Catapult OpenField Integration</h3>
            <p style="margin-top: 20px;">Conecte-se à API para acessar dados reais de atletas e atividades</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔑 Autenticação")
            
            api_token = st.text_area(
                "Token JWT:",
                height=100,
                placeholder="Cole seu token JWT aqui...",
                help="Token fornecido pela Catapult Sports"
            )
            
            api_url = st.text_input(
                "URL da API:",
                value="https://backend-us.openfield.catapultsports.com",
                help="URL base da API Catapult"
            )
            
            st.markdown("---")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Conectar à API", type="primary", use_container_width=True):
                    if api_token:
                        with st.spinner("Conectando à API Catapult..."):
                            success, message = test_api_connection(api_token, api_url)
                            
                            if success:
                                st.session_state.api_token = api_token
                                st.session_state.api_url = api_url
                                st.session_state.api_headers = {
                                    "Authorization": f"Bearer {api_token}",
                                    "Content-Type": "application/json"
                                }
                                st.session_state.authenticated = True
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.warning("Por favor, insira o token da API")
            
            with col_btn2:
                if st.button("ℹ️ Informações", use_container_width=True):
                    st.info("""
                    **Como obter o token:**
                    1. Acesse o portal da Catapult
                    2. Vá em Configurações > API
                    3. Crie ou copie um token JWT
                    
                    **URL padrão:** 
                    https://backend-us.openfield.catapultsports.com
                    """)

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal com nomes amigáveis"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar com filtros em cascata
    st.sidebar.markdown("## 📂 Filtros de Dados")
    st.sidebar.info("📡 Dados reais da API Catapult")
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 1: ATIVIDADES ==========
    st.sidebar.markdown("### 1️⃣ Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        st.session_state.loading_activities = True
        with st.spinner("Carregando atividades da API..."):
            activities = load_activities_from_api()
            if activities:
                st.session_state.activities_list = activities
                st.sidebar.success(f"✅ {len(activities)} atividades carregadas")
                # Mostrar alguns nomes como exemplo
                with st.sidebar.expander("📋 Ver atividades carregadas"):
                    for act in activities[:10]:
                        st.write(f"• {act['name']}")
                    if len(activities) > 10:
                        st.write(f"... e mais {len(activities)-10} atividades")
            else:
                st.sidebar.error("❌ Nenhuma atividade encontrada")
        st.session_state.loading_activities = False
        st.rerun()
    
    if st.session_state.activities_list:
        # Criar opções com nomes amigáveis
        activity_options = {act['id']: act['name'] for act in st.session_state.activities_list}
        activity_options_with_all = {None: "📋 Todas as Atividades"}
        activity_options_with_all.update(activity_options)
        
        selected_activity_id = st.sidebar.selectbox(
            "Selecionar Atividade:",
            options=list(activity_options_with_all.keys()),
            format_func=lambda x: activity_options_with_all[x],
            key="activity_select"
        )
        
        st.session_state.selected_activity_id = selected_activity_id
        st.session_state.selected_activity_name = activity_options_with_all[selected_activity_id]
        
        st.sidebar.success(f"📋 {st.session_state.selected_activity_name}")
    else:
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades' primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 2: EQUIPES ==========
    st.sidebar.markdown("### 2️⃣ Equipes")
    
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            st.session_state.loading_teams = True
            with st.spinner("Carregando equipes da API..."):
                teams = load_teams_from_api(st.session_state.selected_activity_id)
                if teams:
                    st.session_state.teams_list = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes carregadas")
                    with st.sidebar.expander("🏆 Ver equipes carregadas"):
                        for team in teams[:10]:
                            st.write(f"• {team['name']}")
                        if len(teams) > 10:
                            st.write(f"... e mais {len(teams)-10} equipes")
                else:
                    st.sidebar.error("❌ Nenhuma equipe encontrada")
            st.session_state.loading_teams = False
            st.rerun()
        
        if st.session_state.teams_list:
            # Criar opções com nomes amigáveis
            team_options = {team['id']: team['name'] for team in st.session_state.teams_list}
            team_options_with_all = {None: "🏆 Todas as Equipes"}
            team_options_with_all.update(team_options)
            
            selected_team_id = st.sidebar.selectbox(
                "Selecionar Equipe:",
                options=list(team_options_with_all.keys()),
                format_func=lambda x: team_options_with_all[x],
                key="team_select"
            )
            
            st.session_state.selected_team_id = selected_team_id
            st.session_state.selected_team_name = team_options_with_all[selected_team_id]
            
            st.sidebar.success(f"🏆 {st.session_state.selected_team_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Equipes'")
    else:
        st.sidebar.warning("⚠️ Carregue as atividades primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 3: ATLETAS ==========
    st.sidebar.markdown("### 3️⃣ Atletas")
    
    if st.session_state.teams_list:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            st.session_state.loading_players = True
            with st.spinner("Carregando atletas da API..."):
                players = load_players_from_api(
                    st.session_state.selected_team_id,
                    st.session_state.selected_activity_id
                )
                if players:
                    st.session_state.players_list = players
                    st.sidebar.success(f"✅ {len(players)} atletas carregados")
                    with st.sidebar.expander("👥 Ver atletas carregados"):
                        for player in players[:20]:
                            st.write(f"• {player['name']}")
                        if len(players) > 20:
                            st.write(f"... e mais {len(players)-20} atletas")
                else:
                    st.sidebar.error("❌ Nenhum atleta encontrado")
            st.session_state.loading_players = False
            st.rerun()
        
        if st.session_state.players_list:
            # Criar opções com nomes amigáveis
            player_options = {player['id']: player['name'] for player in st.session_state.players_list}
            player_options_with_all = {None: "👥 Todos os Atletas"}
            player_options_with_all.update(player_options)
            
            selected_player_id = st.sidebar.selectbox(
                "Selecionar Atleta:",
                options=list(player_options_with_all.keys()),
                format_func=lambda x: player_options_with_all[x],
                key="player_select"
            )
            
            st.session_state.selected_player_id = selected_player_id
            st.session_state.selected_player_name = player_options_with_all[selected_player_id]
            
            st.sidebar.success(f"👤 {st.session_state.selected_player_name}")
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Atletas'")
    else:
        st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 4: PERÍODO ==========
    st.sidebar.markdown("### 4️⃣ Período de Análise")
    
    period_type = st.sidebar.radio(
        "Tipo de período:",
        ["Últimos dias", "Intervalo personalizado"],
        horizontal=True
    )
    
    if period_type == "Últimos dias":
        days = st.sidebar.slider("Dias atrás:", 1, 180, 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        st.sidebar.info(f"📅 {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    else:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Data inicial:", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("Data final:", datetime.now())
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 5: EVENTOS ==========
    st.sidebar.markdown("### 5️⃣ Eventos")
    
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        if st.session_state.players_list:
            st.session_state.loading_events = True
            with st.spinner("Carregando eventos da API..."):
                df_events = load_events_from_api(
                    team_id=st.session_state.selected_team_id,
                    player_id=st.session_state.selected_player_id,
                    activity_id=st.session_state.selected_activity_id,
                    start_date=start_date,
                    end_date=end_date
                )
                st.session_state.events_data = df_events
                
                if not df_events.empty:
                    st.sidebar.success(f"✅ {len(df_events)} eventos carregados")
                else:
                    st.sidebar.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
            st.session_state.loading_events = False
            st.rerun()
        else:
            st.sidebar.error("❌ Carregue os atletas primeiro!")
    
    # Mostrar status de carregamento
    if st.session_state.loading_activities:
        st.sidebar.info("⏳ Carregando atividades...")
    if st.session_state.loading_teams:
        st.sidebar.info("⏳ Carregando equipes...")
    if st.session_state.loading_players:
        st.sidebar.info("⏳ Carregando atletas...")
    if st.session_state.loading_events:
        st.sidebar.info("⏳ Carregando eventos...")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Resumo dos Filtros")
    st.sidebar.write(f"**Atividade:** {st.session_state.selected_activity_name}")
    st.sidebar.write(f"**Equipe:** {st.session_state.selected_team_name}")
    st.sidebar.write(f"**Atleta:** {st.session_state.selected_player_name}")
    
    # ========== DASHBOARD PRINCIPAL ==========
    
    if st.session_state.events_data is not None and not st.session_state.events_data.empty:
        df = st.session_state.events_data
        
        # Métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Eventos", len(df))
        with col2:
            if 'duration_min' in df.columns:
                st.metric("Duração Média (min)", f"{df['duration_min'].mean():.2f}")
            else:
                st.metric("Duração Média (min)", "N/A")
        with col3:
            if 'back_in_game_min' in df.columns:
                st.metric("Intervalo Médio (min)", f"{df['back_in_game_min'].mean():.2f}")
            else:
                st.metric("Intervalo Médio (min)", "N/A")
        with col4:
            if 'duration_min' in df.columns:
                st.metric("Carga Total (min)", f"{df['duration_min'].sum():.2f}")
            else:
                st.metric("Carga Total (min)", "N/A")
        with col5:
            if 'confidence' in df.columns:
                st.metric("Confiança Média", f"{df['confidence'].mean():.3f}")
            else:
                st.metric("Confiança Média", "N/A")
        
        # Campo de Rugby
        st.markdown('<div class="sub-header">🏟️ Mapa de Calor - Atividade no Campo</div>', unsafe_allow_html=True)
        
        fig_campo = create_rugby_field()
        
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            size_col = df['duration_min'] * 20 if 'duration_min' in df.columns else 8
            color_col = df['confidence'] if 'confidence' in df.columns else 0.5
            
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'],
                y=df['pos_y'],
                mode='markers',
                marker=dict(
                    size=size_col,
                    color=color_col,
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
        
        # Tabela de eventos
        st.markdown('<div class="sub-header">📋 Detalhe dos Eventos</div>', unsafe_allow_html=True)
        
        # Preparar colunas para exibição
        display_cols = []
        if 'tipo_evento' in df.columns:
            display_cols.append('tipo_evento')
        if 'atleta' in df.columns:
            display_cols.append('atleta')
        if 'equipe' in df.columns:
            display_cols.append('equipe')
        if 'duration_min' in df.columns:
            display_cols.append('duration_min')
        if 'confidence' in df.columns:
            display_cols.append('confidence')
        
        if display_cols:
            st.dataframe(
                df[display_cols].head(100),
                use_container_width=True,
                column_config={
                    "tipo_evento": "Tipo de Evento",
                    "atleta": "Atleta",
                    "equipe": "Equipe",
                    "duration_min": "Duração (min)",
                    "confidence": "Confiança"
                }
            )
        
        # Gráficos adicionais
        if 'tipo_evento' in df.columns:
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                event_counts = df['tipo_evento'].value_counts()
                fig_pie = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Distribuição por Tipo de Evento",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            if 'duration_min' in df.columns:
                with col_g2:
                    fig_bar = px.bar(
                        x=range(min(50, len(df))),
                        y=df['duration_min'].head(50),
                        title="Duração dos Eventos (minutos)",
                        labels={"x": "Evento", "y": "Duração (min)"}
                    )
                    fig_bar.update_traces(marker_color='steelblue')
                    st.plotly_chart(fig_bar, use_container_width=True)
        
    elif st.session_state.events_data is not None and st.session_state.events_data.empty:
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        st.info("💡 Tente:")
        st.markdown("""
        - Selecionar um período maior
        - Escolher uma equipe diferente
        - Carregar dados de outra atividade
        """)
    else:
        st.info("👈 **Como usar:**")
        st.markdown("""
        1. **Carregue as Atividades** - Clique no botão na sidebar
        2. **Carregue as Equipes** - Baseado na atividade selecionada
        3. **Carregue os Atletas** - Baseado na equipe selecionada
        4. **Defina o Período** - Escolha os dias da análise
        5. **Carregue os Eventos** - Clique no botão principal
        
        ✅ Todos os dados são carregados em **cascata** da API real da Catapult!
        📋 Você verá **nomes reais** de atividades, equipes e atletas, não códigos ou IDs!
        """)
    
    # Footer
    st.markdown("---")
    st.caption("🏉 BIG Report - Análise de Retorno à Atividade | Powered by Catapult Sports API")
    if st.session_state.events_data is not None and not st.session_state.events_data.empty:
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