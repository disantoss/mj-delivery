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

# ═══════════════════════════════════════════════════════════════════════════════
# ✅ st.set_page_config() REMOVIDO - JÁ CONFIGURADO EM main.py!
# Streamlit exige que seja chamado UMA ÚNICA VEZ no primeiro arquivo executado
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

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO STREAMLIT — CSS GLOBAL JÁ APLICADO EM main.py
# ══════════════════════════════════════════════════════════════════════════════
# ✅ Não precisa aplicar CSS aqui - main.py já faz isso uma única vez!
# dashboard_content.py apenas define as paletas de cores para os gráficos

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

def calcular_semanas(df, data_ini, data_fim=None):
    """Calcula faturamento semana atual vs semana anterior com filtro correto
    
    Args:
        df: DataFrame com dados
        data_ini: Data inicial do filtro
        data_fim: Data final do filtro (se None, usa a última data dos dados)
    
    Retorna:
        fat_semana_atual, fat_semana_anterior, variacao (%)
    """
    if df is None or df.empty:
        return 0, 0, 0
    
    # Se data_fim não for passada, usar a última data do DataFrame
    if data_fim is None:
        data_fim = df['Data'].max().date() if hasattr(df['Data'].max(), 'date') else df['Data'].max()
    
    # Converter para pd.Timestamp se necessário
    data_fim_ts = pd.Timestamp(data_fim)
    
    # Calcular segunda desta semana (contendo data_fim)
    segunda_atual = data_fim_ts - timedelta(days=data_fim_ts.weekday())
    
    # Calcular segunda da semana anterior
    segunda_anterior = segunda_atual - timedelta(weeks=1)
    domingo_anterior = segunda_atual - timedelta(days=1)
    
    # ✅ FILTRAR POR data_ini TAMBÉM para não contar dados antes do período solicitado
    df_filtrado = df[(df['Data'] >= pd.Timestamp(data_ini))]
    
    # Semana atual: de segunda até data_fim (pode ser incompleta)
    df_semana_atual = df_filtrado[(df_filtrado['Data'] >= segunda_atual) & (df_filtrado['Data'] <= data_fim_ts)]
    fat_semana_atual = df_semana_atual['Faturamento_Bruto'].sum() if not df_semana_atual.empty else 0
    
    # Semana anterior: de segunda até domingo da semana anterior
    df_semana_anterior = df_filtrado[(df_filtrado['Data'] >= segunda_anterior) & (df_filtrado['Data'] <= domingo_anterior)]
    fat_semana_anterior = df_semana_anterior['Faturamento_Bruto'].sum() if not df_semana_anterior.empty else 0
    
    # Variação percentual
    if fat_semana_anterior > 0:
        variacao = ((fat_semana_atual - fat_semana_anterior) / fat_semana_anterior * 100)
    else:
        variacao = 0
    
    # 🔍 DEBUG: Mostrar valores calculados
    import sys
    print(f"\n📊 [DEBUG SEMANAS]", file=sys.stderr)
    print(f"  Data Final: {data_fim}", file=sys.stderr)
    print(f"  Segunda Atual: {segunda_atual.date()}", file=sys.stderr)
    print(f"  Domingo Anterior: {domingo_anterior.date()}", file=sys.stderr)
    print(f"  Faturamento Semana Atual ({segunda_atual.date()} até {data_fim}): R$ {fat_semana_atual:,.2f}", file=sys.stderr)
    print(f"  Faturamento Semana Anterior ({segunda_anterior.date()} até {domingo_anterior.date()}): R$ {fat_semana_anterior:,.2f}", file=sys.stderr)
    print(f"  Variação: {variacao:.1f}%\n", file=sys.stderr)
    
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
    """Carrega dados de DELIVERY com CanalVenda e Marca
    
    Carrega 2 semanas antes de data_ini para poder calcular semana anterior!
    """
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        # ✅ Carregar 2 semanas ANTES de data_ini para poder calcular semana anterior
        data_ini_estendida = data_ini - timedelta(weeks=2)
        
        query = f"""
        SELECT 
            v.Data, v.loja_id, l.Loja_Nome, v.venda_id,
            v.SK_Funcionario, v.Faturamento_Bruto, v.Qtd_Item, 
            v.Turno_Venda, v.ModoVenda, v.CanalVenda, v.Marca
        FROM vw_BI_fVendas v
        LEFT JOIN vw_BI_dLoja l ON v.loja_id = l.Loja_ID
        WHERE v.ModoVenda = 'Delivery'
        AND v.Data >= '{data_ini_estendida}'
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

def filtros_globais():
    """Retorna os filtros padrão sem elementos duplicados"""
    return date.today() - timedelta(weeks=4), date.today(), 'Todas'

# ══════════════════════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════════════════════
def view_delivery():
    """Dashboard principal de Delivery"""
    import sys
    print("🔍 [DEBUG] view_delivery() chamado", file=sys.stderr)
    
    # Usar session_state para evitar re-criar inputs
    if 'dlv_filtros' not in st.session_state:
        st.session_state.dlv_filtros = {
            'data_ini': data_ini_padrao,
            'data_fim': date.today(),
            'loja_sel': 'Todas'
        }
    
    # Filtros inline - COM keys ÚNICAS por view
    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input('📅 Data Inicial', value=st.session_state.dlv_filtros['data_ini'], key='view_dlv_d_ini')
        st.session_state.dlv_filtros['data_ini'] = data_ini
    with col2:
        data_fim = st.date_input('📅 Data Final', value=st.session_state.dlv_filtros['data_fim'], key='view_dlv_d_fim')
        st.session_state.dlv_filtros['data_fim'] = data_fim
    with col3:
        with st.spinner('🏪 Carregando lojas...'):
            lojas_opt = carregar_lojas()
        loja_sel = st.selectbox('🏪 Loja', lojas_opt, index=lojas_opt.index(st.session_state.dlv_filtros['loja_sel']) if st.session_state.dlv_filtros['loja_sel'] in lojas_opt else 0, key='view_dlv_d_loja')
        st.session_state.dlv_filtros['loja_sel'] = loja_sel
        loja_nome = None if loja_sel == 'Todas' else loja_sel
    
    with st.spinner('🔍 Carregando dados de delivery...'):
        df = carregar_dados_delivery(data_ini, data_fim, loja_nome)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum delivery encontrado neste período.')
        return
    
    # ✅ NOVO: Filtrar DF para APENAS o período que o usuário filtrou
    # (df original tem 2 semanas extras para calcular semana anterior)
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
        
        # Calcular semanas - PASSAR data_ini E data_fim do filtro
        fat_atual, fat_anterior, variacao = calcular_semanas(df, data_ini, data_fim)
        
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
    import sys
    print("🔍 [DEBUG] view_categorias() chamado", file=sys.stderr)
    
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🏷️ Canal • Marca • Loja</h1>", unsafe_allow_html=True)
    
    # Usar session_state para evitar re-criar inputs
    if 'cat_filtros' not in st.session_state:
        st.session_state.cat_filtros = {
            'data_ini': data_ini_padrao,
            'data_fim': date.today(),
            'loja_sel': 'Todas'
        }
    
    # Filtros inline - COM keys ÚNICAS por view
    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input('📅 Data Inicial', value=st.session_state.cat_filtros['data_ini'], key='view_cat_d_ini')
        st.session_state.cat_filtros['data_ini'] = data_ini
    with col2:
        data_fim = st.date_input('📅 Data Final', value=st.session_state.cat_filtros['data_fim'], key='view_cat_d_fim')
        st.session_state.cat_filtros['data_fim'] = data_fim
    with col3:
        with st.spinner('🏪 Carregando lojas...'):
            lojas_opt = carregar_lojas()
        loja_sel = st.selectbox('🏪 Loja', lojas_opt, index=lojas_opt.index(st.session_state.cat_filtros['loja_sel']) if st.session_state.cat_filtros['loja_sel'] in lojas_opt else 0, key='view_cat_d_loja')
        st.session_state.cat_filtros['loja_sel'] = loja_sel
        loja_nome = None if loja_sel == 'Todas' else loja_sel
    
    with st.spinner('🔍 Carregando dados por categoria...'):
        df = carregar_dados_delivery(data_ini, data_fim, loja_nome)
    
    if df is None or df.empty:
        st.warning('📭 Nenhum delivery encontrado neste período.')
        return
    
    # ✅ NOVO: Filtrar DF para APENAS o período que o usuário filtrou
    df_filtrado = df[(df['Data'] >= pd.Timestamp(data_ini)) & (df['Data'] <= pd.Timestamp(data_fim))]
    
    # ════════════════════════════════════════════════════════════════
    # Se filtrou por loja específica, mostrar análise detalhada
    # ════════════════════════════════════════════════════════════════
    if loja_nome:
        st.markdown(f"### 🏪 Análise Detalhada: **{loja_nome}**")
        st.divider()
        
        # KPIs gerais da loja
        fat_loja = df_filtrado['Faturamento_Bruto'].sum()
        deliveries_loja = df_filtrado['venda_id'].nunique()
        canais_ativos = df_filtrado['CanalVenda'].nunique()
        marcas_ativas = df_filtrado['Marca'].nunique()
        
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
            df_canal_loja = df_filtrado.groupby('CanalVenda').agg({
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
            df_marca_loja = df_filtrado.groupby('Marca').agg({
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
            df_cruzado = df_filtrado.groupby(['CanalVenda', 'Marca'])['Faturamento_Bruto'].sum().reset_index()
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
            df_sunburst = df_filtrado.groupby(['CanalVenda', 'Marca'])['Faturamento_Bruto'].sum().reset_index()
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
            detalhe = df_filtrado.groupby(['CanalVenda', 'Marca']).agg({
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
        fat_geral = df_filtrado['Faturamento_Bruto'].sum()
        deliveries_geral = df_filtrado['venda_id'].nunique()
        canais_ativos = df_filtrado['CanalVenda'].nunique()
        marcas_ativas = df_filtrado['Marca'].nunique()
        lojas_ativas = df_filtrado['Loja_Nome'].nunique()
        
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
            df_canal_geral = df_filtrado.groupby('CanalVenda').agg({
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
            df_marca_geral = df_filtrado.groupby('Marca').agg({
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
            df_loja_canal = df_filtrado.groupby(['Loja_Nome', 'CanalVenda'])['Faturamento_Bruto'].sum().reset_index()
            
            fig = px.bar(df_loja_canal, x='Loja_Nome', y='Faturamento_Bruto',
                        color='CanalVenda', color_discrete_map=CORES_CANAL,
                        barmode='stack')
            fig.update_layout(**chart_layout(height=400, xaxis_title='Loja', yaxis_title='Faturamento (R$)',
                                             margin=dict(b=120)))
            st.plotly_chart(fig, use_container_width=True)
        
        with tab_tabela_geral:
            st.markdown('#### 📋 Detalhamento Geral')
            detalhe_geral = df_filtrado.groupby(['Loja_Nome', 'CanalVenda', 'Marca']).agg({
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
    """Renderiza o header principal"""
    gold = C['gold']
    st.markdown(f"<h1 style='color:{gold};'>🛵 Mamma Jamma Delivery</h1>", unsafe_allow_html=True)
    st.divider()

def view_main():
    """Função principal que renderiza header + tabs + views"""
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
