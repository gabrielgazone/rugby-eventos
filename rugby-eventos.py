import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import re

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
    .endpoint-found {
        background-color: #d1ecf1;
        padding: 0.5rem;
        border-radius: 5px;
        font-family: monospace;
        margin: 0.2rem 0;
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
    if 'api_base_url' not in st.session_state:
        st.session_state.api_base_url = "https://backend-us.openfield.catapultsports.com"
    if 'api_headers' not in st.session_state:
        st.session_state.api_headers = None
    if 'working_endpoints' not in st.session_state:
        st.session_state.working_endpoints = {}
    
    # Dados com nomes e IDs
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
    
    # Dados de eventos
    if 'events_data' not in st.session_state:
        st.session_state.events_data = None
    
    # Estados de carregamento
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    if 'discovery_done' not in st.session_state:
        st.session_state.discovery_done = False

# ==================== DESCOBERTA DE ENDPOINTS ====================

def discover_endpoints(token, base_url):
    """Descobre automaticamente os endpoints corretos da API"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Lista de possíveis caminhos de API
    possible_paths = [
        "",  # root
        "/api",
        "/api/v1",
        "/v1",
        "/v2",
        "/rest",
        "/api/rest",
        "/openfield",
        "/openfield/api",
        "/openfield/api/v1",
        "/services",
        "/data",
        "/api/data"
    ]
    
    # Recursos comuns para testar
    resources = ["activities", "teams", "players", "sessions", "metrics", "events"]
    
    working_endpoints = {}
    
    st.info("🔍 Descobrindo endpoints da API... Isso pode levar alguns segundos.")
    
    progress_bar = st.progress(0)
    total_tests = len(possible_paths) * len(resources)
    test_count = 0
    
    for i, path in enumerate(possible_paths):
        for resource in resources:
            test_count += 1
            progress_bar.progress(test_count / total_tests)
            
            # Construir URL completa
            if path:
                url = f"{base_url}{path}/{resource}"
            else:
                url = f"{base_url}/{resource}"
            
            try:
                response = requests.get(url, headers=headers, timeout=5, params={"limit": 1})
                
                if response.status_code == 200:
                    # Endpoint funcionando!
                    if resource not in working_endpoints:
                        working_endpoints[resource] = url
                        st.success(f"✅ Encontrado: {resource} -> {url}")
                    break  # Encontrou este recurso, não precisa testar mais paths
                    
            except:
                continue
    
    progress_bar.empty()
    
    # Verificar se encontrou pelo menos um endpoint
    if working_endpoints:
        return working_endpoints
    else:
        return None

# ==================== FUNÇÕES GENÉRICAS DE CARREGAMENTO ====================

def load_data(resource_name, params=None):
    """Carrega dados de um recurso da API usando endpoint descoberto"""
    if not st.session_state.api_headers:
        return []
    
    # Verificar se temos um endpoint para este recurso
    if resource_name not in st.session_state.working_endpoints:
        st.error(f"Endpoint para {resource_name} não encontrado. Execute o diagnóstico primeiro.")
        return []
    
    endpoint_url = st.session_state.working_endpoints[resource_name]
    
    try:
        response = requests.get(
            endpoint_url,
            headers=st.session_state.api_headers,
            timeout=15,
            params=params or {"limit": 200}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse da resposta (diferentes formatos possíveis)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Tentar encontrar a lista em campos comuns
                for key in ['data', 'items', 'results', resource_name, 'response']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # Se não encontrou lista, retornar o dict como um item
                return [data]
            else:
                return []
        else:
            st.error(f"Erro {response.status_code} ao carregar {resource_name}")
            return []
            
    except Exception as e:
        st.error(f"Erro ao carregar {resource_name}: {str(e)}")
        return []

def load_activities():
    """Carrega atividades"""
    data = load_data("activities")
    
    activities = []
    for item in data:
        act_id = item.get('id') or item.get('activity_id') or item.get('uid')
        act_name = item.get('name') or item.get('title') or item.get('description')
        if act_id and act_name:
            activities.append({"id": act_id, "name": act_name})
    
    return activities

def load_teams(activity_id=None):
    """Carrega equipes"""
    params = {"limit": 200}
    if activity_id:
        params["activity_id"] = activity_id
    
    data = load_data("teams", params)
    
    teams = []
    for item in data:
        team_id = item.get('id') or item.get('team_id') or item.get('uid')
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
    
    data = load_data("players", params)
    
    players = []
    for item in data:
        player_id = item.get('id') or item.get('player_id') or item.get('uid')
        player_name = item.get('name') or item.get('full_name') or item.get('first_name')
        if player_id and player_name:
            # Adicionar número se disponível
            number = item.get('number') or item.get('jersey_number') or item.get('jersey')
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
    
    data = load_data("events", params)
    
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

# ==================== FUNÇÃO DO CAMPO DE RUGBY ====================

def create_rugby_field():
    """Cria um campo de rugby"""
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
    """Tela de login com diagnóstico automático"""
    
    st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1>
            <h3 style="color: #2c5aa0;">Catapult OpenField Integration</h3>
            <p style="margin-top: 20px;">Conecte-se à API para acessar dados reais</p>
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
                help="Token fornecido pela Catapult Sports",
                value=""  # Campo vazio - sem token padrão
            )
            
            api_url = st.text_input(
                "URL da API:",
                value="https://backend-us.openfield.catapultsports.com",
                help="URL base da API Catapult. O sistema descobrirá os endpoints automaticamente."
            )
            
            st.markdown("---")
            st.markdown("### 🔍 Diagnóstico Automático")
            st.info("O sistema vai descobrir automaticamente os endpoints corretos da API.")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Conectar e Diagnosticar", type="primary", use_container_width=True):
                    if api_token:
                        with st.spinner("Conectando e descobrindo endpoints..."):
                            # Testar conexão básica
                            headers = {
                                "Authorization": f"Bearer {api_token}",
                                "Content-Type": "application/json"
                            }
                            
                            # Descobrir endpoints
                            endpoints = discover_endpoints(api_token, api_url)
                            
                            if endpoints:
                                st.session_state.api_token = api_token
                                st.session_state.api_base_url = api_url
                                st.session_state.api_headers = headers
                                st.session_state.working_endpoints = endpoints
                                st.session_state.discovery_done = True
                                st.session_state.authenticated = True
                                
                                st.success("✅ Conexão estabelecida com sucesso!")
                                
                                # Mostrar endpoints encontrados
                                with st.expander("📡 Endpoints encontrados"):
                                    for resource, url in endpoints.items():
                                        if resource != 'base_path':
                                            st.markdown(f"**{resource}:** `{url}`")
                                
                                # Tentar carregar atividades automaticamente
                                with st.spinner("Carregando atividades iniciais..."):
                                    activities = load_activities()
                                    if activities:
                                        st.session_state.activities_list = activities
                                        st.success(f"✅ {len(activities)} atividades carregadas!")
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Nenhuma atividade encontrada. Verifique suas permissões.")
                            else:
                                st.error("❌ Não foi possível encontrar os endpoints da API.")
                                st.info("""
                                **Possíveis causas:**
                                1. URL base incorreta
                                2. Token inválido ou expirado
                                3. Token sem permissões necessárias
                                4. Problemas de rede
                                
                                **Tente:**
                                - Verificar o token
                                - Usar outra URL base (ex: https://api.catapult.com)
                                - Contatar o suporte da Catapult
                                """)
                    else:
                        st.warning("⚠️ Por favor, insira o token da API")
            
            with col_btn2:
                if st.button("ℹ️ Como obter o token?", use_container_width=True):
                    st.info("""
                    **Para obter seu token da API Catapult:**
                    
                    1. Acesse o portal da Catapult Sports
                    2. Navegue até Configurações > API Keys
                    3. Crie uma nova chave de API
                    4. Copie o token gerado
                    
                    ⚠️ **Importante:** Mantenha seu token em segurança. Não compartilhe publicamente.
                    """)

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.markdown("## 📂 Filtros em Cascata")
    
    # Mostrar status da API
    if st.session_state.working_endpoints:
        st.sidebar.success("✅ API Conectada")
        with st.sidebar.expander("📡 Status da conexão"):
            for resource in ['activities', 'teams', 'players', 'events']:
                if resource in st.session_state.working_endpoints:
                    st.sidebar.caption(f"✓ {resource}: OK")
    else:
        st.sidebar.error("❌ API não conectada")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 1: ATIVIDADES ==========
    st.sidebar.markdown("### 1️⃣ Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        with st.spinner("Carregando atividades..."):
            activities = load_activities()
            if activities:
                st.session_state.activities_list = activities
                st.sidebar.success(f"✅ {len(activities)} atividades carregadas")
                # Mostrar primeiras atividades como exemplo
                with st.sidebar.expander("📋 Ver atividades carregadas"):
                    for act in activities[:10]:
                        st.write(f"• {act['name']}")
                    if len(activities) > 10:
                        st.write(f"... e mais {len(activities)-10} atividades")
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
    
    # ========== NÍVEL 2: EQUIPES ==========
    st.sidebar.markdown("### 2️⃣ Equipes")
    
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            with st.spinner("Carregando equipes..."):
                teams = load_teams(st.session_state.selected_activity_id)
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
    
    # ========== NÍVEL 3: ATLETAS ==========
    st.sidebar.markdown("### 3️⃣ Atletas")
    
    if st.session_state.teams_list:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            with st.spinner("Carregando atletas..."):
                players = load_players(
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
            with st.spinner("Carregando eventos da API..."):
                df_events = load_events(
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
        else:
            st.sidebar.error("❌ Carregue os atletas primeiro!")
    
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
        for col in ['tipo_evento', 'atleta', 'equipe', 'duration_min', 'confidence']:
            if col in df.columns:
                display_cols.append(col)
        
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
        """)
    
    # Footer
    st.markdown("---")
    st.caption("🏉 BIG Report - Análise de Retorno à Atividade | Powered by Catapult Sports API")

# ==================== MAIN ====================

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()