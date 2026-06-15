# 🔍 SQL Snippets · Customizações para app_delivery.py

Este arquivo contém queries SQL prontas para ajustar o app caso você queira mudar as análises ou adicionar novas métricas.

---

## 📋 Queries Base (Já usadas no app)

### Query Principal de Delivery

```sql
-- Esta é a query que o app usa (com joins de dimensão)
SELECT 
    v.Data,
    v.loja_id,
    v.venda_id,
    v.SK_Funcionario,
    v.Produto_ID,
    v.SK_Material,
    v.Faturamento_Bruto,
    v.Qtd_Item,
    v.Preco_Unitario,
    v.Turno_Venda,
    v.ModoVenda,
    v.qtd_pessoas,
    f.Funcionario_Nome,
    f.Funcionario_Funcao,
    l.Loja_Nome,
    m.Categoria_Visao3,
    m.descricao
FROM vw_BI_fVendas v
LEFT JOIN vw_BI_dFuncionario f ON v.SK_Funcionario = f.SK_Funcionario
LEFT JOIN vw_BI_dLoja l ON v.loja_id = l.Loja_ID
LEFT JOIN vw_BI_dMaterial m ON v.SK_Material = m.SK_Material
WHERE v.ModoVenda = 'Delivery'
AND v.Data >= '2025-01-01'
AND v.Data <= '2025-12-31'
;
```

---

## 🆕 Novas Queries (Para adicionar features)

### 1. Top Produtos Mais Vendidos em Delivery

```sql
SELECT TOP 20
    m.descricao AS Produto,
    m.Categoria_Visao3 AS Categoria,
    COUNT(v.venda_id) AS Qtd_Pedidos,
    SUM(v.Qtd_Item) AS Total_Itens,
    SUM(v.Faturamento_Bruto) AS Faturamento_Total,
    AVG(v.Preco_Unitario) AS Preco_Medio
FROM vw_BI_fVendas v
LEFT JOIN vw_BI_dMaterial m ON v.SK_Material = m.SK_Material
WHERE v.ModoVenda = 'Delivery'
    AND v.Data >= '2025-01-01'
    AND v.Data <= '2025-12-31'
GROUP BY m.descricao, m.Categoria_Visao3
ORDER BY Faturamento_Total DESC
;
```

**Uso no app:**
```python
@st.cache_data(ttl=300)
def top_produtos_delivery(data_ini, data_fim):
    engine = get_db_connection()
    query = f"""
    SELECT TOP 20
        descricao, Categoria_Visao3, Qtd_Pedidos, Total_Itens, Faturamento_Total
    FROM ... WHERE Data >= '{data_ini}' AND Data <= '{data_fim}'
    ORDER BY Faturamento_Total DESC
    """
    return pd.read_sql_query(query, engine)

# Em uma nova tab:
produtos = top_produtos_delivery(data_ini, data_fim)
fig = px.bar(produtos, x='descricao', y='Faturamento_Total', color='Categoria_Visao3')
st.plotly_chart(fig, use_container_width=True)
```

### 2. Performance Delivery vs Mesa por Dia (Comparativo Diário)

```sql
SELECT 
    v.Data,
    v.ModoVenda,
    COUNT(DISTINCT v.venda_id) AS Qtd_Vendas,
    SUM(v.Faturamento_Bruto) AS Faturamento,
    AVG(v.Faturamento_Bruto) AS Ticket_Medio
FROM vw_BI_fVendas v
WHERE v.Data >= '2025-01-01'
    AND v.Data <= '2025-12-31'
    AND v.ModoVenda IN ('Delivery', 'Mesa')
GROUP BY v.Data, v.ModoVenda
ORDER BY v.Data DESC
;
```

**Uso no app:**
```python
df_comparativo = pd.read_sql_query(query, engine)

# Dividir em Delivery e Mesa
df_dlv = df_comparativo[df_comparativo['ModoVenda'] == 'Delivery']
df_mesa = df_comparativo[df_comparativo['ModoVenda'] == 'Mesa']

# Gráfico de comparação
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_dlv['Data'], y=df_dlv['Faturamento'],
    name='Delivery', mode='lines', line=dict(color=C['delivery'])
))
fig.add_trace(go.Scatter(
    x=df_mesa['Data'], y=df_mesa['Faturamento'],
    name='Mesa', mode='lines', line=dict(color=C['muted'])
))
st.plotly_chart(fig, use_container_width=True)
```

### 3. Análise por Dia da Semana (Qual dia vende mais delivery?)

```sql
SELECT 
    DATENAME(WEEKDAY, v.Data) AS Dia_Semana,
    DATEPART(WEEKDAY, v.Data) AS Dia_Ordem,  -- 1=Dom, 7=Sab
    COUNT(DISTINCT v.venda_id) AS Qtd_Deliveries,
    SUM(v.Faturamento_Bruto) AS Faturamento,
    AVG(v.Faturamento_Bruto) AS Ticket_Medio
FROM vw_BI_fVendas v
WHERE v.ModoVenda = 'Delivery'
    AND v.Data >= '2025-01-01'
    AND v.Data <= '2025-12-31'
GROUP BY DATENAME(WEEKDAY, v.Data), DATEPART(WEEKDAY, v.Data)
ORDER BY Dia_Ordem
;
```

**Uso no app:**
```python
# Adicionar uma nova tab
with st.tabs([..., '📅 Por Dia da Semana']):
    df_dia = pd.read_sql_query(query, engine)
    fig = px.bar(df_dia, x='Dia_Semana', y='Faturamento', 
                 color='Qtd_Deliveries', color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)
```

### 4. Delivery por Faixa de Horário (Picos de Horário)

```sql
SELECT 
    DATEPART(HOUR, v.Data) AS Hora,
    COUNT(DISTINCT v.venda_id) AS Qtd_Deliveries,
    SUM(v.Faturamento_Bruto) AS Faturamento,
    AVG(v.Faturamento_Bruto) AS Ticket_Medio,
    CASE 
        WHEN DATEPART(HOUR, v.Data) BETWEEN 6 AND 11 THEN 'Manhã'
        WHEN DATEPART(HOUR, v.Data) BETWEEN 12 AND 17 THEN 'Almoço'
        WHEN DATEPART(HOUR, v.Data) BETWEEN 18 AND 22 THEN 'Noite'
        ELSE 'Madrugada'
    END AS Periodo
FROM vw_BI_fVendas v
WHERE v.ModoVenda = 'Delivery'
    AND v.Data >= '2025-01-01'
    AND v.Data <= '2025-12-31'
GROUP BY DATEPART(HOUR, v.Data)
ORDER BY Hora
;
```

### 5. Garçons com Maior Crescimento em Delivery (Week over Week)

```sql
WITH Weekly AS (
    SELECT 
        f.Funcionario_Nome,
        DATEPART(YEAR, v.Data) AS Ano,
        DATEPART(WEEK, v.Data) AS Semana,
        SUM(v.Faturamento_Bruto) AS Faturamento
    FROM vw_BI_fVendas v
    LEFT JOIN vw_BI_dFuncionario f ON v.SK_Funcionario = f.SK_Funcionario
    WHERE v.ModoVenda = 'Delivery'
        AND v.Data >= DATEADD(WEEK, -4, GETDATE())
    GROUP BY f.Funcionario_Nome, DATEPART(YEAR, v.Data), DATEPART(WEEK, v.Data)
)
SELECT TOP 10
    Funcionario_Nome,
    Faturamento,
    LAG(Faturamento) OVER (PARTITION BY Funcionario_Nome ORDER BY Ano, Semana) AS Faturamento_Semana_Anterior,
    ROUND(
        ((Faturamento - LAG(Faturamento) OVER (PARTITION BY Funcionario_Nome ORDER BY Ano, Semana)) 
        / LAG(Faturamento) OVER (PARTITION BY Funcionario_Nome ORDER BY Ano, Semana) * 100),
        2
    ) AS Crescimento_Pct
FROM Weekly
WHERE LAG(Faturamento) OVER (PARTITION BY Funcionario_Nome ORDER BY Ano, Semana) IS NOT NULL
ORDER BY Crescimento_Pct DESC
;
```

### 6. Categorias Delivery vs Mesa (Qual categoria mais faz delivery?)

```sql
SELECT 
    m.Categoria_Visao3,
    v.ModoVenda,
    COUNT(DISTINCT v.venda_id) AS Qtd_Vendas,
    SUM(v.Faturamento_Bruto) AS Faturamento,
    SUM(v.Qtd_Item) AS Total_Itens
FROM vw_BI_fVendas v
LEFT JOIN vw_BI_dMaterial m ON v.SK_Material = m.SK_Material
WHERE v.Data >= '2025-01-01'
    AND v.Data <= '2025-12-31'
    AND v.ModoVenda IN ('Delivery', 'Mesa')
    AND m.Categoria_Visao3 IS NOT NULL
GROUP BY m.Categoria_Visao3, v.ModoVenda
ORDER BY Categoria_Visao3, ModoVenda
;
```

**Uso no app:** Criar um gráfico de dispersão ou heatmap mostrando categorias que mais vendem em delivery

---

## 🔧 Como Integrar uma Nova Query ao app_delivery.py

### Passo 1: Adicionar a função de carregamento

```python
@st.cache_data(ttl=300)
def carregar_dados_customizados(data_ini, data_fim, loja_id=None):
    """Carrega dados customizados com sua query"""
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        query = f"""
        -- AQUI VEM SUA QUERY SQL
        SELECT ...
        WHERE Data >= '{data_ini}'
        AND Data <= '{data_fim}'
        """
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return None
```

### Passo 2: Usar em uma nova tab

```python
# Dentro de view_delivery_gerente()
tab_novo, = st.tabs(['🆕 Sua Nova Análise'])

with tab_novo:
    df_custom = carregar_dados_customizados(data_ini, data_fim, loja_id)
    
    if df_custom is not None:
        st.markdown('#### 🆕 Título da Análise')
        
        # Criar seu gráfico
        fig = px.bar(df_custom, x='coluna_x', y='coluna_y', 
                     color_discrete_sequence=[C['delivery']])
        fig.update_layout(**chart_layout(height=400))
        st.plotly_chart(fig, use_container_width=True)
        
        # Ou uma tabela
        st.dataframe(df_custom, use_container_width=True, hide_index=True)
```

---

## 📊 Exemplos de Métricas Calculadas em Python

Se precisar fazer cálculos que não estão na query:

```python
# Taxa de conversão (quantas pessoas pediram delivery / total)
def taxa_conversao_delivery(df_vendas):
    total_vendas = df_vendas.shape[0]
    vendas_delivery = df_vendas[df_vendas['ModoVenda'] == 'Delivery'].shape[0]
    return (vendas_delivery / total_vendas * 100) if total_vendas > 0 else 0

# Variação em relação ao período anterior
def comparar_periodos(df_atual, df_anterior, coluna='Faturamento_Bruto'):
    fat_atual = df_atual[coluna].sum()
    fat_anterior = df_anterior[coluna].sum()
    variacao = ((fat_atual - fat_anterior) / fat_anterior * 100) if fat_anterior > 0 else 0
    return fat_atual, fat_anterior, variacao

# Ranking e posição
def adicionar_ranking(df, coluna_valor):
    df['Ranking'] = df[coluna_valor].rank(ascending=False, method='dense')
    return df

# Exemplos de uso:
df['Taxa_Conversao'] = taxa_conversao_delivery(df)
df_ranking = adicionar_ranking(df_garcom, 'Faturamento')
```

---

## 🛠️ Troubleshooting de Queries

### ❌ Erro: "Invalid column name"
Verifique se a coluna existe na view:
```sql
-- Verificar colunas disponíveis
SELECT TOP 1 * FROM vw_BI_fVendas;
SELECT TOP 1 * FROM vw_BI_dFuncionario;
SELECT TOP 1 * FROM vw_BI_dLoja;
SELECT TOP 1 * FROM vw_BI_dMaterial;
```

### ❌ Erro: "Null value in aggregate function"
Adicione `WHERE` ou `ISNULL()`:
```sql
SELECT 
    ISNULL(Categoria_Visao3, 'Sem Categoria') AS Categoria,
    SUM(Faturamento_Bruto) AS Total
FROM vw_BI_fVendas
WHERE Categoria_Visao3 IS NOT NULL
GROUP BY Categoria_Visao3
```

### ❌ Lento? Adicione filtros:
```sql
WHERE v.Data >= '2025-01-01'  -- Filtra por ano
AND v.loja_id = 1              -- Filtra por loja
AND v.ModoVenda = 'Delivery'   -- Filtra por tipo
```

### ❌ Muitos resultados? Use TOP:
```sql
SELECT TOP 100 *  -- Limita a 100 linhas
FROM vw_BI_fVendas
```

---

## 📈 Exemplo Completo: Adicionar Tab de "Produtos Mais Vendidos"

**1. Adicione a função de carregamento:**
```python
@st.cache_data(ttl=300)
def carregar_top_produtos(data_ini, data_fim, loja_id=None, limite=20):
    engine = get_db_connection()
    if engine is None:
        return None
    
    try:
        query = f"""
        SELECT TOP {limite}
            m.descricao AS Produto,
            m.Categoria_Visao3 AS Categoria,
            COUNT(DISTINCT v.venda_id) AS Qtd_Pedidos,
            SUM(v.Qtd_Item) AS Total_Itens,
            SUM(v.Faturamento_Bruto) AS Faturamento
        FROM vw_BI_fVendas v
        LEFT JOIN vw_BI_dMaterial m ON v.SK_Material = m.SK_Material
        WHERE v.ModoVenda = 'Delivery'
            AND v.Data >= '{data_ini}'
            AND v.Data <= '{data_fim}'
            {f"AND v.loja_id = {loja_id}" if loja_id else ""}
        GROUP BY m.descricao, m.Categoria_Visao3
        ORDER BY Faturamento DESC
        """
        return pd.read_sql_query(query, engine)
    except Exception as e:
        st.error(f"Erro: {e}")
        return None
```

**2. Adicione em view_delivery_gerente():**
```python
# Dentro de st.tabs([...]):
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    '📈 Tendência Temporal',
    '🍕 Categorias Populares',
    '🏪 Performance por Loja',
    '📍 Horário & Turno',
    '👥 Ranking de Garçons',
    '🆕 Top Produtos'  # ← NOVA TAB
])

with tab6:
    st.markdown('#### 🆕 Produtos Mais Vendidos em Delivery')
    df_produtos = carregar_top_produtos(data_ini, data_fim, loja_id)
    
    if df_produtos is not None:
        fig = px.bar(df_produtos, x='Produto', y='Faturamento',
                     color='Categoria', hover_data=['Qtd_Pedidos', 'Total_Itens'],
                     text=df_produtos['Faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside')
        fig.update_layout(**chart_layout(height=450, xaxis_title='', yaxis_title='Faturamento (R$)',
                                        margin=dict(b=120)))
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_produtos, use_container_width=True, hide_index=True)
```

---

## 🎯 Resumo

| Necessidade | Arquivo | Função |
|---|---|---|
| Adicionar nova métrica | `app_delivery.py` | `carregar_dados_xxx()` |
| Novo gráfico | `app_delivery.py` | `px.chart()` + `st.plotly_chart()` |
| Modificar query base | Acima, queries | Editar a query SQL |
| Cache de performance | `@st.cache_data(ttl=300)` | Acelerar carregamento |
| Tratamento de erros | try/except + `st.error()` | Mostrar mensagem útil |

---

**Precisa de algo específico? Posso criar queries customizadas!** 🚀
