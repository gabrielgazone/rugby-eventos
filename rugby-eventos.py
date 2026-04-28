import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import numpy as np
import json

# Configuração da página DEVE ser o primeiro comando Streamlit
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
    .login-container {
        max-width: 500px;
        margin: 100px auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .warning-text {
        color: #ff6b6b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES DE AUTENTICAÇÃO ====================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'api_connected' not in st.session_state:
        st.session_state.api_connected = False
    if 'api_token' not in st.session_state:
        st.session_state.api_token = None
    if 'api_base_url' not in st.session_state:
        st.session_state.api_base_url = "https://api.catapult.com/v1"

def test_api_connection(api_token, base_url):
    """Testa a conexão com a API da Catapult"""
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Tentativa de conexão com um endpoint básico
        # Nota: Ajuste o endpoint conforme a documentação real da Catapult
        response = requests.get(
            f"{base_url}/health",
            headers=headers,
            timeout=10
        )
        
        # Se a API não tiver endpoint /health, testamos com /teams ou outro básico
        if response.status_code == 404:
            response = requests.get(
                f"{base_url}/teams",
                headers=headers,
                timeout=10
            )
        
        # Consideramos sucesso se status for 200, 201, ou 401 (precisa de permissões específicas)
        if response.status_code in [200, 201]:
            return True, "Conexão realizada com sucesso!"
        elif response.status_code == 401:
            return False, "Token inválido ou não autorizado. Verifique suas credenciais."
        else:
            return False, f"Erro na conexão: Status {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout na conexão. Verifique sua internet ou o URL da API."
    except requests.exceptions.ConnectionError:
        return False, "Erro de conexão. Verifique o URL da API e sua conexão com a internet."
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def save_token_to_secrets(token):
    """
    Salva o token em um arquivo .streamlit/secrets.toml
    Nota: Isso é apenas para demonstração. Em produção, use um sistema seguro.
    """
    import os
    from pathlib import Path
    
    secrets_dir = Path(".streamlit")
    secrets_file = secrets_dir / "secrets.toml"
    
    # Criar diretório se não existir
    secrets_dir.mkdir(exist_ok=True)
    
    # Ler conteúdo existente ou criar novo
    existing_content = {}
    if secrets_file.exists():
        try:
            import tomllib
            with open(secrets_file, "rb") as f:
                existing_content = tomllib.load(f)
        except:
            pass
    
    # Atualizar com novo token
    existing_content["CATAPULT_API_KEY"] = token
    existing_content["CATAPULT_BASE_URL"] = "https://api.catapult.com/v1"
    
    # Escrever arquivo
    with open(secrets_file, "w") as f:
        f.write("# Catapult API Credentials\n")
        f.write(f'CATAPULT_API_KEY = "{token}"\n')
        f.write('CATAPULT_BASE_URL = "https://api.catapult.com/v1"\n')
    
    return True

# ==================== FUNÇÕES DE CARREGAMENTO DE DADOS ====================

@st.cache_data
def load_teams():
    """Carrega lista de equipes da API ou dados de exemplo"""
    if st.session_state.api_connected and st.session_state.api_token:
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.api_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{st.session_state.api_base_url}/teams",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                teams_data = response.json()
                # Adapte conforme a estrutura real da resposta da API
                if isinstance(teams_data, list):
                    return teams_data
                elif isinstance(teams_data, dict) and 'teams' in teams_data:
                    return teams_data['teams']
        except:
            pass
    
    # Dados de exemplo (fallback)
    return [
        "Estudiantes de La Plata",
        "CUBA", 
        "CULP",
        "Selección Argentina",
        "Los Pumas 7's"
    ]

@st.cache_data
def load_players(team=None):
    """Carrega lista de atletas da API ou dados de exemplo"""
    if st.session_state.api_connected and st.session_state.api_token:
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.api_token}",
                "Content-Type": "application/json"
            }
            url = f"{st.session_state.api_base_url}/players"
            if team:
                url += f"?team={team}"
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                players_data = response.json()
                if isinstance(players_data, list):
                    return players_data
                elif isinstance(players_data, dict) and 'players' in players_data:
                    return players_data['players']
        except:
            pass
    
    # Dados de exemplo (fallback)
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
    
    if team and team in players:
        return players[team]
    elif not team:
        all_players = []
        for team_players in players.values():
            all_players.extend(team_players)
        return list(set(all_players))
    else:
        return []

@st.cache_data
def load_activities():
    """Carrega atividades disponíveis da API ou dados de exemplo"""
    if st.session_state.api_connected and st.session_state.api_token:
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.api_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{st.session_state.api_base_url}/activities",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                activities_data = response.json()
                if isinstance(activities_data, list):
                    return [act.get('name', f"Activity {i}") for i, act in enumerate(activities_data)]
        except:
            pass
    
    # Dados de exemplo (fallback)
    dates = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        dates.append(f"Activity {date.strftime('%Y%m%d%H%M%S')} - {date.strftime('%d/%m/%Y %H:%M')}")
    return dates

@st.cache_data
def load_event_data(team, player, activity, days_period):
    """Carrega dados de eventos com filtros aplicados"""
    
    # Se conectado à API, tentar carregar dados reais
    if st.session_state.api_connected and st.session_state.api_token:
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.api_token}",
                "Content-Type": "application/json"
            }
            
            # Construir URL com parâmetros
            params = {
                "days": days_period,
                "limit": 1000
            }
            if team and team != "Todos":
                params["team"] = team
            if player and player != "Todos":
                params["player"] = player
            if activity and activity != "Última Atividade":
                params["activity"] = activity
            
            response = requests.get(
                f"{st.session_state.api_base_url}/events",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                events_data = response.json()
                if isinstance(events_data, list) and len(events_data) > 0:
                    return pd.DataFrame(events_data)
        except Exception as e:
            st.warning(f"Erro ao carregar dados da API: {str(e)}. Usando dados de exemplo.")
    
    # Dados de exemplo (fallback) - Gerar dados simulados
    np.random.seed(42)
    
    if player and player != "Todos":
        n_events = np.random.randint(15, 45)
    else:
        n_events = np.random.randint(30, 80)
    
    base_time = datetime.now() - timedelta(days=np.random.randint(1, days_period))
    start_times = []
    current_time = base_time
    
    for i in range(n_events):
        delta = timedelta(seconds=np.random.randint(30, 300))
        start_times.append(current_time.timestamp())
        current_time += delta
    
    eventos_data = {
        "tipo_evento": np.random.choice(["Contact", "Tackle", "Ruck", "Maul", "Scrum", "Lineout"], n_events),
        "end_time": [t + np.random.uniform(2, 15) for t in start_times],
        "start_time": start_times,
        "duration_min": np.random.uniform(0.01, 0.35, n_events),
        "back_in_game_min": np.random.uniform(0.03, 6.0, n_events),
        "confidence": np.random.uniform(0.95, 1.0, n_events),
        "pos_x": np.random.uniform(0, 100, n_events),
        "pos_y": np.random.uniform(0, 70, n_events),
        "equipe": team if team and team != "Todos" else "Equipe Exemplo",
        "atleta": player if player and player != "Todos" else "Atleta Exemplo",
        "atividade": activity if activity else "Atividade Exemplo"
    }
    
    df = pd.DataFrame(eventos_data)
    df = df.sort_values('start_time')
    
    return df

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
    
    return fig, field_length, field_width

# ==================== FUNÇÃO PRINCIPAL DO DASHBOARD ====================

def main_dashboard():
    """Função principal do dashboard após autenticação"""
    
    # Título principal
    st.markdown('<div class="main-header">🏉 BIG Report - Análisis de Retorno a la Actividad</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Barra lateral com filtros
    st.sidebar.markdown("## 📂 Filtros de Dados")
    
    # Status da conexão API
    if st.session_state.api_connected:
        st.sidebar.success("✅ Conectado à API Catapult")
    else:
        st.sidebar.warning("⚠️ Usando dados de demonstração")
        if st.sidebar.button("🔌 Conectar à API"):
            st.rerun()
    
    st.sidebar.markdown("---")
    
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
    
    # 3. Filtro de Atleta
    st.sidebar.markdown("### 👤 Atleta")
    players_dict = load_players()
    
    if selected_team != "Todos":
        available_players = load_players(selected_team)
    else:
        available_players = load_players()
    
    if not available_players:
        available_players = ["Todos"]
    else:
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
    
    # Carregar dados
    df = load_event_data(
        selected_team, 
        selected_player if selected_player != "Todos" else None, 
        selected_activity, 
        dias_periodo
    )
    
    # Aplicar filtro de tipo de evento
    if selected_event_type != "Todos" and 'tipo_evento' in df.columns:
        df = df[df["tipo_evento"] == selected_event_type]
    
    # Mostrar informações dos filtros
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**📊 Total de Eventos:** {len(df)}")
    st.sidebar.markdown(f"**📅 Período:** {dias_periodo} días")
    if selected_team != "Todos":
        st.sidebar.markdown(f"**🏆 Equipo:** {selected_team}")
    if selected_player != "Todos":
        st.sidebar.markdown(f"**👤 Atleta:** {selected_player}")
    
    # Métricas resumidas
    if len(df) > 0:
        total_eventos = len(df)
        tempo_medio_entre = df["back_in_game_min"].mean() if 'back_in_game_min' in df.columns else 0
        duracao_media = df["duration_min"].mean() if 'duration_min' in df.columns else 0
        carga_total = df["duration_min"].sum() if 'duration_min' in df.columns else 0
        confianca_media = df["confidence"].mean() if 'confidence' in df.columns else 0
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
    
    # Campo de Rugby
    st.markdown('<div class="sub-header">🏟️ Mapa de Calor - Atividade no Campo</div>', unsafe_allow_html=True)
    
    fig_campo, field_len, field_wid = create_rugby_field()
    
    if len(df) > 0 and 'pos_x' in df.columns and 'pos_y' in df.columns:
        scatter = fig_campo.add_trace(go.Scatter(
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
    
    # Tabela de eventos
    if len(df) > 0:
        st.markdown('<div class="sub-header">📋 Detalle de Eventos</div>', unsafe_allow_html=True)
        
        df_display = df.copy()
        if 'start_time' in df_display.columns:
            df_display["start_time_dt"] = pd.to_datetime(df_display["start_time"], unit='s')
        if 'end_time' in df_display.columns:
            df_display["end_time_dt"] = pd.to_datetime(df_display["end_time"], unit='s')
        
        display_cols = []
        for col in ['tipo_evento', 'start_time_dt', 'end_time_dt', 'duration_min', 'back_in_game_min', 'confidence']:
            if col in df_display.columns:
                display_cols.append(col)
        
        if 'equipe' in df_display.columns and selected_team == "Todos":
            display_cols.insert(1, 'equipe')
        if 'atleta' in df_display.columns and selected_player == "Todos":
            display_cols.insert(2, 'atleta')
        
        if display_cols:
            st.dataframe(
                df_display[display_cols],
                use_container_width=True
            )
    
    # Gráficos adicionais
    if len(df) > 0:
        st.markdown('<div class="sub-header">📈 Análise de Eventos</div>', unsafe_allow_html=True)
        
        col_graf1, col_graf2 = st.columns(2)
        
        if 'tipo_evento' in df.columns:
            with col_graf1:
                event_counts = df['tipo_evento'].value_counts()
                fig_pie = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Distribución por Tipo de Evento",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        if 'duration_min' in df.columns:
            with col_graf2:
                fig_duration = px.bar(
                    x=range(min(len(df), 50)),
                    y=df['duration_min'].head(50),
                    title="Duración por Evento (minutos)",
                    labels={"x": "Número de Evento", "y": "Duración (min)"}
                )
                fig_duration.update_traces(marker_color='steelblue')
                st.plotly_chart(fig_duration, use_container_width=True)
        
        col_graf3, col_graf4 = st.columns(2)
        
        if 'back_in_game_min' in df.columns:
            with col_graf3:
                fig_timeline = px.line(
                    x=range(len(df)),
                    y=df['back_in_game_min'],
                    title="Tiempo entre Eventos - Back in Game (minutos)",
                    labels={"x": "Secuencia de Eventos", "y": "Tiempo (min)"}
                )
                fig_timeline.update_traces(line=dict(color='orange', width=2))
                st.plotly_chart(fig_timeline, use_container_width=True)
        
        if 'confidence' in df.columns:
            with col_graf4:
                fig_conf = px.scatter(
                    x=range(len(df)),
                    y=df['confidence'],
                    title="Confianza por Evento",
                    labels={"x": "Evento", "y": "Confianza"},
                    color=df['confidence'],
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_conf, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption("📡 Datos obtenidos via API de Catapult Sports | Dashboard BIG Report - Análisis de Retorno a la Actividad")
    if not st.session_state.api_connected:
        st.caption("⚠️ Modo de demostración - Conecte à API Catapult para dados reais")

# ==================== TELA DE LOGIN/AUTENTICAÇÃO ====================

def login_screen():
    """Tela de login para inserção do token da API"""
    
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
            st.markdown("""
                <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-top: 2rem;">
                    <h3 style="text-align: center; color: #1f3b73;">🔑 Autenticação</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Input para o token da API
            api_token = st.text_input(
                "Token da API Catapult:",
                type="password",
                placeholder="Insira seu token de acesso da API Catapult",
                help="O token é fornecido pela Catapult Sports. Contate o suporte se não tiver um."
            )
            
            # Input para URL da API (opcional)
            api_url = st.text_input(
                "URL da API (opcional):",
                placeholder="https://api.catapult.com/v1",
                value="https://api.catapult.com/v1",
                help="URL base da API Catapult. Geralmente não é necessário alterar."
            )
            
            st.markdown("---")
            
            # Informações de ajuda
            with st.expander("ℹ️ Como obter um token da API Catapult?"):
                st.markdown("""
                    1. Acesse o portal da Catapult Sports
                    2. Navegue até Configurações > API Keys
                    3. Crie uma nova chave de API
                    4. Copie o token gerado
                    
                    **Modo de demonstração:** Se você não tem um token, clique em "Usar Modo de Demonstração" para testar o dashboard com dados simulados.
                """)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Conectar à API", type="primary", use_container_width=True):
                    if api_token:
                        with st.spinner("Conectando à API Catapult..."):
                            success, message = test_api_connection(api_token, api_url)
                            
                            if success:
                                st.session_state.api_token = api_token
                                st.session_state.api_base_url = api_url
                                st.session_state.api_connected = True
                                st.session_state.authenticated = True
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.warning("Por favor, insira o token da API")
            
            with col_btn2:
                if st.button("🎮 Usar Modo de Demonstração", use_container_width=True):
                    st.session_state.api_connected = False
                    st.session_state.authenticated = True
                    st.success("Modo de demonstração ativado! Usando dados simulados.")
                    st.rerun()

# ==================== MAIN ====================

def main():
    """Função principal do aplicativo"""
    
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        try:
            main_dashboard()
        except Exception as e:
            st.error(f"Erro ao carregar o dashboard: {str(e)}")
            st.info("Tente reiniciar o aplicativo ou contate o suporte.")
            
            if st.button("🔄 Reiniciar Sessão"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()