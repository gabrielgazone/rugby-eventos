import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
import json

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="Rugby Performance Dashboard", 
    layout="wide",
    page_icon="🏉"
)

# ========== INICIALIZAÇÃO DA SESSION STATE ==========
if 'token' not in st.session_state:
    st.session_state.token = None
if 'dados_carregados' not in st.session_state:
    st.session_state.dados_carregados = False
if 'atividades_df' not in st.session_state:
    st.session_state.atividades_df = None
if 'jogadores_df' not in st.session_state:
    st.session_state.jogadores_df = None

# ========== FUNÇÕES DE API GENÉRICAS ==========
def api_get(endpoint: str, params: dict = None, token: str = None) -> dict:
    """Função genérica para chamadas GET à API"""
    if not token:
        token = st.session_state.token
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Usar URL base do token (extrair do próprio token ou fixa)
    base_url = "https://backend-us.openfield.catapultsports.com"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Erro {response.status_code}: {response.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
        return {}

def api_post(endpoint: str, data: dict, token: str = None) -> dict:
    """Função genérica para chamadas POST à API"""
    if not token:
        token = st.session_state.token
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://backend-us.openfield.catapultsports.com"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Erro {response.status_code}: {response.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
        return {}

# ========== FUNÇÕES DE CARREGAMENTO DE DADOS ==========
@st.cache_data(ttl=300, show_spinner=False)
def carregar_temporadas(token: str) -> pd.DataFrame:
    """Carrega temporadas/activity groups"""
    data = api_get("/v1/activity_groups", token=token)
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        if 'start_date' in df.columns:
            df['ano'] = pd.to_datetime(df['start_date']).dt.year
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_atividades(token: str, season_id: str = None) -> pd.DataFrame:
    """Carrega atividades com filtro opcional de temporada"""
    params = {}
    if season_id:
        params['activity_group_id'] = season_id
    
    data = api_get("/v1/activities", params=params, token=token)
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['ano'] = df['date'].dt.year
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_jogadores(token: str) -> pd.DataFrame:
    """Carrega todos os jogadores/atletas"""
    data = api_get("/v1/athletes", token=token)
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        # Mapear posição (ajustar conforme sua API)
        if 'position_name' in df.columns:
            df['posicao'] = df['position_name']
        else:
            df['posicao'] = 'Não informado'
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_eventos(token: str, athlete_id: str, activity_id: str) -> pd.DataFrame:
    """Carrega eventos de um jogador em uma atividade específica"""
    endpoint = f"/v1/athletes/{athlete_id}/events"
    params = {'activity_id': activity_id}
    data = api_get(endpoint, params=params, token=token)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame()

# ========== FUNÇÃO DO CAMPO DE RUGBY ==========
def criar_campo_rugby():
    """Cria o campo de rugby regulation (100m x 70m) com visual profissional"""
    fig = go.Figure()
    
    # Fundo do campo
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=70,
                  line=dict(color="white", width=2),
                  fillcolor="rgba(34, 139, 34, 0.6)",
                  layer="below")
    
    # Linha do meio campo
    fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=70,
                  line=dict(color="white", width=2, dash="dash"))
    
    # Círculo central
    fig.add_shape(type="circle", x0=46, y0=31, x1=54, y1=39,
                  line=dict(color="white", width=2),
                  fillcolor="rgba(255,255,255,0)")
    
    # Linhas de 22m
    fig.add_shape(type="line", x0=22, y0=0, x1=22, y1=70,
                  line=dict(color="white", width=1.5))
    fig.add_shape(type="line", x0=78, y0=0, x1=78, y1=70,
                  line=dict(color="white", width=1.5))
    
    # Linhas de 10m
    fig.add_shape(type="line", x0=10, y0=0, x1=10, y1=70,
                  line=dict(color="white", width=1, dash="dot"))
    fig.add_shape(type="line", x0=90, y0=0, x1=90, y1=70,
                  line=dict(color="white", width=1, dash="dot"))
    
    # Linhas de try (5m)
    fig.add_shape(type="line", x0=5, y0=0, x1=5, y1=70,
                  line=dict(color="white", width=1, dash="dot"))
    fig.add_shape(type="line", x0=95, y0=0, x1=95, y1=70,
                  line=dict(color="white", width=1, dash="dot"))
    
    # Configurar layout
    fig.update_layout(
        plot_bgcolor='darkgreen',
        paper_bgcolor='#1a1a2e',
        xaxis=dict(
            title="Metros", 
            range=[-2, 102], 
            gridcolor='rgba(255,255,255,0.15)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            title="Metros", 
            range=[-2, 72], 
            gridcolor='rgba(255,255,255,0.15)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(color='white')
        ),
        height=600,
        width=900,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.7)",
            font=dict(color="white", size=12)
        )
    )
    
    # Adicionar anotações das áreas
    anotacoes = [
        (11, 35, "10m", 10),
        (27, 35, "22m", 10),
        (50, -3, "MEIO CAMPO", 12),
        (73, 35, "22m", 10),
        (89, 35, "10m", 10)
    ]
    
    for x, y, texto, tamanho in anotacoes:
        fig.add_annotation(
            x=x, y=y, text=texto, 
            showarrow=False, 
            font=dict(color="white", size=tamanho, family="Arial Black"),
            bgcolor="rgba(0,0,0,0.5)",
            borderpad=2
        )
    
    return fig

def adicionar_eventos_ao_campo(fig, eventos_df):
    """Adiciona os marcadores dos eventos no campo"""
    
    # Configurações por tipo de evento
    config_eventos = {
        'scrum': {'cor': '#FF4444', 'tamanho': 16, 'nome': 'Scrum', 'simbolo': 'circle', 'opacidade': 0.9},
        'contact': {'cor': '#FF9933', 'tamanho': 13, 'nome': 'Contact', 'simbolo': 'square', 'opacidade': 0.8},
        'kick': {'cor': '#33CCFF', 'tamanho': 11, 'nome': 'Kick', 'simbolo': 'triangle-up', 'opacidade': 0.8},
        'lineout': {'cor': '#CC33FF', 'tamanho': 17, 'nome': 'Lineout', 'simbolo': 'star', 'opacidade': 0.9},
        'rhie': {'cor': '#33FF33', 'tamanho': 14, 'nome': 'RHIE', 'simbolo': 'diamond', 'opacidade': 0.8}
    }
    
    # Agrupar por tipo para legenda
    tipos_adicionados = set()
    
    for idx, evento in eventos_df.iterrows():
        tipo = evento.get('event_type', '').lower()
        
        # Identificar qual tipo de evento
        tipo_real = None
        for key in config_eventos.keys():
            if key in tipo:
                tipo_real = key
                break
        
        if not tipo_real:
            continue
        
        config = config_eventos[tipo_real]
        
        # Obter coordenadas (simular se não existir)
        x = evento.get('x_coordinate') or evento.get('coordinate_x')
        y = evento.get('y_coordinate') or evento.get('coordinate_y')
        
        if pd.isna(x) or x is None:
            x = np.random.uniform(15, 85)
        if pd.isna(y) or y is None:
            y = np.random.uniform(10, 60)
        
        # Texto para hover
        hover_text = (
            f"<b>{config['nome']}</b><br>"
            f"⏱️ Tempo: {evento.get('timestamp', 'N/A')}<br>"
            f"⚡ Big Time: {evento.get('big_time', evento.get('duration', 'N/A'))}s<br>"
            f"📍 Posição: ({x:.1f}, {y:.1f})"
        )
        
        # Mostrar na legenda apenas uma vez por tipo
        show_legend = tipo_real not in tipos_adicionados
        
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=config['tamanho'],
                color=config['cor'],
                symbol=config['simbolo'],
                line=dict(color='white', width=2),
                opacity=config['opacidade']
            ),
            text=hover_text,
            hoverinfo='text',
            name=config['nome'],
            legendgroup=tipo_real,
            showlegend=show_legend
        ))
        
        tipos_adicionados.add(tipo_real)
    
    return fig

# ========== INTERFACE PRINCIPAL ==========
st.title("🏉 Rugby Performance Analytics Dashboard")
st.markdown("---")

# ========== SIDEBAR - AUTENTICAÇÃO E FILTROS ==========
with st.sidebar:
    st.header("🔐 1. Autenticação API")
    
    # Input do token
    token_input = st.text_area(
        "**Cole seu token JWT da Catapult:**",
        height=120,
        help="Token gerado no OpenField Cloud em Settings > API Tokens.\n\nO token não é salvo, apenas usado durante a sessão.",
        placeholder="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Carregar Token", type="primary", use_container_width=True):
            if token_input and len(token_input) > 50:
                st.session_state.token = token_input.strip()
                st.session_state.dados_carregados = False
                st.session_state.atividades_df = None
                st.session_state.jogadores_df = None
                st.cache_data.clear()
                st.success("Token carregado! Configure os filtros abaixo.")
                st.rerun()
            else:
                st.error("Token inválido! Cole um token JWT válido.")
    
    with col2:
        if st.button("🗑️ Limpar Token", use_container_width=True):
            st.session_state.token = None
            st.session_state.dados_carregados = False
            st.cache_data.clear()
            st.rerun()
    
    # Mostrar status do token
    if st.session_state.token:
        st.success(f"✅ Token ativo ({st.session_state.token[:30]}...)")
    else:
        st.info("⏳ Aguardando token...")
    
    st.divider()
    
    # ========== FILTROS (aparecem só após token) ==========
    if st.session_state.token:
        st.header("🎯 2. Filtros de Dados")
        
        # Spinner para carregamento inicial
        with st.spinner("Carregando dados básicos..."):
            if not st.session_state.dados_carregados:
                st.session_state.atividades_df = carregar_atividades(st.session_state.token)
                st.session_state.jogadores_df = carregar_jogadores(st.session_state.token)
                st.session_state.dados_carregados = True
        
        # Verificar se há dados
        if st.session_state.atividades_df.empty:
            st.warning("⚠️ Nenhuma atividade encontrada para este token.")
        else:
            # 1. FILTRO DE TEMPORADA
            if 'ano' in st.session_state.atividades_df.columns:
                anos_disponiveis = sorted(st.session_state.atividades_df['ano'].dropna().unique(), reverse=True)
                temporada = st.selectbox("📅 Temporada", anos_disponiveis)
            else:
                temporada = st.selectbox("📅 Temporada", ["2024", "2023", "2022"])
            
            # Filtrar atividades por temporada
            if 'ano' in st.session_state.atividades_df.columns:
                atividades_temp = st.session_state.atividades_df[st.session_state.atividades_df['ano'] == temporada]
            else:
                atividades_temp = st.session_state.atividades_df
            
            # 2. FILTRO DE TIPO (TREINO/JOGO)
            tipo_options = ["Todos", "Treino", "Jogo", "Partida", "Amistoso"]
            tipo_selecionado = st.selectbox("⚽ Tipo de Atividade", tipo_options)
            
            if tipo_selecionado != "Todos":
                atividades_filtradas = atividades_temp[
                    atividades_temp['activity_name'].str.contains(tipo_selecionado, case=False, na=False)
                ]
            else:
                atividades_filtradas = atividades_temp
            
            # 3. SELECIONAR ATIVIDADE
            if not atividades_filtradas.empty:
                atividade_selecionada = st.selectbox(
                    "📋 Atividade",
                    atividades_filtradas['activity_name'].tolist()
                )
                activity_id = atividades_filtradas[
                    atividades_filtradas['activity_name'] == atividade_selecionada
                ]['id'].iloc[0]
            else:
                atividade_selecionada = None
                activity_id = None
                st.warning("Nenhuma atividade encontrada com os filtros atuais.")
            
            # 4. FILTRO DE POSIÇÃO
            if not st.session_state.jogadores_df.empty:
                posicoes = ["Todas"] + sorted(st.session_state.jogadores_df['posicao'].dropna().unique())
                posicao_selecionada = st.selectbox("🏉 Posição", posicoes)
                
                if posicao_selecionada != "Todas":
                    jogadores_filtrados = st.session_state.jogadores_df[
                        st.session_state.jogadores_df['posicao'] == posicao_selecionada
                    ]
                else:
                    jogadores_filtrados = st.session_state.jogadores_df
            else:
                st.warning("⚠️ Nenhum jogador encontrado.")
                jogadores_filtrados = pd.DataFrame()
            
            # 5. SELECIONAR JOGADOR
            if not jogadores_filtrados.empty:
                jogador_selecionado = st.selectbox(
                    "👤 Jogador",
                    jogadores_filtrados['name'].tolist()
                )
                athlete_id = jogadores_filtrados[
                    jogadores_filtrados['name'] == jogador_selecionado
                ]['id'].iloc[0]
            else:
                jogador_selecionado = None
                athlete_id = None
            
            st.divider()
            
            # 6. SELEÇÃO DE EVENTOS
            st.subheader("🏆 3. Eventos para Visualizar")
            mostrar_scrums = st.checkbox("Scrum Count", value=True)
            mostrar_contacts = st.checkbox("Contact Involvement", value=True)
            mostrar_kicks = st.checkbox("Kick Count", value=True)
            mostrar_lineouts = st.checkbox("Total Lineout Jump Count", value=True)
            mostrar_rhie = st.checkbox("RHIE Total Bouts", value=True)
            
            st.divider()
            
            # Botão para atualizar o dashboard
            if st.button("🚀 Atualizar Dashboard", type="primary", use_container_width=True):
                if activity_id and athlete_id:
                    st.session_state.activity_id = activity_id
                    st.session_state.athlete_id = athlete_id
                    st.session_state.mostrar_scrums = mostrar_scrums
                    st.session_state.mostrar_contacts = mostrar_contacts
                    st.session_state.mostrar_kicks = mostrar_kicks
                    st.session_state.mostrar_lineouts = mostrar_lineouts
                    st.session_state.mostrar_rhie = mostrar_rhie
                    st.rerun()
                else:
                    st.error("❌ Selecione uma atividade e um jogador primeiro!")
    
    else:
        st.info("👈 **Cole seu token e clique em 'Carregar Token'** para começar.")
        st.stop()

# ========== ÁREA PRINCIPAL - DASHBOARD ==========
if (st.session_state.token and 
    'activity_id' in st.session_state and 
    'athlete_id' in st.session_state):
    
    st.subheader(f"📊 Análise do Jogador")
    
    # Carregar eventos
    with st.spinner("Carregando eventos..."):
        eventos_raw = carregar_eventos(
            st.session_state.token,
            st.session_state.athlete_id,
            st.session_state.activity_id
        )
    
    # Filtrar eventos por tipo selecionado
    eventos_filtrados = pd.DataFrame()
    metricas_dict = {}
    
    if st.session_state.mostrar_scrums:
        scrum_events = eventos_raw[eventos_raw['event_type'].str.contains('scrum', case=False, na=False)] if not eventos_raw.empty else pd.DataFrame()
        eventos_filtrados = pd.concat([eventos_filtrados, scrum_events]) if not eventos_filtrados.empty else scrum_events
        metricas_dict['Scrum'] = len(scrum_events)
    
    if st.session_state.mostrar_contacts:
        contact_events = eventos_raw[eventos_raw['event_type'].str.contains('contact', case=False, na=False)] if not eventos_raw.empty else pd.DataFrame()
        eventos_filtrados = pd.concat([eventos_filtrados, contact_events]) if not eventos_filtrados.empty else contact_events
        metricas_dict['Contact Involvement'] = len(contact_events)
    
    if st.session_state.mostrar_kicks:
        kick_events = eventos_raw[eventos_raw['event_type'].str.contains('kick', case=False, na=False)] if not eventos_raw.empty else pd.DataFrame()
        eventos_filtrados = pd.concat([eventos_filtrados, kick_events]) if not eventos_filtrados.empty else kick_events
        metricas_dict['Kick'] = len(kick_events)
    
    if st.session_state.mostrar_lineouts:
        lineout_events = eventos_raw[eventos_raw['event_type'].str.contains('lineout', case=False, na=False)] if not eventos_raw.empty else pd.DataFrame()
        eventos_filtrados = pd.concat([eventos_filtrados, lineout_events]) if not eventos_filtrados.empty else lineout_events
        metricas_dict['Lineout'] = len(lineout_events)
    
    if st.session_state.mostrar_rhie:
        rhie_events = eventos_raw[eventos_raw['event_type'].str.contains('rhie', case=False, na=False)] if not eventos_raw.empty else pd.DataFrame()
        eventos_filtrados = pd.concat([eventos_filtrados, rhie_events]) if not eventos_filtrados.empty else rhie_events
        metricas_dict['RHIE'] = len(rhie_events)
    
    # ========== MÉTRICAS EM CARDS ==========
    col1, col2, col3, col4, col5 = st.columns(5)
    
    cards = [
        (col1, 'Scrum', metricas_dict.get('Scrum', 0), '🟠'),
        (col2, 'Contact', metricas_dict.get('Contact Involvement', 0), '🟡'),
        (col3, 'Kick', metricas_dict.get('Kick', 0), '🔵'),
        (col4, 'Lineout', metricas_dict.get('Lineout', 0), '🟣'),
        (col5, 'RHIE', metricas_dict.get('RHIE', 0), '🟢')
    ]
    
    for col, nome, valor, icone in cards:
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1e2e, #2a2a3e); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #3a3a4e;">
                <h3 style="margin:0; font-size: 1.8rem;">{icone} {valor}</h3>
                <p style="margin:0; color: #aaa;">{nome}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ========== CAMPO DE RUGBY ==========
    st.markdown("---")
    st.subheader("🏟️ Mapa de Eventos no Campo")
    
    if not eventos_filtrados.empty:
        fig = criar_campo_rugby()
        fig = adicionar_eventos_ao_campo(fig, eventos_filtrados)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📋 Detalhamento dos Eventos", expanded=False):
            colunas_exibir = ['timestamp', 'event_type', 'duration', 'big_time']
            colunas_existentes = [col for col in colunas_exibir if col in eventos_filtrados.columns]
            if colunas_existentes:
                st.dataframe(eventos_filtrados[colunas_existentes], use_container_width=True)
            else:
                st.info("Detalhes adicionais não disponíveis para estes eventos.")
    else:
        fig = criar_campo_rugby()
        st.plotly_chart(fig, use_container_width=True)
        st.warning("⚠️ Nenhum evento encontrado para os filtros selecionados.")
    
else:
    # Estado inicial - nenhum dado carregado ainda
    st.info("""
    ### 🏉 Bem-vindo ao Dashboard de Performance Rugby
    
    **Como usar:**
    
    1. 👈 Na barra lateral, cole seu token JWT da API Catapult
    2. Clique em **"Carregar Token"**
    3. Selecione **Temporada, Atividade, Posição e Jogador**
    4. Escolha quais eventos deseja visualizar
    5. Clique em **"Atualizar Dashboard"**
    
    **O que você verá:**
    - 📊 Contagem total dos eventos selecionados
    - 🏟️ Campo de rugby com a localização de cada evento
    - 📋 Tabela detalhada com timestamps e métricas
    
    ---
    *Desenvolvido para análise de performance usando dados da Catapult OpenField*
    """)