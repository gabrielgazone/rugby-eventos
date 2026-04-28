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
    .debug-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.8rem;
        margin-top: 1rem;
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
    if 'working_endpoints' not in st.session_state:
        st.session_state.working_endpoints = {}
    if 'debug_logs' not in st.session_state:
        st.session_state.debug_logs = []
    
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

def add_debug_log(message, type="info"):
    """Adiciona log de debug"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.debug_logs.append(f"[{timestamp}] {type.upper()}: {message}")

# ==================== DESCOBERTA DE ENDPOINTS MELHORADA ====================

def test_url(url, headers, params=None):
    """Testa uma URL e retorna resultado"""
    try:
        add_debug_log(f"Testando: {url}")
        response = requests.get(url, headers=headers, timeout=10, params=params or {"limit": 1})
        add_debug_log(f"  Status: {response.status_code}")
        return response.status_code == 200, response.status_code
    except Exception as e:
        add_debug_log(f"  Erro: {str(e)[:100]}")
        return False, None

def discover_endpoints(token, base_url):
    """Descobre automaticamente os endpoints corretos da API"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Lista MUITO MAIS ABRANGENTE de possíveis caminhos
    possible_paths = [
        "",  # root
        "/api",
        "/api/v1",
        "/v1",
        "/v2",
        "/v3",
        "/rest",
        "/api/rest",
        "/openfield",
        "/openfield/api",
        "/openfield/api/v1",
        "/openfield/v1",
        "/services",
        "/data",
        "/api/data",
        "/apis",
        "/apis/v1",
        "/api/v2",
        "/public",
        "/api/public",
        "/api/v1/public",
        "/graphql",
        "/api/graphql"
    ]
    
    # URLs base alternativas para testar
    alternative_base_urls = [
        base_url,
        base_url.replace("backend-us", "backend-eu"),
        base_url.replace("backend-us", "backend-asia"),
        base_url.replace("backend-us", "api"),
        "https://api.catapult.com",
        "https://api.openfield.catapultsports.com",
        "https://openfield.catapultsports.com/api",
        base_url.replace(".openfield.catapultsports.com", ".catapultsports.com")
    ]
    
    # Recursos comuns para testar
    resources = ["activities", "teams", "players", "events", "sessions", "users"]
    
    working_endpoints = {}
    
    st.info("🔍 Testando múltiplas configurações de API...")
    
    progress_bar = st.progress(0)
    total_tests = len(alternative_base_urls) * len(possible_paths) * len(resources)
    test_count = 0
    
    # Limpar logs anteriores
    st.session_state.debug_logs = []
    add_debug_log(f"Iniciando descoberta de endpoints")
    add_debug_log(f"Token: {token[:50]}... (truncado)")
    
    for base_url_test in alternative_base_urls:
        add_debug_log(f"\n📡 Testando URL base: {base_url_test}")
        
        for path in possible_paths:
            for resource in resources:
                test_count += 1
                progress_bar.progress(min(test_count / total_tests, 1.0))
                
                # Construir URL completa
                if path:
                    url = f"{base_url_test}{path}/{resource}"
                else:
                    url = f"{base_url_test}/{resource}"
                
                success, status = test_url(url, headers)
                
                if success:
                    add_debug_log(f"✅ ENDPOINT ENCONTRADO: {resource} -> {url}")
                    if resource not in working_endpoints:
                        working_endpoints[resource] = url
                        working_endpoints['base_url_working'] = base_url_test
                        working_endpoints['path_working'] = path
                    break  # Encontrou este recurso, próximo
                
            # Se já encontrou todos os recursos essenciais, para
            if len(working_endpoints) >= 3:
                break
        
        # Se já encontrou todos os recursos essenciais, para
        if len(working_endpoints) >= 3:
            break
    
    progress_bar.empty()
    
    # Verificar recursos essenciais
    essential_resources = ["activities", "teams", "players"]
    found_essential = [r for r in essential_resources if r in working_endpoints]
    
    add_debug_log(f"\n📊 Resumo: Encontrados {len(working_endpoints)} endpoints")
    add_debug_log(f"Essenciais encontrados: {found_essential}")
    
    if working_endpoints:
        return working_endpoints
    else:
        return None

# ==================== FUNÇÕES GENÉRICAS DE CARREGAMENTO ====================

def load_data(resource_name, params=None):
    """Carrega dados de um recurso da API usando endpoint descoberto"""
    if not st.session_state.api_headers:
        return []
    
    if resource_name not in st.session_state.working_endpoints:
        st.error(f"Endpoint para {resource_name} não encontrado")
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
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ['data', 'items', 'results', resource_name, 'response']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
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
                value=""  # Campo vazio
            )
            
            # Limpar token (remover espaços e quebras de linha extras)
            if api_token:
                api_token = api_token.strip().replace('\n', '').replace('\r', '')
            
            # Múltiplas opções de URL
            url_options = st.radio(
                "Região da API:",
                ["América do Norte (padrão)", "Europa", "Ásia", "Personalizado"],
                horizontal=True
            )
            
            if url_options == "América do Norte (padrão)":
                api_url = "https://backend-us.openfield.catapultsports.com"
            elif url_options == "Europa":
                api_url = "https://backend-eu.openfield.catapultsports.com"
            elif url_options == "Ásia":
                api_url = "https://backend-asia.openfield.catapultsports.com"
            else:
                api_url = st.text_input(
                    "URL Personalizada:",
                    value="https://backend-us.openfield.catapultsports.com",
                    help="Digite a URL completa da API"
                )
            
            st.markdown("---")
            
            show_debug = st.checkbox("🔧 Mostrar logs de debug", value=False)
            
            if st.button("✅ Conectar e Diagnosticar", type="primary", use_container_width=True):
                if api_token:
                    with st.spinner("Conectando e descobrindo endpoints..."):
                        endpoints = discover_endpoints(api_token, api_url)
                        
                        if endpoints:
                            st.session_state.api_token = api_token
                            st.session_state.api_url = endpoints.get('base_url_working', api_url)
                            st.session_state.api_headers = {
                                "Authorization": f"Bearer {api_token}",
                                "Content-Type": "application/json"
                            }
                            st.session_state.working_endpoints = endpoints
                            st.session_state.authenticated = True
                            
                            st.success("✅ Conexão estabelecida com sucesso!")
                            
                            # Mostrar endpoints encontrados
                            with st.expander("📡 Endpoints encontrados"):
                                for resource, url in endpoints.items():
                                    if resource not in ['base_url_working', 'path_working']:
                                        st.markdown(f"**{resource}:** `{url}`")
                            
                            # Tentar carregar atividades
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
                            
                            # Mostrar diagnóstico detalhado
                            with st.expander("🔍 Diagnóstico detalhado", expanded=True):
                                st.markdown("**Possíveis causas:**")
                                st.markdown("""
                                1. **Token inválido ou mal formatado** - Verifique se copiou o token completo
                                2. **Token expirado** - Gere um novo token no portal da Catapult
                                3. **Região incorreta** - Tente América do Norte, Europa ou Ásia
                                4. **Permissões insuficientes** - O token precisa de acesso aos endpoints
                                5. **URL base incorreta** - Verifique com o suporte da Catapult
                                """)
                                
                                st.markdown("**Soluções sugeridas:**")
                                st.markdown("""
                                - **Limpe o token** - Remova espaços extras ou quebras de linha
                                - **Teste outra região** - Tente Europa ou Ásia
                                - **Verifique o token** no site: https://jwt.io (não compartilhe o resultado!)
                                - **Contate o suporte** da Catapult para confirmar a URL correta
                                """)
                            
                            if show_debug and st.session_state.debug_logs:
                                st.markdown("### 📋 Logs de Debug")
                                st.text_area("Debug Logs:", value="\n".join(st.session_state.debug_logs), height=300, key="debug_logs_area")
                else:
                    st.warning("⚠️ Por favor, insira o token da API")
            
            # Informações adicionais
            with st.expander("ℹ️ Como obter o token?"):
                st.markdown("""
                **Para obter seu token da API Catapult:**
                
                1. Acesse o portal da Catapult Sports
                2. Navegue até **Configurações > API Keys**
                3. Clique em **"Create New API Key"**
                4. Selecione as permissões necessárias (pelo menos leitura)
                5. Copie o token gerado
                
                **Importante:** O token deve começar com `eyJ` e ter 3 partes separadas por pontos.
                """)

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.markdown("## 📂 Filtros em Cascata")
    
    if st.session_state.working_endpoints:
        st.sidebar.success("✅ API Conectada")
        
        # Mostrar URL ativa
        if 'base_url_working' in st.session_state.working_endpoints:
            st.sidebar.caption(f"🌐 {st.session_state.working_endpoints['base_url_working']}")
    else:
        st.sidebar.error("❌ API não conectada")
    
    st.sidebar.markdown("---")
    
    # Botão para desconectar
    if st.sidebar.button("🚪 Desconectar", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # ========== ATIVIDADES ==========
    st.sidebar.markdown("### 1️⃣ Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        with st.spinner("Carregando atividades..."):
            activities = load_activities()
            if activities:
                st.session_state.activities_list = activities
                st.sidebar.success(f"✅ {len(activities)} atividades")
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
    else:
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades'")
    
    st.sidebar.markdown("---")
    
    # ========== EQUIPES ==========
    st.sidebar.markdown("### 2️⃣ Equipes")
    
    if st.session_state.activities_list:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            with st.spinner("Carregando equipes..."):
                teams = load_teams(st.session_state.selected_activity_id)
                if teams:
                    st.session_state.teams_list = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes")
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
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Equipes'")
    else:
        st.sidebar.warning("⚠️ Carregue as atividades primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== ATLETAS ==========
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
                    st.sidebar.success(f"✅ {len(players)} atletas")
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
        else:
            st.sidebar.warning("⚠️ Clique em 'Carregar Atletas'")
    else:
        st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== PERÍODO ==========
    st.sidebar.markdown("### 4️⃣ Período")
    
    days = st.sidebar.slider("Últimos dias:", 1, 180, 30)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    st.sidebar.info(f"📅 {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    st.sidebar.markdown("---")
    
    # ========== EVENTOS ==========
    st.sidebar.markdown("### 5️⃣ Eventos")
    
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
                    st.sidebar.warning("⚠️ Nenhum evento encontrado")
        else:
            st.sidebar.error("❌ Carregue os atletas primeiro")
    
    # ========== DASHBOARD ==========
    
    if st.session_state.events_data is not None and not st.session_state.events_data.empty:
        df = st.session_state.events_data
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Eventos", len(df))
        with col2:
            st.metric("Período (dias)", days)
        with col3:
            st.metric("Equipes", len(st.session_state.teams_list) if st.session_state.teams_list else 0)
        with col4:
            st.metric("Atletas", len(st.session_state.players_list) if st.session_state.players_list else 0)
        with col5:
            st.metric("Atividades", len(st.session_state.activities_list) if st.session_state.activities_list else 0)
        
        # Campo
        st.markdown('<div class="sub-header">🏟️ Atividade no Campo</div>', unsafe_allow_html=True)
        fig_campo = create_rugby_field()
        
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'],
                y=df['pos_y'],
                mode='markers',
                marker=dict(size=10, opacity=0.6),
                text=df.get('tipo_evento', ['Evento'] * len(df)),
                hoverinfo='text'
            ))
        
        st.plotly_chart(fig_campo, use_container_width=True)
        
        # Tabela
        st.markdown('<div class="sub-header">📋 Eventos</div>', unsafe_allow_html=True)
        st.dataframe(df.head(100), use_container_width=True)
        
    elif st.session_state.events_data is not None:
        st.warning("⚠️ Nenhum evento encontrado. Tente ajustar os filtros.")
    else:
        st.info("👈 Selecione os filtros na sidebar e clique em 'CARREGAR EVENTOS'")

# ==================== MAIN ====================

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()