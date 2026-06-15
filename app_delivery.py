import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from urllib.parse import quote

try:
    from sqlalchemy import create_engine
    import pymssql
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

st.set_page_config(
    page_title="Mamma Jamma · Delivery",
    page_icon="🛵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# TEMA — Paleta Mamma Jamma
# ══════════════════════════════════════════════════════════════════════════════
C = {
    'bg':      '#0D0705', 'bg2':    '#1A0F0A', 'bg3':     '#2A1810',
    'border':  '#4A2E1A', 'gold':   '#C8973A', 'gold_lt': '#E8C090',
    'cream':   '#F5E6D3', 'muted':  '#A08060', 'red':     '#C43A3A',
    'noite':   '#7B5EA7', 'dia':    '#C4763A', 'interc':  '#4A8B6F',
    'grid':    '#3A2010', 'delivery': '#FF6B35',
}
CORES_TURNO = {'Noite': C['noite'], 'Intercalado': C['interc'], 'Dia': C['dia']}

def chart_layout(**kw):
    base = dict(
        plot_bgcolor=C['bg2'], paper_bgcolor=C['bg2'],
        font=dict(color=C['cream'], family='Inter, sans-serif'),
        xaxis=dict(gridcolor=C['grid'], color=C['muted'], showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=C['grid'], color=C['muted'], showgrid=True, zeroline=False),
        legend=dict(bgcolor=C['bg3'], bordercolor=C['border'], borderwidth=1, font=dict(color=C['cream'])),
        margin=dict(l=0, r=0, t=30, b=10),
        hoverlabel=dict(bgcolor=C['bg3'], bordercolor=C['gold'], font=dict(color=C['cream'])),
    )
    base.update(kw)
    return base

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;background-color:{C['bg']}!important;color:{C['cream']}!important;}}
#MainMenu,footer,header{{visibility:hidden;}}
[data-testid="collapsedControl"]{{display:none!important;}}
.stApp,.block-container{{background-color:{C['bg']};}}
div[data-testid="metric-container"]{{background:{C['bg3']}!important;border:1px solid {C['border']}!important;border-radius:12px;padding:16px 18px;}}
div[data-testid="metric-container"] label{{color:{C['muted']}!important;font-size:12px!important;}}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{C['gold']}!important;font-size:22px!important;font-weight:600!important;}}
.stTabs [data-baseweb="tab-list"]{{border-bottom:2px solid {C['border']};background:{C['bg2']};}}
.stTabs [aria-selected="true"]{{color:{C['gold']}!important;border-bottom:2px solid {C['gold']}!important;background:{C['bg3']}!important;}}
.stSelectbox>div>div, .stSelectbox [data-baseweb="select"]{{background:{C['bg3']}!important;border-color:{C['border']}!important;color:{C['cream']}!important;}}
.stDateInput input{{background:{C['bg3']}!important;border-color:{C['border']}!important;color:{C['cream']}!important;}}
h1,h2,h3,h4,p,span,li{{color:{C['cream']}!important;}}
</style>
""", unsafe_allow_html=True)

# Data padrão: segunda-feira da semana atual
hoje = date.today()
segunda = hoje - timedelta(days=hoje.weekday())

# ══════════════════════════════════════════════════════════════════════════════
# CONEXÃO BANCO
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_db_connection():
    if not DB_AVAILABLE:
        return None
    try:
        import os
        # Tenta ler do secrets.toml (local) ou Environment variables (Azure)
        server = st.secrets.get('db_server') or os.getenv('db_server')
        database = st.secrets.get('db_database') or os.getenv('db_database')
        username = st.secrets.get('db_username') or os.getenv('db_username')
        password = st.secrets.get('db_password') or os.getenv('db_password')
        
        password_encoded = quote(password, safe='')
        connection_string = f"mssql+pymssql://{username}:{password_encoded}@{server}/{database}"
        engine = create_engine(connection_string, echo=False)
        return engine
    except Exception as e:
        st.error(f"❌ Erro ao conectar no banco: {str(e)[:100]}")
        return None

def fmt_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def carregar_lojas():
    """Carrega lista de lojas do banco"""
    engine = get_db_connection()
    if engine is None:
        return ['Todas']
    
    try:
        query = "SELECT DISTINCT Loja_Nome FROM vw_BI_dLoja ORDER BY Loja_Nome"
        df = pd.read_sql_query(query, engine)
        lojas = ['Todas'] + df['Loja_Nome'].tolist()
        return lojas
    except:
        return ['Todas']

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_delivery(data_ini, data_fim, loja_nome=None):
    """Carrega dados de DELIVERY"""
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        query = f"""
        SELECT 
            v.Data, v.loja_id, l.Loja_Nome, v.venda_id, v.SK_Funcionario,
            v.Faturamento_Bruto, v.Qtd_Item, v.Turno_Venda, v.ModoVenda, v.qtd_pessoas
        FROM vw_BI_fVendas v
        LEFT JOIN vw_BI_dLoja l ON v.loja_id = l.Loja_ID
        WHERE v.ModoVenda = 'Delivery'
        AND v.Data >= '{data_ini}'
        AND v.Data <= '{data_fim}'
        {f"AND l.Loja_Nome = '{loja_nome}'" if loja_nome else ""}
        """
        
        df = pd.read_sql_query(query, engine)
        if df.empty:
            return None
        
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)[:100]}")
        return None

def filtros_globais(key_prefix='dlv'):
    """Filtros de data e loja"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_ini = st.date_input('📅 Data Inicial', value=segunda, key=f'{key_prefix}_data_ini')
    with col2:
        data_fim = st.date_input('📅 Data Final', value=date.today(), key=f'{key_prefix}_data_fim')
    with col3:
        with st.spinner('🏪 Carregando lojas...'):
            lojas_opt = carregar_lojas()
        loja_sel = st.selectbox('🏪 Loja', lojas_opt, key=f'{key_prefix}_loja')
        loja_nome = None if loja_sel == 'Todas' else loja_sel
    
    return data_ini, data_fim, loja_nome, loja_sel

# ══════════════════════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════════════════════
def view_delivery():
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>📊 Dashboard de Delivery</h1>", unsafe_allow_html=True)
    
    data_ini, data_fim, loja_nome, loja_sel = filtros_globais('dlv_gg')
    
    with st.spinner('🔍 Carregando dados de delivery...'):
        df = carregar_dados_delivery(data_ini, data_fim, loja_nome)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum delivery encontrado neste período.')
        return
    
    # KPIs
    faturamento = df['Faturamento_Bruto'].sum()
    qtd_deliveries = df['venda_id'].nunique()
    ticket_medio = faturamento / qtd_deliveries if qtd_deliveries > 0 else 0
    itens = df['Qtd_Item'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('🛵 Faturamento', fmt_brl(faturamento))
    col2.metric('📦 Deliveries', f"{int(qtd_deliveries):,}".replace(',', '.'))
    col3.metric('🎯 Ticket Médio', fmt_brl(ticket_medio))
    col4.metric('📊 Itens', f"{int(itens):,}".replace(',', '.'))
    st.divider()
    
    # Abas
    tab1, tab2, tab3 = st.tabs(['📈 Tendência', '🏪 Por Loja', '⏰ Horário & Turno'])
    
    with tab1:
        st.markdown('#### 📈 Faturamento Diário')
        df_daily = df.groupby('Data')['Faturamento_Bruto'].sum().reset_index().sort_values('Data')
        fig = px.area(df_daily, x='Data', y='Faturamento_Bruto', color_discrete_sequence=[C['delivery']])
        fig.update_traces(line=dict(width=3))
        fig.update_layout(**chart_layout(height=400, xaxis_title='Data', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown('#### 🏪 Por Loja')
        df_loja = df.groupby('Loja_Nome').agg({'Faturamento_Bruto': 'sum', 'venda_id': 'nunique'}).reset_index()
        df_loja.columns = ['Loja', 'Faturamento', 'Deliveries']
        df_loja = df_loja.sort_values('Faturamento', ascending=False)
        
        fig = px.bar(df_loja, x='Loja', y='Faturamento', color='Deliveries', color_continuous_scale='Oranges',
                    text=df_loja['Faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Loja', yaxis_title='Faturamento (R$)', margin=dict(b=120)))
        st.plotly_chart(fig, use_container_width=True)
        
        df_loja_display = df_loja.copy()
        df_loja_display['Faturamento'] = df_loja_display['Faturamento'].apply(fmt_brl)
        st.dataframe(df_loja_display, use_container_width=True, hide_index=True)
    
    with tab3:
        st.markdown('#### ⏰ Por Turno')
        df_turno = df.groupby('Turno_Venda')['Faturamento_Bruto'].sum().reset_index().sort_values('Faturamento_Bruto', ascending=False)
        
        fig = px.bar(df_turno, x='Turno_Venda', y='Faturamento_Bruto', color='Turno_Venda',
                    color_discrete_map=CORES_TURNO, text=df_turno['Faturamento_Bruto'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=350, xaxis_title='Turno', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)

def header():
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🛵 Mamma Jamma Delivery</h1>", unsafe_allow_html=True)
    st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
header()
view_delivery()
