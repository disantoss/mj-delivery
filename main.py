"""
MJ Delivery - App Principal com OAuth Google Manual
Tema Dark centralizado AQUI, sem conflitos!
"""

# ════════════════════════════════════════════════════════════════════════════
# ✅ CARREGAR VARIÁVEIS DE AMBIENTE DO .env
# ════════════════════════════════════════════════════════════════════════════
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from login_oauth_manual import main_login, renderizar_usuario_logado

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO STREAMLIT - CHAMADO UMA ÚNICA VEZ, NO INÍCIO!
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MJ Delivery",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════════════
# CORES E TEMA DARK
# ════════════════════════════════════════════════════════════════════════════
C = {
    'bg':      '#0D0705',
    'bg2':     '#1A0F0A',
    'bg3':     '#2A1810',
    'border':  '#4A2E1A',
    'gold':    '#C8973A',
    'cream':   '#F5E6D3',
    'muted':   '#A08060',
    'grid':    '#3A2010',
    'delivery': '#FF6B35',
}

# ════════════════════════════════════════════════════════════════════════════
# CSS TEMA ESCURO - APLICADO UMA ÚNICA VEZ!
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* FUNDO ESCURO */
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {C['bg']} !important;
    color: {C['cream']} !important;
}}

/* ESCONDER MENU DO STREAMLIT */
#MainMenu, footer, header {{
    visibility: hidden;
}}

[data-testid="collapsedControl"] {{
    display: none !important;
}}

/* CONTAINERS ESCUROS */
.stApp, .block-container {{
    background-color: {C['bg']} !important;
}}

/* MÉTRICAS */
div[data-testid="metric-container"] {{
    background: {C['bg3']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 12px;
    padding: 16px 18px;
}}

div[data-testid="metric-container"] label {{
    color: {C['muted']} !important;
    font-size: 12px !important;
}}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C['gold']} !important;
    font-size: 22px !important;
    font-weight: 600 !important;
}}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{
    border-bottom: 2px solid {C['border']};
    background: {C['bg2']};
}}

.stTabs [aria-selected="true"] {{
    color: {C['gold']} !important;
    border-bottom: 2px solid {C['gold']} !important;
    background: {C['bg3']} !important;
}}

/* SELECTBOX E DATE INPUT */
.stSelectbox > div > div, .stSelectbox [data-baseweb="select"] {{
    background: {C['bg3']} !important;
    border: 1px solid {C['muted']} !important;
    color: {C['cream']} !important;
    border-radius: 8px !important;
}}

.stDateInput input {{
    background: {C['bg3']} !important;
    border: 1px solid {C['muted']} !important;
    color: {C['cream']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}

/* LABELS */
.stSelectbox label, .stDateInput label {{
    color: {C['gold']} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    margin-bottom: 8px !important;
}}

/* DROPDOWNS */
[data-baseweb="popover"], 
[data-baseweb="popover"] [data-baseweb="menu"], 
[data-baseweb="menu"], 
[role="listbox"], 
[role="option"], 
[data-baseweb="select"] [data-baseweb="list"] {{
    background: {C['bg2']} !important;
}}

[data-baseweb="popover"] li, 
[data-baseweb="menu"] li, 
[role="listbox"] li, 
[role="option"], 
[data-baseweb="select"] [data-baseweb="list"] li {{
    color: {C['cream']} !important;
    background: {C['bg2']} !important;
    font-weight: 600 !important;
    padding: 10px !important;
}}

[data-baseweb="popover"] li:hover, 
[data-baseweb="menu"] li:hover, 
[role="option"]:hover, 
[data-baseweb="select"] [data-baseweb="list"] li:hover {{
    background: {C['bg3']} !important;
    color: {C['gold']} !important;
}}

/* TEXTOS */
h1, h2, h3, h4, p, span, li {{
    color: {C['cream']} !important;
}}

/* DIVIDER */
.stDivider {{
    background-color: {C['border']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# LÓGICA DA APP
# ════════════════════════════════════════════════════════════════════════════

# Verificar autenticação
if st.session_state.get("authentication_status") is None or "token" not in st.session_state:
    # Mostrar tela de login
    main_login()

elif st.session_state.get("authentication_status") is True and "token" in st.session_state:
    # Usuário logado - importar e rodar dashboard_content
    try:
        # Importar a função principal
        from dashboard_content import view_main
        
        # Renderizar com sidebar de logout
        renderizar_usuario_logado(view_main)
    
    except ImportError as e:
        st.error(f"❌ Erro ao carregar dashboard: {str(e)}")
        st.info("Certifique-se de que o arquivo `dashboard_content.py` está na mesma pasta que `main.py`")
        
        if st.button("🔄 Tentar Novamente"):
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Erro geral: {str(e)}")
        
        if st.button("🔄 Tentar Novamente"):
            st.rerun()
