import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from urllib.parse import quote
from sqlalchemy import text

try:
    from sqlalchemy import create_engine
    import pymssql
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# ✅ st.set_page_config() REMOVIDO - JÁ CONFIGURADO EM main.py!
# ═══════════════════════════════════════════════════════════════════════════════

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
CORES_CANAL = {
    '99Food': '#E74C3C',
    'Ifood': '#F39C12', 
    'Loja': '#27AE60',
    'Alphacode': '#3498DB'
}

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

# Data padrão: últimas 2 semanas (período atual + 1 semana atrás)
hoje = date.today()
segunda_atual = hoje - timedelta(days=hoje.weekday())  # Segunda desta semana
data_ini_padrao = segunda_atual - timedelta(weeks=2)   # 2 semanas atrás

# ══════════════════════════════════════════════════════════════════════════════
# CONEXÃO BANCO
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_db_connection():
    if not DB_AVAILABLE:
        return None
    try:
        import os
        try:
            server = st.secrets['db_server']
            database = st.secrets['db_database']
            username = st.secrets['db_username']
            password = st.secrets['db_password']
        except (FileNotFoundError, KeyError):
            server = os.getenv('db_server')
            database = os.getenv('db_database')
            username = os.getenv('db_username')
            password = os.getenv('db_password')
        
        password_encoded = quote(password, safe='')
        connection_string = f"mssql+pymssql://{username}:{password_encoded}@{server}/{database}"
        engine = create_engine(connection_string, echo=False)
        return engine
    except Exception as e:
        st.error(f"❌ Erro ao conectar no banco: {str(e)[:100]}")
        return None

def fmt_brl(val):
    if pd.isna(val) or val == 0:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS - OTIMIZADO COM PARAMETRIZAÇÃO
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
    """
    ✅ OTIMIZADO: Carrega dados de DELIVERY com CanalVenda e Marca
    
    IMPORTANTE: Carrega 2 semanas ANTES de data_ini pra poder calcular 
    a semana anterior corretamente!
    
    Melhorias:
    - Parametrização adequada (sem SQL injection)
    - INNER JOIN (melhor performance)
    - Traz período + 2 semanas anteriores (pra cálculo, não exibe)
    - Data como pd.Timestamp para comparações rápidas
    
    Args:
        data_ini: Data inicial (datetime.date)
        data_fim: Data final (datetime.date)
        loja_nome: Nome da loja (str) ou None para todas
    """
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        # ✅ Trazer 2 semanas ANTES pra calcular semana anterior corretamente
        data_ini_estendida = data_ini - timedelta(weeks=2)
        
        # ✅ Query parametrizada - evita SQL injection
        query_text = text("""
        SELECT 
            v.Data, v.loja_id, l.Loja_Nome, v.venda_id,
            v.SK_Funcionario, v.Faturamento_Bruto, v.Qtd_Item, 
            v.Turno_Venda, v.ModoVenda, v.CanalVenda, v.Marca
        FROM vw_BI_fVendas v
        INNER JOIN vw_BI_dLoja l ON v.loja_id = l.Loja_ID
        WHERE v.ModoVenda = 'Delivery'
            AND v.Data >= :data_ini_estendida
            AND v.Data <= :data_fim
            AND (:loja_nome IS NULL OR l.Loja_Nome = :loja_nome)
        ORDER BY v.Data DESC
        """)
        
        params = {
            'data_ini_estendida': data_ini_estendida,
            'data_fim': data_fim,
            'loja_nome': loja_nome
        }
        
        df = pd.read_sql_query(query_text, engine, params=params)
        
        if df.empty:
            return None
        
        # Converter Data para datetime se necessário
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)[:150]}")
        return None

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_categorias(data_ini, data_fim):
    """
    ✅ OTIMIZADO: Carrega dados pra análise de Canais & Marcas
    
    Sem filtro de loja específica (análise geral)
    """
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        query_text = text("""
        SELECT 
            v.Data, v.venda_id, v.Faturamento_Bruto, v.Qtd_Item,
            v.CanalVenda, v.Marca, l.Loja_Nome
        FROM vw_BI_fVendas v
        INNER JOIN vw_BI_dLoja l ON v.loja_id = l.Loja_ID
        WHERE v.Data >= :data_ini
            AND v.Data <= :data_fim
        ORDER BY v.Data DESC
        """)
        
        params = {
            'data_ini': data_ini,
            'data_fim': data_fim
        }
        
        df = pd.read_sql_query(query_text, engine, params=params)
        
        if df.empty:
            return None
        
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de categorias: {str(e)[:150]}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE SEMANAS - LÓGICA MANTIDA DO ORIGINAL (em Python é OK aqui)
# ══════════════════════════════════════════════════════════════════════════════
def calcular_semanas(df, data_ini, data_fim=None):
    """
    ✅ SIMPLES: Semana Atual vs Semana Anterior
    
    Se filtrar 08/06 a 14/06:
    - Semana Atual: 08/06 a 14/06 (período filtrado)
    - Semana Anterior: 01/06 a 07/06 (7 dias antes do início)
    
    Args:
        df: DataFrame com dados
        data_ini: Data inicial do filtro
        data_fim: Data final do filtro
    
    Retorna:
        fat_semana_atual, fat_semana_anterior, variacao (%)
    """
    if df is None or df.empty:
        return 0, 0, 0
    
    # Converter pra Timestamp
    data_ini_ts = pd.Timestamp(data_ini)
    data_fim_ts = pd.Timestamp(data_fim) if data_fim else pd.Timestamp(data_ini)
    
    # ✅ Semana ATUAL = período que o usuário filtrou
    df_semana_atual = df[(df['Data'] >= data_ini_ts) & (df['Data'] <= data_fim_ts)]
    fat_semana_atual = df_semana_atual['Faturamento_Bruto'].sum() if not df_semana_atual.empty else 0
    
    # ✅ Semana ANTERIOR = 7 dias antes (mesmo período, só que anterior)
    dias_periodo = (data_fim_ts - data_ini_ts).days + 1  # Quantidade de dias no período
    data_anterior_fim = data_ini_ts - timedelta(days=1)  # Dia antes do início
    data_anterior_ini = data_anterior_fim - timedelta(days=dias_periodo-1)  # Mesmo tamanho
    
    df_semana_anterior = df[(df['Data'] >= data_anterior_ini) & (df['Data'] <= data_anterior_fim)]
    fat_semana_anterior = df_semana_anterior['Faturamento_Bruto'].sum() if not df_semana_anterior.empty else 0
    
    # Variação percentual
    if fat_semana_anterior > 0:
        variacao = ((fat_semana_atual - fat_semana_anterior) / fat_semana_anterior * 100)
    else:
        variacao = 0
    
    return fat_semana_atual, fat_semana_anterior, variacao

def filtros_globais():
    """Retorna os filtros padrão"""
    return date.today() - timedelta(weeks=4), date.today(), 'Todas'

# ══════════════════════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════════════════════
def view_delivery():
    """Dashboard principal de Delivery - OTIMIZADO"""
    
    # ✅ Usar filtros_app unificados (sincronizados com outras abas)
    
    # Filtros inline
    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input('📅 Data Inicial', value=st.session_state.filtros_app['data_ini'], key='view_dlv_d_ini')
        st.session_state.filtros_app['data_ini'] = data_ini
    with col2:
        data_fim = st.date_input('📅 Data Final', value=st.session_state.filtros_app['data_fim'], key='view_dlv_d_fim')
        st.session_state.filtros_app['data_fim'] = data_fim
    with col3:
        with st.spinner('🏪 Carregando lojas...'):
            lojas_opt = carregar_lojas()
        loja_sel = st.selectbox('🏪 Loja', lojas_opt, index=lojas_opt.index(st.session_state.filtros_app['loja_sel']) if st.session_state.filtros_app['loja_sel'] in lojas_opt else 0, key='view_dlv_d_loja')
        st.session_state.filtros_app['loja_sel'] = loja_sel
        loja_nome = None if loja_sel == 'Todas' else loja_sel
    
    # ✅ OTIMIZADO: Apenas uma query, sem dados extras
    with st.spinner('🔍 Carregando dados de delivery...'):
        df = carregar_dados_delivery(data_ini, data_fim, loja_nome)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum delivery encontrado neste período.')
        return
    
    # ✅ FILTRAR para mostrar APENAS o período que o usuário filtrou
    # (df tem 2 semanas extras pra calcular semana anterior, mas exibir só o pedido)
    df_filtrado = df[(df['Data'] >= pd.Timestamp(data_ini)) & (df['Data'] <= pd.Timestamp(data_fim))]
    
    # KPIs usam APENAS o período filtrado
    faturamento = df_filtrado['Faturamento_Bruto'].sum()
    qtd_deliveries = df_filtrado['venda_id'].nunique()
    ticket_medio = faturamento / qtd_deliveries if qtd_deliveries > 0 else 0
    itens = df_filtrado['Qtd_Item'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('🛵 Faturamento', fmt_brl(faturamento))
    col2.metric('📦 Deliveries', f"{int(qtd_deliveries):,}".replace(',', '.'))
    col3.metric('🎯 Ticket Médio', fmt_brl(ticket_medio))
    col4.metric('📊 Itens', f"{int(itens):,}".replace(',', '.'))
    st.divider()
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs(['📈 Tendência', '🏪 Por Loja', '⏰ Horário & Turno', '🛣️ Por Canal'])
    
    with tab1:
        st.markdown('#### 📊 Comparação: Semana Atual vs Semana Anterior')
        
        # Calcular semanas
        fat_atual, fat_anterior, variacao = calcular_semanas(df, data_ini, data_fim)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('📆 Semana Atual', fmt_brl(fat_atual))
        with col2:
            st.metric('📅 Semana Anterior', fmt_brl(fat_anterior))
        with col3:
            cor = '🟢' if variacao >= 0 else '🔴'
            st.metric(f'{cor} Variação', f'{variacao:.1f}%')
        
        st.divider()
        st.markdown('#### 📈 Faturamento Diário (Período Filtrado)')
        df_daily = df_filtrado.groupby('Data')['Faturamento_Bruto'].sum().reset_index().sort_values('Data')
        fig = px.area(df_daily, x='Data', y='Faturamento_Bruto', color_discrete_sequence=[C['delivery']])
        fig.update_traces(line=dict(width=3))
        fig.update_layout(**chart_layout(height=400, xaxis_title='Data', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown('#### 🏪 Por Loja')
        df_loja = df_filtrado.groupby('Loja_Nome').agg({'Faturamento_Bruto': 'sum', 'venda_id': 'nunique'}).reset_index()
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
        df_turno = df_filtrado.groupby('Turno_Venda')['Faturamento_Bruto'].sum().reset_index().sort_values('Faturamento_Bruto', ascending=False)
        
        fig = px.bar(df_turno, x='Turno_Venda', y='Faturamento_Bruto', color='Turno_Venda',
                    color_discrete_map=CORES_TURNO, text=df_turno['Faturamento_Bruto'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=350, xaxis_title='Turno', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown('#### 🛣️ Faturamento por Canal de Venda')
        df_canal = df_filtrado.groupby('CanalVenda').agg({
            'Faturamento_Bruto': 'sum',
            'venda_id': 'nunique',
            'Qtd_Item': 'sum'
        }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
        
        df_canal.columns = ['Canal', 'Faturamento', 'Qtd_Vendas', 'Itens']
        
        cols = st.columns(len(df_canal))
        for idx, (_, row) in enumerate(df_canal.iterrows()):
            with cols[idx]:
                st.metric(f"🛣️ {row['Canal']}", fmt_brl(row['Faturamento']))
        
        st.divider()
        
        fig = px.bar(df_canal, x='Canal', y='Faturamento',
                    color='Canal', color_discrete_map=CORES_CANAL,
                    text=df_canal['Faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Canal de Venda', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_canal, use_container_width=True, hide_index=True)

def view_categorias():
    """Análise por Canal, Marca e Loja - OTIMIZADO"""
    
    # ✅ Usar filtros_app unificados (sincronizados com outras abas)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input('📅 Data Inicial', value=st.session_state.filtros_app['data_ini'], key='view_cat_d_ini')
        st.session_state.filtros_app['data_ini'] = data_ini
    with col2:
        data_fim = st.date_input('📅 Data Final', value=st.session_state.filtros_app['data_fim'], key='view_cat_d_fim')
        st.session_state.filtros_app['data_fim'] = data_fim
    with col3:
        with st.spinner('🏪 Carregando lojas...'):
            lojas_opt = carregar_lojas()
        loja_sel = st.selectbox('🏪 Loja', lojas_opt, index=lojas_opt.index(st.session_state.filtros_app['loja_sel']) if st.session_state.filtros_app['loja_sel'] in lojas_opt else 0, key='view_cat_d_loja')
        st.session_state.filtros_app['loja_sel'] = loja_sel
    
    with st.spinner('🔍 Carregando dados de categorias...'):
        df = carregar_dados_categorias(data_ini, data_fim)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum dado encontrado neste período.')
        return
    
    # Filtrar loja se necessário
    if loja_sel != 'Todas':
        df = df[df['Loja_Nome'] == loja_sel]
        if df.empty:
            st.warning('📭 Nenhum dado encontrado para esta loja.')
            return
    
    # KPIs gerais
    fat_geral = df['Faturamento_Bruto'].sum()
    vendas_geral = df['venda_id'].nunique()
    canais_ativos = df['CanalVenda'].nunique()
    marcas_ativas = df['Marca'].nunique()
    lojas_ativas = df['Loja_Nome'].nunique()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('💰 Faturamento', fmt_brl(fat_geral))
    col2.metric('📦 Vendas', f"{int(vendas_geral):,}".replace(',', '.'))
    col3.metric('🏪 Lojas', f"{int(lojas_ativas)}")
    col4.metric('🛣️ Canais', f"{int(canais_ativos)}")
    col5.metric('🏷️ Marcas', f"{int(marcas_ativas)}")
    st.divider()
    
    tab_canal, tab_marca, tab_loja, tab_tabela = st.tabs(['🛣️ Por Canal', '🏷️ Por Marca', '🏪 Por Loja', '📋 Tabela'])
    
    with tab_canal:
        st.markdown('#### 🛣️ Faturamento por Canal')
        df_canal = df.groupby('CanalVenda').agg({
            'Faturamento_Bruto': 'sum',
            'venda_id': 'nunique',
            'Qtd_Item': 'sum'
        }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
        df_canal.columns = ['Canal', 'Faturamento', 'Vendas', 'Itens']
        
        fig = px.bar(df_canal, x='Canal', y='Faturamento',
                    color='Canal', color_discrete_map=CORES_CANAL,
                    text=df_canal['Faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Canal', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_marca:
        st.markdown('#### 🏷️ Top 15 Marcas')
        df_marca = df.groupby('Marca').agg({
            'Faturamento_Bruto': 'sum',
            'venda_id': 'nunique'
        }).reset_index().sort_values('Faturamento_Bruto', ascending=False).head(15)
        df_marca.columns = ['Marca', 'Faturamento', 'Vendas']
        
        fig = px.bar(df_marca, x='Faturamento', y='Marca', orientation='h',
                    text=df_marca['Faturamento'].apply(fmt_brl),
                    color='Faturamento', color_continuous_scale='Oranges')
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_loja:
        st.markdown('#### 🏪 Por Loja')
        df_loja = df.groupby('Loja_Nome')['Faturamento_Bruto'].sum().reset_index().sort_values('Faturamento_Bruto', ascending=False)
        df_loja.columns = ['Loja', 'Faturamento']
        
        fig = px.bar(df_loja, x='Loja', y='Faturamento',
                    text=df_loja['Faturamento'].apply(fmt_brl),
                    color='Faturamento', color_continuous_scale='Oranges')
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Loja', yaxis_title='Faturamento (R$)', margin=dict(b=120)))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_tabela:
        st.markdown('#### 📋 Detalhamento Completo')
        detalhe = df.groupby(['Loja_Nome', 'CanalVenda', 'Marca']).agg({
            'Faturamento_Bruto': 'sum',
            'venda_id': 'nunique',
            'Qtd_Item': 'sum'
        }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
        detalhe.columns = ['Loja', 'Canal', 'Marca', 'Faturamento', 'Vendas', 'Itens']
        detalhe['Faturamento_fmt'] = detalhe['Faturamento'].apply(fmt_brl)
        
        st.dataframe(
            detalhe[['Loja', 'Canal', 'Marca', 'Faturamento_fmt', 'Vendas', 'Itens']],
            use_container_width=True, hide_index=True
        )

def header():
    """Renderiza o header principal"""
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🛵 Mamma Jamma Delivery</h1>", unsafe_allow_html=True)
    st.divider()

def view_main():
    """Função principal que renderiza header + tabs + views"""
    
    # ✅ INICIALIZAR FILTROS ÚNICOS (sincronizados entre abas)
    if 'filtros_app' not in st.session_state:
        st.session_state.filtros_app = {
            'data_ini': data_ini_padrao,
            'data_fim': date.today(),
            'loja_sel': 'MJP NYC'  # ✅ Padrão pré-filtrado
        }
    
    header()
    
    # Abas principais
    main_tab1, main_tab2 = st.tabs(['📊 Dashboard', '🏷️ Canais & Marcas'])
    
    with main_tab1:
        view_delivery()
    
    with main_tab2:
        view_categorias()

# ══════════════════════════════════════════════════════════════════════════════
# NÃO EXECUTAR AQUI - será chamado do main.py
# ══════════════════════════════════════════════════════════════════════════════
