import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        st.session_state.api_url = None
    if 'api_headers' not in st.session_state:
        st.session_state.api_headers = None
    if 'api_base_path' not in st.session_state:
        st.session_state.api_base_path = None
    
    # Dados
    if 'activities_list' not in st.session_state:
        st.session_state.activities_list = []
    if 'teams_list' not in st.session_state:
        st.session_state.teams_list = []
    if 'players_list' not in st.session_state:
        st.session_state.players_list = []
    
    # Seleções
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
    
    # Eventos
    if 'events_data' not in st.session_state:
        st.session_state.events_data = None

# ==================== CONEXÃO RÁPIDA (APENAS URLs MAIS PROVÁVEIS) ====================

def quick_test_endpoint(url, headers, timeout=3):
    """Testa um endpoint rapidamente"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout, params={"limit": 1})
        return response.status_code == 200, url
    except:
        return False, url

def discover_endpoints_fast(token, base_url):
    """Descobre endpoints rapidamente - testa apenas as URLs mais prováveis"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Apenas os paths mais prováveis (reduzido de 25 para 4)
    most_likely_paths = [
        "/api/v1",
        "/v1",
        "/api",
        ""
    ]
    
    # Apenas os recursos essenciais
    essential_resources = ["activities", "teams", "players"]
    
    # URLs para testar (apenas a fornecida + variação regional)
    urls_to_test = []
    
    for path in most_likely_paths:
        for resource in essential_resources:
            if path:
                url = f"{base_url}{path}/{resource}"
            else:
                url = f"{base_url}/{resource}"
            urls_to_test.append((resource, url))
    
    # Testar também variação europeia se a URL for americana
    if "backend-us" in base_url:
        euro_url = base_url.replace("backend-us", "backend-eu")
        for path in most_likely_paths[:2]:  # Apenas os 2 primeiros paths
            for resource in essential_resources[:1]:  # Apenas activities
                if path:
                    url = f"{euro_url}{path}/{resource}"
                else:
                    url = f"{euro_url}/{resource}"
                urls_to_test.append((resource, url))
    
    st.info("🔍 Testando conexão (isso leva apenas alguns segundos)...")
    
    working_endpoints = {}
    tested = 0
    
    for resource, url in urls_to_test:
        tested += 1
        # Mostrar progresso simples
        if tested % 5 == 0:
            st.caption(f"Testando... {tested}/{len(urls_to_test)}")
        
        success, _ = quick_test_endpoint(url, headers, timeout=2)
        
        if success:
            if resource not in working_endpoints:
                working_endpoints[resource] = url
                # Se encontrou activities, já podemos extrair o base_path
                if resource == "activities":
                    # Extrair o caminho base
                    if "/activities" in url:
                        st.session_state.api_base_path = url.replace("/activities", "")
                    st.success(f"✅ Conectado! Endpoint: {url}")
                    # Podemos parar se já encontrou os 3 essenciais
                    if len(working_endpoints) >= 2:
                        break
    
    # Se não encontrou nada, tentar URL direta sem path
    if not working_endpoints:
        for resource in essential_resources:
            url = f"{base_url}/{resource}"
            success, _ = quick_test_endpoint(url, headers, timeout=2)
            if success:
                working_endpoints[resource] = url
                if resource == "activities":
                    st.session_state.api_base_path = base_url
                break
    
    return working_endpoints if working_endpoints else None

# ==================== FUNÇÕES DE CARREGAMENTO RÁPIDO ====================

def load_data_fast(resource_name, params=None):
    """Carrega dados rapidamente"""
    if not st.session_state.api_headers:
        return []
    
    # Construir URL
    if st.session_state.api_base_path:
        url = f"{st.session_state.api_base_path}/{resource_name}"
    else:
        # Tentar URL direta
        url = f"{st.session_state.api_url}/{resource_name}"
    
    try:
        response = requests.get(
            url,
            headers=st.session_state.api_headers,
            timeout=10,
            params=params or {"limit": 200}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ['data', 'items', 'results', resource_name]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data] if data else []
            else:
                return []
        else:
            return []
            
    except Exception as e:
        st.error(f"Erro: {str(e)[:100]}")
        return []

def load_activities():
    """Carrega atividades"""
    data = load_data_fast("activities")
    
    activities = []
    for item in data:
        act_id = item.get('id') or item.get('activity_id')
        act_name = item.get('name') or item.get('title')
        if act_id and act_name:
            activities.append({"id": act_id, "name": act_name})
    
    return activities

def load_teams(activity_id=None):
    """Carrega equipes"""
    params = {"limit": 200}
    if activity_id:
        params["activity_id"] = activity_id
    
    data = load_data_fast("teams", params)
    
    teams = []
    for item in data:
        team_id = item.get('id') or item.get('team_id')
        team_name = item.get('name') or item.get('team_name')
        if team_id and team_name:
            teams.append({"id": team_id, "name": team_name})
    
    return teams

def load_players(team_id=None, activity_id=None):
    """Carrega atletas"""
    params = {"limit": 500}
    if team_id:
        params["team_id"] = team_id
    if activity_id:
        params["activity_id"] = activity_id
    
    data = load_data_fast("players", params)
    
    players = []
    for item in data:
        player_id = item.get('id') or item.get('player_id')
        player_name = item.get('name') or item.get('full_name')
        if player_id and player_name:
            number = item.get('number') or item.get('jersey_number')
            if number:
                player_name = f"{player_name} (#{number})"
            players.append({"id": player_id, "name": player_name})
    
    return players

def load_events(team_id=None, player_id=None, activity_id=None, start_date=None, end_date=None):
    """Carrega eventos"""
    params = {"limit": 1000}
    
    if team_id:
        params["team_id"] = team_id
    if player_id:
        params["player_id"] = player_id
    if activity_id:
        params["activity_id"] = activity_id
    if start_date:
        params["start_date"] = start_date.isoformat() if isinstance(start_date, datetime) else str(start_date)
    if end_date:
        params["end_date"] = end_date.isoformat() if isinstance(end_date, datetime) else str(end_date)
    
    data = load_data_fast("events", params)
    
    if data:
        return pd.DataFrame(data)
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
    
    fig.update_layout(
        title="🏟️ Campo de Rugby - Dimensões Oficiais (100m x 70m)",
        xaxis=dict(title="Comprimento (metros)", range=[-5, field_length+5]),
        yaxis=dict(title="Largura (metros)", range=[-5, field_width+5]),
        plot_bgcolor="lightgreen",
        height=550,
        hovermode='closest'
    )
    
    return fig

# ==================== TELA DE LOGIN RÁPIDA ====================

def login_screen():
    """Tela de login rápida"""
    
    st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1>
            <h3 style="color: #2c5aa0;">Catapult OpenField Integration</h3>
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
                help="Token fornecido pela Catapult Sports",
                value=""
            )
            
            # Limpar token
            if api_token:
                api_token = api_token.strip().replace('\n', '').replace('\r', '')
            
            # Opção de região simplificada
            region = st.selectbox(
                "Região:",
                ["América do Norte", "Europa", "Ásia", "Personalizado"]
            )
            
            if region == "América do Norte":
                api_url = "https://backend-us.openfield.catapultsports.com"
            elif region == "Europa":
                api_url = "https://backend-eu.openfield.catapultsports.com"
            elif region == "Ásia":
                api_url = "https://backend-asia.openfield.catapultsports.com"
            else:
                api_url = st.text_input("URL:", value="https://backend-us.openfield.catapultsports.com")
            
            if st.button("✅ Conectar", type="primary", use_container_width=True):
                if api_token:
                    with st.spinner("Conectando... (leva apenas alguns segundos)"):
                        endpoints = discover_endpoints_fast(api_token, api_url)
                        
                        if endpoints:
                            st.session_state.api_token = api_token
                            st.session_state.api_url = api_url
                            st.session_state.api_headers = {
                                "Authorization": f"Bearer {api_token}",
                                "Content-Type": "application/json"
                            }
                            st.session_state.authenticated = True
                            
                            st.success("✅ Conectado!")
                            
                            # Carregar atividades automaticamente
                            with st.spinner("Carregando atividades..."):
                                activities = load_activities()
                                if activities:
                                    st.session_state.activities_list = activities
                                    st.success(f"✅ {len(activities)} atividades encontradas")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Nenhuma atividade encontrada")
                        else:
                            st.error("❌ Falha na conexão")
                            st.info("💡 Dica: Verifique se o token está correto e tente outra região")
                else:
                    st.warning("⚠️ Insira o token")

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.markdown("## 📂 Filtros")
    
    # Botão desconectar
    if st.sidebar.button("🚪 Desconectar", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # ========== ATIVIDADES ==========
    st.sidebar.markdown("### 1️⃣ Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        with st.spinner("Carregando..."):
            activities = load_activities()
            if activities:
                st.session_state.activities_list = activities
                st.sidebar.success(f"✅ {len(activities)} atividades")
            else:
                st.sidebar.error("❌ Nenhuma atividade")
    
    if st.session_state.activities_list:
        activity_options = {act['id']: act['name'] for act in st.session_state.activities_list}
        activity_options_with_all = {None: "📋 Todas"}
        activity_options_with_all.update(activity_options)
        
        selected_activity_id = st.sidebar.selectbox(
            "Atividade:",
            options=list(activity_options_with_all.keys()),
            format_func=lambda x: activity_options_with_all[x]
        )
        
        st.session_state.selected_activity_id = selected_activity_id
        st.session_state.selected_activity_name = activity_options_with_all[selected_activity_id]
    else:
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades'")
    
    st.sidebar.markdown("---")
    
    # ========== EQUIPES ==========
    st.sidebar.markdown("### 2️⃣ Equipes")
    
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            with st.spinner("Carregando..."):
                teams = load_teams(st.session_state.selected_activity_id)
                if teams:
                    st.session_state.teams_list = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes")
                else:
                    st.sidebar.error("❌ Nenhuma equipe")
        
        if st.session_state.teams_list:
            team_options = {team['id']: team['name'] for team in st.session_state.teams_list}
            team_options_with_all = {None: "🏆 Todas"}
            team_options_with_all.update(team_options)
            
            selected_team_id = st.sidebar.selectbox(
                "Equipe:",
                options=list(team_options_with_all.keys()),
                format_func=lambda x: team_options_with_all[x]
            )
            
            st.session_state.selected_team_id = selected_team_id
            st.session_state.selected_team_name = team_options_with_all[selected_team_id]
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Equipes'")
    else:
        st.sidebar.warning("⚠️ Carregue atividades primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== ATLETAS ==========
    st.sidebar.markdown("### 3️⃣ Atletas")
    
    if st.session_state.teams_list:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            with st.spinner("Carregando..."):
                players = load_players(
                    st.session_state.selected_team_id,
                    st.session_state.selected_activity_id
                )
                if players:
                    st.session_state.players_list = players
                    st.sidebar.success(f"✅ {len(players)} atletas")
                else:
                    st.sidebar.error("❌ Nenhum atleta")
        
        if st.session_state.players_list:
            player_options = {player['id']: player['name'] for player in st.session_state.players_list}
            player_options_with_all = {None: "👥 Todos"}
            player_options_with_all.update(player_options)
            
            selected_player_id = st.sidebar.selectbox(
                "Atleta:",
                options=list(player_options_with_all.keys()),
                format_func=lambda x: player_options_with_all[x]
            )
            
            st.session_state.selected_player_id = selected_player_id
            st.session_state.selected_player_name = player_options_with_all[selected_player_id]
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Atletas'")
    else:
        st.sidebar.warning("⚠️ Carregue equipes primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== PERÍODO ==========
    st.sidebar.markdown("### 4️⃣ Período")
    
    days = st.sidebar.slider("Dias:", 1, 180, 30)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    st.sidebar.caption(f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    st.sidebar.markdown("---")
    
    # ========== EVENTOS ==========
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        if st.session_state.players_list:
            with st.spinner("Carregando eventos..."):
                df_events = load_events(
                    team_id=st.session_state.selected_team_id,
                    player_id=st.session_state.selected_player_id,
                    activity_id=st.session_state.selected_activity_id,
                    start_date=start_date,
                    end_date=end_date
                )
                st.session_state.events_data = df_events
                
                if not df_events.empty:
                    st.sidebar.success(f"✅ {len(df_events)} eventos")
                else:
                    st.sidebar.warning("⚠️ Nenhum evento")
        else:
            st.sidebar.error("❌ Carregue atletas primeiro")
    
    # ========== DASHBOARD ==========
    
    if st.session_state.events_data is not None and not st.session_state.events_data.empty:
        df = st.session_state.events_data
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Eventos", len(df))
        with col2:
            st.metric("Período (dias)", days)
        with col3:
            st.metric("Equipes", len(st.session_state.teams_list) if st.session_state.teams_list else 0)
        with col4:
            st.metric("Atletas", len(st.session_state.players_list) if st.session_state.players_list else 0)
        
        # Campo
        st.markdown('<div class="sub-header">🏟️ Atividade no Campo</div>', unsafe_allow_html=True)
        fig_campo = create_rugby_field()
        
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'],
                y=df['pos_y'],
                mode='markers',
                marker=dict(size=8, opacity=0.6),
                hoverinfo='text'
            ))
        
        st.plotly_chart(fig_campo, use_container_width=True)
        
        # Tabela
        st.markdown('<div class="sub-header">📋 Eventos</div>', unsafe_allow_html=True)
        st.dataframe(df.head(100), use_container_width=True)
        
    elif st.session_state.events_data is not None:
        st.warning("⚠️ Nenhum evento encontrado")
    else:
        st.info("👈 Selecione os filtros e clique em 'CARREGAR EVENTOS'")

# ==================== MAIN ====================

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()