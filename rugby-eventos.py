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

# ==================== FUNÇÕES DE AUTENTICAÇÃO ====================

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
    
    # Dados carregados em cascata
    if 'activities_data' not in st.session_state:
        st.session_state.activities_data = None
    if 'teams_data' not in st.session_state:
        st.session_state.teams_data = None
    if 'players_data' not in st.session_state:
        st.session_state.players_data = None
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

def test_api_connection(token, base_url):
    """Testa a conexão com a API da Catapult"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Testar com endpoint de atividades
        response = requests.get(
            f"{base_url}/activities",
            headers=headers,
            timeout=10,
            params={"limit": 1}
        )
        
        if response.status_code == 200:
            return True, "Conexão realizada com sucesso!"
        elif response.status_code == 401:
            return False, "Token inválido ou expirado"
        elif response.status_code == 403:
            return False, "Token sem permissão para acessar atividades"
        else:
            return False, f"Erro {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout - Servidor não respondeu"
    except requests.exceptions.ConnectionError:
        return False, "Erro de conexão - Verifique a URL"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

# ==================== FUNÇÕES DE CARREGAMENTO EM CASCATA ====================

def load_activities_from_api():
    """Carrega atividades disponíveis da API (NÍVEL 1)"""
    if not st.session_state.api_headers:
        return None
    
    try:
        response = requests.get(
            f"{st.session_state.api_url}/activities",
            headers=st.session_state.api_headers,
            timeout=15,
            params={"limit": 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse da resposta (ajustar conforme estrutura real)
            if isinstance(data, list):
                activities = data
            elif isinstance(data, dict) and 'activities' in data:
                activities = data['activities']
            elif isinstance(data, dict) and 'data' in data:
                activities = data['data']
            else:
                activities = []
            
            # Extrair nomes das atividades
            activity_names = []
            for act in activities:
                name = act.get('name') or act.get('title') or act.get('id')
                if name:
                    activity_names.append(name)
            
            return activity_names
        else:
            st.error(f"Erro ao carregar atividades: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Erro na requisição de atividades: {str(e)}")
        return None

def load_teams_from_api(activity_name=None):
    """Carrega equipes da API baseado na atividade selecionada (NÍVEL 2)"""
    if not st.session_state.api_headers:
        return None
    
    try:
        params = {}
        if activity_name and activity_name != "Todas Atividades":
            params["activity"] = activity_name
        
        response = requests.get(
            f"{st.session_state.api_url}/teams",
            headers=st.session_state.api_headers,
            timeout=15,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                teams = data
            elif isinstance(data, dict) and 'teams' in data:
                teams = data['teams']
            elif isinstance(data, dict) and 'data' in data:
                teams = data['data']
            else:
                teams = []
            
            # Extrair nomes das equipes
            team_names = []
            for team in teams:
                name = team.get('name') or team.get('team_name') or team.get('id')
                if name:
                    team_names.append(name)
            
            return team_names if team_names else ["Nenhuma equipe encontrada"]
        else:
            st.warning(f"Não foi possível carregar equipes: {response.status_code}")
            return None
            
    except Exception as e:
        st.warning(f"Erro ao carregar equipes: {str(e)}")
        return None

def load_players_from_api(team_name=None, activity_name=None):
    """Carrega atletas da API baseado na equipe selecionada (NÍVEL 3)"""
    if not st.session_state.api_headers:
        return None
    
    try:
        params = {"limit": 200}
        if team_name and team_name != "Todas Equipes":
            params["team"] = team_name
        if activity_name and activity_name != "Todas Atividades":
            params["activity"] = activity_name
        
        response = requests.get(
            f"{st.session_state.api_url}/players",
            headers=st.session_state.api_headers,
            timeout=15,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                players = data
            elif isinstance(data, dict) and 'players' in data:
                players = data['players']
            elif isinstance(data, dict) and 'data' in data:
                players = data['data']
            else:
                players = []
            
            # Extrair nomes dos atletas
            player_names = []
            for player in players:
                name = player.get('name') or player.get('full_name') or player.get('first_name')
                if name:
                    # Adicionar número se disponível
                    number = player.get('number') or player.get('jersey_number')
                    if number:
                        name = f"{name} - #{number}"
                    player_names.append(name)
            
            return player_names if player_names else ["Nenhum atleta encontrado"]
        else:
            st.warning(f"Não foi possível carregar atletas: {response.status_code}")
            return None
            
    except Exception as e:
        st.warning(f"Erro ao carregar atletas: {str(e)}")
        return None

def load_events_from_api(team_name=None, player_name=None, activity_name=None, start_date=None, end_date=None):
    """Carrega eventos da API com todos os filtros (NÍVEL 4)"""
    if not st.session_state.api_headers:
        return pd.DataFrame()
    
    try:
        params = {"limit": 1000}
        
        if team_name and team_name != "Todas Equipes":
            params["team"] = team_name
        if player_name and player_name != "Todos Atletas":
            params["player"] = player_name
        if activity_name and activity_name != "Todas Atividades":
            params["activity"] = activity_name
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = requests.get(
            f"{st.session_state.api_url}/events",
            headers=st.session_state.api_headers,
            timeout=20,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                events = data
            elif isinstance(data, dict) and 'events' in data:
                events = data['events']
            elif isinstance(data, dict) and 'data' in data:
                events = data['data']
            else:
                events = []
            
            if events:
                df = pd.DataFrame(events)
                
                # Mapear campos para o formato esperado pelo dashboard
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
                    'y': 'pos_y'
                }
                
                for old, new in column_mapping.items():
                    if old in df.columns and new not in df.columns:
                        df[new] = df[old]
                
                # Garantir colunas necessárias
                if 'duration_min' not in df.columns:
                    df['duration_min'] = 0.1
                if 'confidence' not in df.columns:
                    df['confidence'] = 0.95
                if 'pos_x' not in df.columns:
                    df['pos_x'] = 50
                if 'pos_y' not in df.columns:
                    df['pos_y'] = 35
                if 'tipo_evento' not in df.columns:
                    df['tipo_evento'] = 'Evento'
                
                return df
            else:
                st.info("Nenhum evento encontrado para os filtros selecionados")
                return pd.DataFrame()
        else:
            st.error(f"Erro ao carregar eventos: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro na requisição de eventos: {str(e)}")
        return pd.DataFrame()

# ==================== FUNÇÃO DO CAMPO DE RUGBY ====================

def create_rugby_field():
    """Cria um campo de rugby com dimensões oficiais"""
    
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
    """Tela de login para inserção do token da API"""
    
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="color: #1f3b73;">🏉 BIG Report - Rugby Analytics</h1>
            <h3 style="color: #2c5aa0;">Catapult Sports Integration</h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔑 Autenticação API Catapult")
            
            api_token = st.text_area(
                "Token JWT:",
                height=150,
                placeholder="Cole seu token JWT aqui...",
                help="Token fornecido pela Catapult Sports"
            )
            
            api_url = st.text_input(
                "URL da API:",
                value="https://backend-us.openfield.catapultsports.com",
                help="URL base da API Catapult"
            )
            
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

# ==================== DASHBOARD PRINCIPAL ====================

def main_dashboard():
    """Dashboard principal com carregamento em cascata"""
    
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar com carregamento em cascata
    st.sidebar.markdown("## 📂 Dados em Cascata")
    st.sidebar.info("Os dados são carregados em etapas:")
    st.sidebar.markdown("1️⃣ Atividades → 2️⃣ Equipes → 3️⃣ Atletas → 4️⃣ Eventos")
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 1: CARREGAR ATIVIDADES ==========
    st.sidebar.markdown("### 1️⃣ Atividades")
    
    if st.sidebar.button("🔄 Carregar Atividades", use_container_width=True):
        st.session_state.loading_activities = True
        with st.spinner("Carregando atividades da API..."):
            activities = load_activities_from_api()
            if activities:
                st.session_state.activities_data = activities
                st.sidebar.success(f"✅ {len(activities)} atividades carregadas")
            else:
                st.sidebar.error("❌ Falha ao carregar atividades")
        st.session_state.loading_activities = False
        st.rerun()
    
    if st.session_state.activities_data:
        selected_activity = st.sidebar.selectbox(
            "Selecionar Atividade:",
            ["Todas Atividades"] + st.session_state.activities_data
        )
        st.sidebar.success(f"📋 Atividade: {selected_activity}")
    else:
        selected_activity = "Todas Atividades"
        st.sidebar.warning("⚠️ Clique em 'Carregar Atividades' primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 2: CARREGAR EQUIPES ==========
    st.sidebar.markdown("### 2️⃣ Equipes")
    
    if st.session_state.activities_data:
        if st.sidebar.button("🔄 Carregar Equipes", use_container_width=True):
            st.session_state.loading_teams = True
            with st.spinner("Carregando equipes da API..."):
                teams = load_teams_from_api(selected_activity if selected_activity != "Todas Atividades" else None)
                if teams:
                    st.session_state.teams_data = teams
                    st.sidebar.success(f"✅ {len(teams)} equipes carregadas")
                else:
                    st.sidebar.error("❌ Falha ao carregar equipes")
            st.session_state.loading_teams = False
            st.rerun()
        
        if st.session_state.teams_data:
            selected_team = st.sidebar.selectbox(
                "Selecionar Equipe:",
                ["Todas Equipes"] + st.session_state.teams_data
            )
            st.sidebar.success(f"🏆 Equipe: {selected_team}")
        else:
            selected_team = "Todas Equipes"
            st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    else:
        selected_team = "Todas Equipes"
        st.sidebar.warning("⚠️ Carregue as atividades primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 3: CARREGAR ATLETAS ==========
    st.sidebar.markdown("### 3️⃣ Atletas")
    
    if st.session_state.teams_data:
        if st.sidebar.button("🔄 Carregar Atletas", use_container_width=True):
            st.session_state.loading_players = True
            with st.spinner("Carregando atletas da API..."):
                players = load_players_from_api(
                    selected_team if selected_team != "Todas Equipes" else None,
                    selected_activity if selected_activity != "Todas Atividades" else None
                )
                if players:
                    st.session_state.players_data = players
                    st.sidebar.success(f"✅ {len(players)} atletas carregados")
                else:
                    st.sidebar.error("❌ Falha ao carregar atletas")
            st.session_state.loading_players = False
            st.rerun()
        
        if st.session_state.players_data:
            selected_player = st.sidebar.selectbox(
                "Selecionar Atleta:",
                ["Todos Atletas"] + st.session_state.players_data
            )
            st.sidebar.success(f"👤 Atleta: {selected_player}")
        else:
            selected_player = "Todos Atletas"
            st.sidebar.warning("⚠️ Carregue os atletas primeiro")
    else:
        selected_player = "Todos Atletas"
        st.sidebar.warning("⚠️ Carregue as equipes primeiro")
    
    st.sidebar.markdown("---")
    
    # ========== NÍVEL 4: PERÍODO E EVENTOS ==========
    st.sidebar.markdown("### 4️⃣ Período")
    
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
    
    # ========== BOTÃO PARA CARREGAR EVENTOS ==========
    st.sidebar.markdown("### 🎯 Carregar Eventos")
    
    if st.sidebar.button("📊 CARREGAR EVENTOS", type="primary", use_container_width=True):
        if st.session_state.players_data:
            st.session_state.loading_events = True
            with st.spinner("Carregando eventos da API..."):
                df_events = load_events_from_api(
                    team_name=selected_team if selected_team != "Todas Equipes" else None,
                    player_name=selected_player if selected_player != "Todos Atletas" else None,
                    activity_name=selected_activity if selected_activity != "Todas Atividades" else None,
                    start_date=start_date,
                    end_date=end_date
                )
                st.session_state.events_data = df_events
                
                if not df_events.empty:
                    st.sidebar.success(f"✅ {len(df_events)} eventos carregados")
                else:
                    st.sidebar.warning("⚠️ Nenhum evento encontrado")
            st.session_state.loading_events = False
            st.rerun()
        else:
            st.sidebar.error("❌ Carregue os atletas primeiro!")
    
    st.sidebar.markdown("---")
    
    # Mostrar status dos carregamentos
    if st.session_state.loading_activities:
        st.sidebar.info("⏳ Carregando atividades...")
    if st.session_state.loading_teams:
        st.sidebar.info("⏳ Carregando equipes...")
    if st.session_state.loading_players:
        st.sidebar.info("⏳ Carregando atletas...")
    if st.session_state.loading_events:
        st.sidebar.info("⏳ Carregando eventos...")
    
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
            fig_campo.add_trace(go.Scatter(
                x=df['pos_x'],
                y=df['pos_y'],
                mode='markers',
                marker=dict(
                    size=df['duration_min'] * 20 if 'duration_min' in df.columns else 10,
                    color=df['confidence'] if 'confidence' in df.columns else 0.5,
                    colorscale='Viridis',
                    showscale=True,
                    opacity=0.7
                ),
                text=[f"Tipo: {row.get('tipo_evento', 'N/A')}<br>Duração: {row.get('duration_min', 0):.2f}min" 
                      for _, row in df.iterrows()],
                hoverinfo='text'
            ))
        
        st.plotly_chart(fig_campo, use_container_width=True)
        
        # Tabela de eventos
        st.markdown('<div class="sub-header">📋 Detalhe dos Eventos</div>', unsafe_allow_html=True)
        st.dataframe(df.head(100), use_container_width=True)
        
        # Gráficos
        if 'tipo_evento' in df.columns:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_pie = px.pie(values=df['tipo_evento'].value_counts().values,
                                names=df['tipo_evento'].value_counts().index,
                                title="Distribuição por Tipo")
                st.plotly_chart(fig_pie, use_container_width=True)
        
        if 'duration_min' in df.columns:
            with col_g2:
                fig_bar = px.bar(x=range(min(50, len(df))), y=df['duration_min'].head(50),
                                title="Duração dos Eventos")
                st.plotly_chart(fig_bar, use_container_width=True)
                
    elif st.session_state.events_data is not None and st.session_state.events_data.empty:
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados")
        st.info("Tente ajustar o período ou selecionar diferentes equipes/atletas")
    else:
        st.info("👈 Selecione os filtros na barra lateral e clique em 'CARREGAR EVENTOS'")
        st.markdown("""
        ### Como usar:
        1. **Carregue as Atividades** - Clique no botão na sidebar
        2. **Carregue as Equipes** - Baseado na atividade selecionada
        3. **Carregue os Atletas** - Baseado na equipe selecionada
        4. **Defina o Período** - Escolha os dias
        5. **Carregue os Eventos** - Clique no botão principal
        
        Os dados serão carregados em cascata da API real da Catapult!
        """)

# ==================== MAIN ====================

def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()