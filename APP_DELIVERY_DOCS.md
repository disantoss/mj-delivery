# 🛵 Mamma Jamma Delivery · Documentação da Nova App

## 🎯 O que foi criado?

Um **dashboard de Delivery** com a mesma vibe/estilo do app de garçons, mas focado em **análise de vendas por delivery** vs mesa.

---

## ✨ Features Principais

### 1. **Dashboard Principal (Gerente Geral)**

Filtros globais:
- 📅 Data inicial e final
- 🏪 Seleção de loja (uma ou todas)

KPIs principais:
- 🛵 **Faturamento em Delivery** - Total de R$ em vendas delivery
- 📦 **Total de Deliveries** - Quantidade de pedidos
- 🎯 **Ticket Médio** - Faturamento ÷ Pedidos
- 📊 **Itens Vendidos** - Quantidade total de items

### 2. **Abas de Análise (5 tabs)**

#### **Tab 1: 📈 Tendência Temporal**
- Gráfico de área com faturamento diário (linha suave, preenchida)
- Gráfico de barras com quantidade de deliveries por dia
- Identifica picos de venda e padrões

#### **Tab 2: 🍕 Categorias Populares**
- Top 10 categorias por faturamento (gráfico horizontal)
- Tabela detalhada com:
  - Categoria
  - Faturamento total
  - Quantidade de itens
  - Quantidade de pedidos
- Mostra quais produtos/categorias impulsionam delivery

#### **Tab 3: 🏪 Performance por Loja**
- Gráfico de barras colorido por faturamento
- Gráfico de pizza com proporção (%)
- Tabela de resumo por loja
- Identifica lojas com melhor performance em delivery

#### **Tab 4: 📍 Horário & Turno**
- Faturamento por turno (Dia/Noite/Intercalado)
- Distribuição por hora do dia (gráfico de linha com marcadores)
- Revela horários de pico para delivery

#### **Tab 5: 👥 Ranking de Garçons**
- Top 15 garçons que mais vendem em delivery
- Gráfico com color coding por ticket médio
- Tabela com:
  - Garçom
  - Faturamento total
  - Quantidade de deliveries
  - Quantidade de itens
  - Ticket médio
- Gamificação: ver quem lidera em delivery

### 3. **Comparativo: Delivery vs Mesa (2ª Aba)**

Tab separada que compara:
- 🛵 **Faturamento Delivery** vs 🍽️ **Faturamento Mesa**
- Percentual de cada um no total
- Gráfico de pizza (proporção)
- Gráfico de linhas mostrando tendência diária de ambos
- Tabela com resumo estatístico:
  - Faturamento total
  - Qtd pedidos
  - Ticket médio
  - % do total

**Insights:**
- Saber se delivery é 10%, 30% ou 50% das vendas
- Identificar se delivery está crescendo ou diminuindo
- Comparar ticket médio (delivery costuma ser menor)

---

## 🎨 Design & Vibe

✅ **Mantém 100% da identidade visual:**
- Mesma paleta: preto (#0D0705), ouro (#C8973A), cream (#F5E6D3)
- Mesmos gráficos Plotly escuros
- Mesmos componentes: metrics, tabs, dataframes
- Mesma fonte Inter, mesma spacing

❌ **Diferenças (propositais):**
- Cor destaque em **#FF6B35** (laranja/delivery) em vez de ouro
- Ícones delivery 🛵 em vez de 🍽️
- Badge "Delivery Edition" (opcional)

---

## 🔌 Integração com Banco de Dados

### Views SQL Usadas:
```sql
vw_BI_fVendas        ← Tabela de vendas com ModoVenda
vw_BI_dFuncionario   ← Dados do funcionário (garçom)
vw_BI_dLoja          ← Dados da loja
vw_BI_dMaterial      ← Categorias de produtos
```

### Filtro Principal:
```sql
WHERE v.ModoVenda = 'Delivery'
```

Isso garante que **apenas vendas de delivery** apareçam.

---

## 🔐 Autenticação

Usa **exatamente o mesmo sistema** do app.py:
- Arquivo `config.yaml` com usuários bcrypt
- 3 perfis: `gerente_geral`, `subgerente`, `garcom`
- Mesma tela de login
- Gerente pode ver tudo, subgerente tem acesso limitado, garcom tem acesso negado

```yaml
# Exemplo de usuário que pode acessar
junior:
  email: junior@gruponoz.com.br
  name: Junior Silva
  password: $2b$12$0j9OGAJyF9TUFtRnAwDttuiMaYvX3MbVnn8h5nROgH29yJGnDvMiW
  role: gerente_geral  ← Pode acessar delivery
```

---

## 📊 Métricas Calculadas

| Métrica | Fórmula | Uso |
|---------|---------|-----|
| Faturamento | SUM(Faturamento_Bruto) | Total gerado |
| Qtd Deliveries | COUNT(DISTINCT venda_id) | Quantidade de pedidos |
| Ticket Médio | Faturamento ÷ Qtd Deliveries | Tamanho médio do pedido |
| Itens Vendidos | SUM(Qtd_Item) | Volume total |
| % do Total | Delivery ÷ (Delivery + Mesa) × 100 | Participação |

---

## 🚀 Como a App Funciona (Flow)

### 1. **Usuário entra**
```
Tela de Login → Valida username/password via config.yaml → Abre dashboard
```

### 2. **Gerente acessa Dashboard**
```
Seleciona data/loja → App conecta ao Azure SQL → 
Filtra apenas ModoVenda = 'Delivery' → 
Agrupa/calcula métricas → Exibe gráficos e tabelas
```

### 3. **Interatividade**
```
Usuário clica nas tabs → Dados já carregados em cache →
Gráficos Plotly atualizam → Pode exportar dados (dataframe)
```

### 4. **Cache (performance)**
```
@st.cache_data(ttl=300)  ← Dados em cache por 5 minutos
Primeira requisição: demora (query SQL)
Requisições seguintes: rápido (cache)
Após 5 min: re-executa query
```

---

## 🔧 Customizações Fáceis

Se precisar ajustar:

### Mudar cores:
```python
C = {
    'delivery': '#FF6B35',  ← Cor principal de delivery
    # ... outras cores
}
```

### Adicionar nova métrica:
```python
# Em view_delivery_gerente(), após os KPIs:
c5.metric('🆕 Nova Métrica', valor_calculado)
```

### Ajustar queries SQL:
```python
query_vendas = f"""
SELECT ...
WHERE v.ModoVenda = 'Delivery'
AND v.Data >= '{data_ini}'
AND ...
"""
```

### Mudar período de cache:
```python
@st.cache_data(ttl=600)  ← Agora cache de 10 minutos
```

---

## 📝 Estrutura do Código

```
app_delivery.py
├── Imports & Config
├── Page Config (title, layout)
├── Tema & Cores (C = {...})
├── CSS Styling (st.markdown com estilos)
├── Constantes (DATA_MIN, CORES_TURNO, etc)
├── Funções Auxiliares
│   ├── chart_layout()       ← Formato padrão dos gráficos
│   ├── load_credentials()   ← Lê config.yaml
│   ├── check_password()     ← Valida senha bcrypt
│   ├── login()              ← Tela de login
│   ├── header()             ← Cabeçalho com logo e logout
│   ├── get_db_connection()  ← Conexão Azure SQL (cache)
│   ├── fmt_brl()            ← Formata valores em R$
│   ├── carregar_dados_delivery()  ← Query principal com filtros
│   └── filtros_globais()    ← UI dos filtros
├── Views principais
│   ├── view_delivery_gerente()    ← Dashboard principal
│   └── view_delivery_vs_mesa()    ← Comparativo
└── Roteador (if authenticated...)  ← Lógica de entrada
```

---

## ⚙️ Requisitos Instalados

```txt
streamlit>=1.35.0      ← Framework web
pandas>=2.0.0          ← Manipulação de dados
plotly>=5.20.0         ← Gráficos interativos
pymssql>=2.2.0         ← Driver MSSQL
sqlalchemy>=2.0.0      ← ORM para SQL
bcrypt>=4.0.0          ← Hash de senhas
PyYAML>=6.0            ← Parser YAML (config.yaml)
```

---

## 🎯 Possíveis Melhorias Futuras

1. **Adicionar uma Tab de Produtos Específicos**
   - Top 10 produtos mais pedidos em delivery
   - Produtos que vendem mais em delivery vs mesa

2. **Análise de Endereço/Localização**
   - Se tiver dados de endereço, plotar heatmap com Folium
   - Ver regiões que mais pede delivery

3. **Histórico de Crescimento**
   - Gráfico de crescimento Week-over-Week
   - % de crescimento em relação à semana anterior

4. **Alertas Inteligentes**
   - Se faturamento cair 20%, alerta garçom
   - Se horário de pico muda, notifica

5. **Integração com Metas**
   - Colocar meta de delivery mensal
   - Ver se está no track ou não

6. **Export Avançado**
   - Botão para exportar relatório em PDF
   - Enviar por email automaticamente

---

## 📞 Suporte & Debugging

Se algo der errado no deploy:

```bash
# Ver logs em tempo real
az webapp log stream --resource-group seu-rg --name seu-app

# Ver erros específicos
az webapp log tail --resource-group seu-rg --name seu-app

# Restart da app
az webapp restart --resource-group seu-rg --name seu-app

# Check status
az webapp show --resource-group seu-rg --name seu-app --query "{state:state, defaultHostName:defaultHostName}"
```

---

## 🎉 Resumo

| Item | Status |
|------|--------|
| App criada | ✅ |
| Design mantido | ✅ |
| Autenticação integrada | ✅ |
| 5 tabs de análise | ✅ |
| Comparativo Delivery vs Mesa | ✅ |
| Cache de performance | ✅ |
| Pronto para produção | ✅ |
| Guia de deployment | ✅ |

---

**Próximo passo:** Seguir o [DEPLOYMENT_GUIDE_DELIVERY.md](./DEPLOYMENT_GUIDE_DELIVERY.md) para fazer deploy na Azure! 🚀
