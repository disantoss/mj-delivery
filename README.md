# 🛵 Mamma Jamma Delivery · Passo-a-Passo Completo

> Uma segunda app focada em Delivery, mantendo a mesma vibe/estilo da app de garçons.

---

## 📦 O que você recebeu

```
✅ app_delivery.py                    ← App Streamlit de delivery
✅ RODAR_LOCALMENTE.md               ← Guia para testar no PC
✅ APP_DELIVERY_DOCS.md              ← Documentação da app
✅ DEPLOYMENT_GUIDE_DELIVERY.md      ← Guia de deploy no Azure
✅ SQL_SNIPPETS_CUSTOMIZATION.md     ← Queries SQL customizáveis
✅ Este README.md                    ← Você está aqui
```

---

## 🚀 Fluxo Recomendado

### Fase 1: Testar Localmente (AGORA)
```
1️⃣  Ler: RODAR_LOCALMENTE.md
2️⃣  Copiar arquivos para pasta local
3️⃣  Rodar: streamlit run app_delivery.py
4️⃣  Testar features (login, gráficos, dados)
5️⃣  Fazer ajustes conforme necessário
```

### Fase 2: Preparar para Azure
```
6️⃣  Ler: DEPLOYMENT_GUIDE_DELIVERY.md
7️⃣  Fazer commit no GitHub
8️⃣  Configurar Azure App Service
9️⃣  Configurar GitHub Actions
🔟  Deploy automático
```

### Fase 3: Em Produção
```
1️⃣1️⃣  Testar em produção
1️⃣2️⃣  Compartilhar link com gerentes
1️⃣3️⃣  Monitorar performance
```

---

## 📋 Checklist Rápido

### Antes de Rodar Localmente
- [ ] Python 3.9+ instalado
- [ ] Git instalado (opcional)
- [ ] Pasta criada para o projeto
- [ ] `app_delivery.py` copiado
- [ ] `config.yaml` copiado (segurança: não commite!)
- [ ] `requirements.txt` copiado

### Depois de Instalar Dependências
- [ ] `pip install -r requirements.txt` completado
- [ ] Sem erros na instalação

### Primeiro Run
- [ ] App abre em `http://localhost:8501`
- [ ] Tela de login aparece
- [ ] Login funciona com credenciais de gerente

### Testes das Features
- [ ] Filtros (data/loja) funcionam
- [ ] Tab 1: Gráfico de tendência temporal carrega
- [ ] Tab 2: Categorias populares aparecem
- [ ] Tab 3: Performance por loja exibe
- [ ] Tab 4: Horário & turno mostram dados
- [ ] Tab 5: Ranking de garçons funciona
- [ ] Tab 2 (Comparativo): Delivery vs Mesa carrega
- [ ] Botão Sair funciona

### Antes do Deploy
- [ ] Nenhum erro no terminal
- [ ] Performance é aceitável
- [ ] Todos os testes passaram
- [ ] `config.yaml` está no `.gitignore`
- [ ] Credenciais seguras no `.streamlit/secrets.toml`

---

## 📚 Documentação Detalhada

| Arquivo | Conteúdo | Quando Usar |
|---------|----------|------------|
| **RODAR_LOCALMENTE.md** | Setup local, teste, debug | Agora (fase 1) |
| **APP_DELIVERY_DOCS.md** | Features, design, métricas | Entender a app |
| **DEPLOYMENT_GUIDE_DELIVERY.md** | Deploy no Azure, GitHub Actions | Quando for mandar pro Azure |
| **SQL_SNIPPETS_CUSTOMIZATION.md** | Queries SQL prontas, customizações | Se quiser adicionar features |

---

## 🎯 Estrutura da App

```
app_delivery.py
├── Configuração Streamlit (tema, cores, CSS)
├── Autenticação (login via config.yaml)
├── Conexão Azure SQL (cache resource)
├── Funções auxiliares
│   ├── chart_layout()          ← Formata gráficos
│   ├── fmt_brl()               ← Formata valores R$
│   ├── carregar_dados_delivery() ← Query com filtros
│   └── filtros_globais()       ← UI filtros
├── View: Gerente (dashboard principal)
│   ├── Tab 1: Tendência temporal
│   ├── Tab 2: Categorias
│   ├── Tab 3: Performance por loja
│   ├── Tab 4: Horário & turno
│   └── Tab 5: Ranking de garçons
├── View: Comparativo (Delivery vs Mesa)
└── Roteador (if authenticated...)
```

---

## 🎨 Design & Vibe

✅ **Mantém 100% da identidade Mamma Jamma:**
- Paleta escura: preto (#0D0705), ouro (#C8973A), cream (#F5E6D3)
- Mesmos componentes Streamlit
- Mesmos gráficos Plotly
- Mesma autenticação

🆕 **Diferenciação de Delivery:**
- Cor destaque: laranja (#FF6B35) em vez de ouro
- Ícone 🛵 em vez de 🍽️
- Foco em análise de delivery (vs garçons)

---

## 📊 Dados & Métricas

### Fonte de Dados
- Banco Azure SQL (mesmo do app.py)
- Views: `vw_BI_fVendas`, `vw_BI_dFuncionario`, `vw_BI_dLoja`, `vw_BI_dMaterial`
- Filtro principal: `WHERE ModoVenda = 'Delivery'`

### Principais Métricas
| Métrica | Cálculo | Uso |
|---------|---------|-----|
| Faturamento Delivery | SUM(Faturamento_Bruto) | Total em R$ |
| Total de Deliveries | COUNT(DISTINCT venda_id) | Quantidade de pedidos |
| Ticket Médio | Faturamento ÷ Deliveries | Tamanho médio |
| Itens Vendidos | SUM(Qtd_Item) | Volume |
| % do Total | Delivery ÷ (Delivery + Mesa) × 100 | Participação |

---

## 🔐 Segurança

### ✅ Boas práticas aplicadas:
- Autenticação via bcrypt (hashed)
- Senhas não aparecem em logs
- `config.yaml` não é commitado (`.gitignore`)
- Secrets em `.streamlit/secrets.toml` ou Azure Key Vault
- Cache de dados (não re-executa query a cada refresh)
- SQL injection safe (SQLAlchemy parameteriza)

### 📋 Credenciais
- Use **gerente_geral** ou **subgerente** para acessar
- Garçom não tem acesso (validação de role)

---

## 🐛 Troubleshooting Rápido

| Erro | Solução |
|------|---------|
| "ModuleNotFoundError: No module named 'streamlit'" | `pip install streamlit` |
| "No such file: config.yaml" | Copiar arquivo para pasta do projeto |
| "Login failed for user" | Credenciais erradas ou acesso ao banco negado |
| "Connection refused" | VPN/Firewall bloqueando acesso ao servidor |
| "App fica carregando" | Query SQL lenta, adicionar filtro de data |
| "Gráficos aparecem em branco" | Sem dados ou erro na query, check logs |

Veja **RODAR_LOCALMENTE.md** para troubleshooting detalhado.

---

## 📈 Próximos Passos

### Curto Prazo (Esta semana)
1. Rodar localmente e testar
2. Fazer ajustes conforme necessário
3. Validar com Junior se features estão OK

### Médio Prazo (Próximas semanas)
1. Criar segundo App Service no Azure
2. Configurar GitHub Actions para deploy automático
3. Mandar pro Azure
4. Compartilhar link com gerentes

### Longo Prazo (Melhorias)
1. Adicionar Top Produtos Mais Vendidos
2. Integrar metas de delivery
3. Alertas inteligentes (queda de vendas, etc)
4. Exportar relatório em PDF
5. Dashboard de hora de pico por loja

---

## 💬 Resumo em Uma Frase

> Uma nova app Streamlit focada em delivery, com mesma vibe que a de garçons, pronta para rodar localmente e depois fazer deploy no Azure.

---

## ✅ Status

- [x] App criada (app_delivery.py)
- [x] Design mantido
- [x] Autenticação integrada
- [x] 5 tabs de análise
- [x] Comparativo Delivery vs Mesa
- [x] Documentação completa
- [x] Guias de local + Azure
- [ ] Testado localmente (você faz isso!)
- [ ] Pronto para produção (após testes)

---

## 📞 Próximas Ações

1. **Agora:** Ler `RODAR_LOCALMENTE.md`
2. **Depois:** Rodar no PC e testar
3. **Quando estiver OK:** Seguir `DEPLOYMENT_GUIDE_DELIVERY.md`
4. **Dúvidas em SQL:** Ver `SQL_SNIPPETS_CUSTOMIZATION.md`
5. **Entender a app:** Ler `APP_DELIVERY_DOCS.md`

---

**Boa sorte com os testes! 🚀 Qualquer dúvida, é só chamar!**
