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

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;background-color:{C['bg']}!important;color:{C['cream']}!important;}}
#MainMenu,footer,header{{visibility:hidden;}}
[data-testid="collapsedControl"]{{display:none!important;}}
.stApp,.block-container{{background-color:{C['bg']};}}
div[data-testid="metric-container"]{{background:{C['bg3']}!important;border:1px solid {C['border']}!important;border-radius:12px;padding:16px 18px;}}
div[data-testid="metric-container"] label{{color:{C['muted']}!important;font-size:12px!important;}}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{C['gold']}!important;font-size:22px!important;font-weight:600!important;}}
.stTabs [data-baseweb="tab-list"]{{border-bottom:2px solid {C['border']};background:{C['bg2']};}}
.stTabs [aria-selected="true"]{{color:{C['gold']}!important;border-bottom:2px solid {C['gold']}!important;background:{C['bg3']}!important;}}
.stSelectbox>div>div, .stSelectbox [data-baseweb="select"]{{background:{C['bg3']}!important;border:1px solid {C['muted']}!important;color:{C['cream']}!important;border-radius:8px!important;}}
.stDateInput input{{background:{C['bg3']}!important;border:1px solid {C['muted']}!important;color:{C['cream']}!important;border-radius:8px!important;font-weight:600!important;}}
.stSelectbox label, .stDateInput label{{color:{C['gold']}!important;font-weight:600!important;font-size:13px!important;margin-bottom:8px!important;}}
[data-baseweb="popover"], [data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="menu"], [role="listbox"], [role="option"], [data-baseweb="select"] [data-baseweb="list"]{{background:{C['bg2']}!important;}}
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [role="listbox"] li, [role="option"], [data-baseweb="select"] [data-baseweb="list"] li{{color:{C['cream']}!important;background:{C['bg2']}!important;font-weight:600!important;padding:10px!important;}}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover, [role="option"]:hover, [data-baseweb="select"] [data-baseweb="list"] li:hover{{background:{C['bg3']}!important;color:{C['gold']}!important;}}
h1,h2,h3,h4,p,span,li{{color:{C['cream']}!important;}}
</style>
""", unsafe_allow_html=True)

# Data padrão: últimas 5 semanas (período atual + 4 semanas atrás)
hoje = date.today()
segunda_atual = hoje - timedelta(days=hoje.weekday())  # Segunda desta semana
data_ini_padrao = segunda_atual - timedelta(weeks=4)   # 4 semanas atrás

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

def calcular_semanas(df):
    """Calcula faturamento semana atual vs semana anterior"""
    if df is None or df.empty:
        return None, None, None
    
    hoje = pd.Timestamp(date.today())
    segunda_atual = hoje - timedelta(days=hoje.weekday())
    segunda_anterior = segunda_atual - timedelta(weeks=1)
    
    # Semana atual (segunda até hoje)
    df_semana_atual = df[(df['Data'] >= segunda_atual) & (df['Data'] <= hoje)]
    fat_semana_atual = df_semana_atual['Faturamento_Bruto'].sum() if not df_semana_atual.empty else 0
    
    # Semana anterior (segunda até domingo da semana anterior)
    domingo_anterior = segunda_atual - timedelta(days=1)
    df_semana_anterior = df[(df['Data'] >= segunda_anterior) & (df['Data'] <= domingo_anterior)]
    fat_semana_anterior = df_semana_anterior['Faturamento_Bruto'].sum() if not df_semana_anterior.empty else 0
    
    # Variação
    variacao = ((fat_semana_atual - fat_semana_anterior) / fat_semana_anterior * 100) if fat_semana_anterior > 0 else 0
    
    return fat_semana_atual, fat_semana_anterior, variacao

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
    """Carrega dados de DELIVERY com CanalVenda e Marca"""
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        query = f"""
        SELECT 
            v.Data, v.loja_id, l.Loja_Nome, v.venda_id,
            v.SK_Funcionario, v.Faturamento_Bruto, v.Qtd_Item, 
            v.Turno_Venda, v.ModoVenda, v.CanalVenda, v.Marca
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
        data_ini = st.date_input('📅 Data Inicial', value=data_ini_padrao, key=f'{key_prefix}_data_ini')
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
    """Dashboard principal de Delivery"""
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
    tab1, tab2, tab3, tab4 = st.tabs(['📈 Tendência', '🏪 Por Loja', '⏰ Horário & Turno', '🛣️ Por Canal'])
    
    with tab1:
        st.markdown('#### 📊 Comparação: Semana Atual vs Semana Anterior')
        
        # Calcular semanas
        fat_atual, fat_anterior, variacao = calcular_semanas(df)
        
        # Cards de comparação
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('📆 Semana Atual', fmt_brl(fat_atual))
        with col2:
            st.metric('📅 Semana Anterior', fmt_brl(fat_anterior))
        with col3:
            cor = '🟢' if variacao >= 0 else '🔴'
            st.metric(f'{cor} Variação', f'{variacao:.1f}%')
        
        st.divider()
        st.markdown('#### 📈 Faturamento Diário (Últimas 5 Semanas)')
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
    
    with tab4:
        st.markdown('#### 🛣️ Faturamento por Canal de Venda')
        df_canal = df.groupby('CanalVenda').agg({
            'Faturamento_Bruto': 'sum',
            'venda_id': 'nunique',
            'Qtd_Item': 'sum'
        }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
        
        df_canal.columns = ['Canal', 'Faturamento', 'Qtd_Vendas', 'Itens']
        
        # Cards de KPI por Canal
        cols = st.columns(len(df_canal))
        for idx, (_, row) in enumerate(df_canal.iterrows()):
            with cols[idx]:
                st.metric(f"🛣️ {row['Canal']}", fmt_brl(row['Faturamento']))
        
        st.divider()
        
        # Gráfico de barras
        fig = px.bar(df_canal, x='Canal', y='Faturamento',
                    color='Canal', color_discrete_map=CORES_CANAL,
                    text=df_canal['Faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=400, xaxis_title='Canal de Venda', yaxis_title='Faturamento (R$)'))
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_canal, use_container_width=True, hide_index=True)

def view_categorias():
    """Análise por Canal, Marca e Loja"""
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🏷️ Canal • Marca • Loja</h1>", unsafe_allow_html=True)
    
    data_ini, data_fim, loja_nome, loja_sel = filtros_globais('cat')
    
    with st.spinner('🔍 Carregando dados por categoria...'):
        df = carregar_dados_delivery(data_ini, data_fim, loja_nome)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum delivery encontrado neste período.')
        return
    
    # ════════════════════════════════════════════════════════════════
    # Se filtrou por loja específica, mostrar análise detalhada
    # ════════════════════════════════════════════════════════════════
    if loja_nome:
        st.markdown(f"### 🏪 Análise Detalhada: **{loja_nome}**")
        st.divider()
        
        # KPIs gerais da loja
        fat_loja = df['Faturamento_Bruto'].sum()
        deliveries_loja = df['venda_id'].nunique()
        canais_ativos = df['CanalVenda'].nunique()
        marcas_ativas = df['Marca'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric('💰 Faturamento', fmt_brl(fat_loja))
        col2.metric('📦 Deliveries', f"{int(deliveries_loja):,}".replace(',', '.'))
        col3.metric('🛣️ Canais Ativos', f"{int(canais_ativos)}")
        col4.metric('🏷️ Marcas Ativas', f"{int(marcas_ativas)}")
        st.divider()
        
        # Tabs para análise da loja
        tab_canal, tab_marca, tab_cruzado, tab_tabela = st.tabs(
            ['🛣️ Canais', '🏷️ Marcas', '🔄 Cruzamento', '📋 Tabela Completa']
        )
        
        with tab_canal:
            st.markdown(f'#### 🛣️ Faturamento por Canal em {loja_nome}')
            df_canal_loja = df.groupby('CanalVenda').agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique',
                'Qtd_Item': 'sum'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
            df_canal_loja.columns = ['Canal', 'Faturamento', 'Vendas', 'Itens']
            
            # KPI Cards
            cols_canal = st.columns(len(df_canal_loja))
            for idx, (_, row) in enumerate(df_canal_loja.iterrows()):
                with cols_canal[idx]:
                    st.metric(row['Canal'], fmt_brl(row['Faturamento']), f"{int(row['Vendas'])} vendas")
            
            st.divider()
            
            # Gráfico de barras
            fig_canal = px.bar(df_canal_loja, x='Canal', y='Faturamento',
                              color='Canal', color_discrete_map=CORES_CANAL,
                              text=df_canal_loja['Faturamento'].apply(fmt_brl),
                              hover_data=['Vendas', 'Itens'])
            fig_canal.update_traces(textposition='outside')
            fig_canal.update_layout(**chart_layout(height=400, xaxis_title='Canal', yaxis_title='Faturamento (R$)'))
            st.plotly_chart(fig_canal, use_container_width=True)
            
            # Gráfico de pizza
            fig_pie = px.pie(df_canal_loja, names='Canal', values='Faturamento',
                            color_discrete_map=CORES_CANAL)
            fig_pie.update_layout(**chart_layout(height=400))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab_marca:
            st.markdown(f'#### 🏷️ Faturamento por Marca em {loja_nome}')
            df_marca_loja = df.groupby('Marca').agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
            df_marca_loja.columns = ['Marca', 'Faturamento', 'Vendas']
            
            fig_marca = px.bar(df_marca_loja, x='Faturamento', y='Marca', orientation='h',
                              text=df_marca_loja['Faturamento'].apply(fmt_brl),
                              color='Faturamento', color_continuous_scale='Oranges')
            fig_marca.update_traces(textposition='outside')
            fig_marca.update_layout(**chart_layout(height=max(400, len(df_marca_loja)*30), xaxis_title='Faturamento (R$)'))
            st.plotly_chart(fig_marca, use_container_width=True)
        
        with tab_cruzado:
            st.markdown(f'#### 🔄 Marcas por Canal em {loja_nome}')
            
            # Criar tabela de cruzamento
            df_cruzado = df.groupby(['CanalVenda', 'Marca'])['Faturamento_Bruto'].sum().reset_index()
            df_pivot = df_cruzado.pivot_table(
                values='Faturamento_Bruto',
                index='Marca',
                columns='CanalVenda',
                fill_value=0,
                aggfunc='sum'
            )
            df_pivot = df_pivot.sort_values(by=df_pivot.columns[0] if len(df_pivot.columns) > 0 else df_pivot.index[0], ascending=False)
            
            # Heatmap
            fig_heatmap = px.imshow(df_pivot,
                                   labels=dict(color='Faturamento (R$)'),
                                   color_continuous_scale='YlOrRd',
                                   text_auto=True,
                                   aspect='auto')
            fig_heatmap.update_layout(**chart_layout(height=max(400, len(df_pivot)*25)))
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Sunburst para visualizar hierarquia
            st.markdown('#### 🌟 Sunburst: Hierarquia de Faturamento')
            df_sunburst = df.groupby(['CanalVenda', 'Marca'])['Faturamento_Bruto'].sum().reset_index()
            df_sunburst.columns = ['Canal', 'Marca', 'Faturamento']
            
            if not df_sunburst.empty:
                # Preparar dados para sunburst de forma simplificada
                canais_unicos = df_sunburst['Canal'].unique().tolist()
                
                # Criar listas manualmente para evitar problemas
                labels_list = ['Todas as Lojas'] + canais_unicos + df_sunburst['Marca'].tolist()
                parents_list = [''] + ['Todas as Lojas'] * len(canais_unicos) + df_sunburst['Canal'].tolist()
                values_list = [df_sunburst['Faturamento'].sum()] + \
                             [df_sunburst[df_sunburst['Canal']==c]['Faturamento'].sum() for c in canais_unicos] + \
                             df_sunburst['Faturamento'].tolist()
                
                fig_sunburst = go.Figure(go.Sunburst(
                    labels=labels_list,
                    parents=parents_list,
                    values=values_list,
                    branchvalues='total',
                    marker=dict(colorscale='YlOrRd')
                ))
                fig_sunburst.update_layout(**chart_layout(height=500))
                st.plotly_chart(fig_sunburst, use_container_width=True)
            else:
                st.info('Sem dados para exibir sunburst neste período')
        
        with tab_tabela:
            st.markdown(f'#### 📋 Detalhamento Completo: {loja_nome}')
            detalhe = df.groupby(['CanalVenda', 'Marca']).agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique',
                'Qtd_Item': 'sum'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
            detalhe.columns = ['Canal', 'Marca', 'Faturamento', 'Vendas', 'Itens']
            detalhe['Faturamento_fmt'] = detalhe['Faturamento'].apply(fmt_brl)
            
            st.dataframe(
                detalhe[['Canal', 'Marca', 'Faturamento_fmt', 'Vendas', 'Itens']],
                use_container_width=True, hide_index=True
            )
    
    else:
        # ════════════════════════════════════════════════════════════════
        # Análise GERAL (todas as lojas)
        # ════════════════════════════════════════════════════════════════
        st.markdown('### 📊 Análise Geral - Todos os Canais & Marcas')
        st.divider()
        
        # KPIs gerais
        fat_geral = df['Faturamento_Bruto'].sum()
        deliveries_geral = df['venda_id'].nunique()
        canais_ativos = df['CanalVenda'].nunique()
        marcas_ativas = df['Marca'].nunique()
        lojas_ativas = df['Loja_Nome'].nunique()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric('💰 Faturamento', fmt_brl(fat_geral))
        col2.metric('📦 Deliveries', f"{int(deliveries_geral):,}".replace(',', '.'))
        col3.metric('🏪 Lojas', f"{int(lojas_ativas)}")
        col4.metric('🛣️ Canais', f"{int(canais_ativos)}")
        col5.metric('🏷️ Marcas', f"{int(marcas_ativas)}")
        st.divider()
        
        tab_canal, tab_marca, tab_loja_canal, tab_tabela_geral = st.tabs(
            ['🛣️ Por Canal', '🏷️ Por Marca', '🏪 Loja × Canal', '📋 Tabela']
        )
        
        with tab_canal:
            st.markdown('#### 🛣️ Faturamento por Canal (Geral)')
            df_canal_geral = df.groupby('CanalVenda').agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique',
                'Qtd_Item': 'sum'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
            df_canal_geral.columns = ['Canal', 'Faturamento', 'Vendas', 'Itens']
            
            cols_canal = st.columns(len(df_canal_geral))
            for idx, (_, row) in enumerate(df_canal_geral.iterrows()):
                with cols_canal[idx]:
                    st.metric(row['Canal'], fmt_brl(row['Faturamento']))
            
            st.divider()
            
            fig = px.bar(df_canal_geral, x='Canal', y='Faturamento',
                        color='Canal', color_discrete_map=CORES_CANAL,
                        text=df_canal_geral['Faturamento'].apply(fmt_brl))
            fig.update_traces(textposition='outside')
            fig.update_layout(**chart_layout(height=400, xaxis_title='Canal', yaxis_title='Faturamento (R$)'))
            st.plotly_chart(fig, use_container_width=True)
        
        with tab_marca:
            st.markdown('#### 🏷️ Faturamento por Marca (Geral)')
            df_marca_geral = df.groupby('Marca').agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False).head(15)
            df_marca_geral.columns = ['Marca', 'Faturamento', 'Vendas']
            
            fig = px.bar(df_marca_geral, x='Faturamento', y='Marca', orientation='h',
                        text=df_marca_geral['Faturamento'].apply(fmt_brl),
                        color='Faturamento', color_continuous_scale='Oranges')
            fig.update_traces(textposition='outside')
            fig.update_layout(**chart_layout(height=400, xaxis_title='Faturamento (R$)'))
            st.plotly_chart(fig, use_container_width=True)
        
        with tab_loja_canal:
            st.markdown('#### 🏪 Faturamento por Loja e Canal')
            df_loja_canal = df.groupby(['Loja_Nome', 'CanalVenda'])['Faturamento_Bruto'].sum().reset_index()
            
            fig = px.bar(df_loja_canal, x='Loja_Nome', y='Faturamento_Bruto',
                        color='CanalVenda', color_discrete_map=CORES_CANAL,
                        barmode='stack')
            fig.update_layout(**chart_layout(height=400, xaxis_title='Loja', yaxis_title='Faturamento (R$)',
                                             margin=dict(b=120)))
            st.plotly_chart(fig, use_container_width=True)
        
        with tab_tabela_geral:
            st.markdown('#### 📋 Detalhamento Geral')
            detalhe_geral = df.groupby(['Loja_Nome', 'CanalVenda', 'Marca']).agg({
                'Faturamento_Bruto': 'sum',
                'venda_id': 'nunique',
                'Qtd_Item': 'sum'
            }).reset_index().sort_values('Faturamento_Bruto', ascending=False)
            detalhe_geral.columns = ['Loja', 'Canal', 'Marca', 'Faturamento', 'Vendas', 'Itens']
            detalhe_geral['Faturamento_fmt'] = detalhe_geral['Faturamento'].apply(fmt_brl)
            
            st.dataframe(
                detalhe_geral[['Loja', 'Canal', 'Marca', 'Faturamento_fmt', 'Vendas', 'Itens']],
                use_container_width=True, hide_index=True
            )

def header():
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🛵 Mamma Jamma Delivery</h1>", unsafe_allow_html=True)
    st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
header()

# Abas principais
main_tab1, main_tab2 = st.tabs(['📊 Dashboard', '🏷️ Canais & Marcas'])

with main_tab1:
    view_delivery()

with main_tab2:
    view_categorias()
