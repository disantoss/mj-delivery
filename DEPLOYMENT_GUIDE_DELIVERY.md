# 🚀 Guia de Deployment · Mamma Jamma Delivery no Azure

## 📋 Índice
1. [Estrutura esperada](#estrutura-esperada)
2. [Preparação local](#preparação-local)
3. [Upload para GitHub](#upload-para-github)
4. [Configuração do Azure App Service](#configuração-do-azure-app-service)
5. [Deploy via GitHub Actions](#deploy-via-github-actions)
6. [Troubleshooting](#troubleshooting)

---

## 📁 Estrutura Esperada

Seu repositório GitHub deve ter **duas apps dentro da mesma pasta**:

```
seu-repo-mamma-jamma/
├── app.py                          ← App de garçons (existente)
├── app_delivery.py                 ← App de delivery (NOVO)
├── config.yaml                     ← Autenticação (compartilhado)
├── requirements.txt                ← Dependências (ajustado)
├── startup.sh                      ← Script de inicialização (MODIFICADO)
├── requirements_base.txt           ← (opcional, se dividir)
├── .gitignore
└── README.md
```

---

## 🔧 Preparação Local

### Passo 1: Atualizar requirements.txt

Como ambos os apps rodam no mesmo ambiente, certifique-se que o `requirements.txt` tem tudo:

```txt
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.20.0
bcrypt>=4.0.0
PyYAML>=6.0
pymssql>=2.2.0
sqlalchemy>=2.0.0
pyodbc>=5.0.0
Office365-REST-Python-Client>=2.5.0
openpyxl>=3.1.0
gunicorn>=20.1.0
waitress>=2.1.0
```

### Passo 2: Modificar startup.sh

O arquivo `startup.sh` precisa ser ajustado para rodar **apenas um app** por instância. 
Você tem **duas opções**:

**OPÇÃO A: Rodar app de garçons (recomendado, pois é o principal)**
```bash
#!/bin/bash
pip install -r requirements.txt --quiet
python -m streamlit run app.py \
  --server.port 8000 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --client.showErrorDetails true
```

**OPÇÃO B: Rodar app de delivery (se criar uma segunda instância no Azure)**
```bash
#!/bin/bash
pip install -r requirements.txt --quiet
python -m streamlit run app_delivery.py \
  --server.port 8000 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --client.showErrorDetails true
```

### Passo 3: Testar Localmente

Antes de fazer deploy, teste tudo localmente:

```bash
# Terminal 1 - App de Garçons
streamlit run app.py

# Terminal 2 - App de Delivery (em outra porta)
streamlit run app_delivery.py --server.port 8501
```

Acesse:
- App Garçons: `http://localhost:8500`
- App Delivery: `http://localhost:8501`

---

## 📤 Upload para GitHub

### 1. Criar repositório no GitHub (ou usar existente)

```bash
# Se criando novo
git init
git add .
git commit -m "Adicionar app_delivery.py + guia de deployment"
git branch -M main
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main

# Se já tem repositório
cd seu-repo-existente
git add app_delivery.py startup.sh requirements.txt README.md
git commit -m "Add: Delivery dashboard app"
git push origin main
```

### 2. Estrutura do .gitignore

Certifique-se que esses arquivos **NÃO** estão no git (segurança):

```
# .gitignore
__pycache__/
*.pyc
*.pyo
.streamlit/
.env
secrets.toml
config.yaml           ← IMPORTANTE: senhas em bcrypt
*.csv
.DS_Store
node_modules/
venv/
env/
```

⚠️ **IMPORTANTE**: Se `config.yaml` com senhas estiver no GitHub, é um risco de segurança. 
→ Use **Azure Key Vault** ou **secrets.toml** do Streamlit (vide seção abaixo).

---

## 🔷 Configuração do Azure App Service

### Opção 1: App Service Existente (Garçons) + Deployment da Nova App

Se já tem um App Service rodando `app.py`, você pode:

**A) Fazer deploy junto (mesmo container, mas seria confuso)**
```bash
# Isso trocaria entre um app e outro a cada deploy
git push origin main
```

**B) Criar um SEGUNDO App Service para Delivery (RECOMENDADO)**

1. **No Azure Portal:**
   - Vá em "App Services" → "+ Create"
   - Nome: `mamma-jamma-delivery` (ex: "mamma-jamma-delivery-prod")
   - Runtime: Python 3.11
   - Region: Mesmo que o banco de dados
   - Pricing Tier: B1 ou B2 (conforme orçamento)
   - Clique em "Review + Create"

2. **Configure as Environment Variables:**
   - Settings → Configuration → Application settings
   - Adicione:
     ```
     db_server=seu-servidor.database.windows.net
     db_database=seu-database
     db_username=seu-usuario
     db_password=sua-senha-segura
     ```

3. **Modifique startup.sh para Delivery:**
   ```bash
   #!/bin/bash
   pip install -r requirements.txt --quiet
   python -m streamlit run app_delivery.py \
     --server.port 8000 \
     --server.address 0.0.0.0 \
     --server.headless true
   ```

### Opção 2: Usar um ÚNICO App Service com Múltiplas Apps (Advanced)

Se quiser economizar em custos, pode rodar as duas apps no mesmo container usando **nginx** como reverse proxy. Mas é mais complexo.

---

## 🔄 Deploy via GitHub Actions (Automatizado)

### 1. Criar arquivo `.github/workflows/deploy.yml`

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests (opcional)
      run: |
        # Aqui você pode adicionar testes se quiser
        echo "Tests would go here"
    
    - name: Deploy to Azure App Service
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'mamma-jamma-delivery-prod'  # ← ALTERE PARA SEU APP
        publish-profile: ${{ secrets.AZURE_PUBLISH_PROFILE }}
        package: .

    - name: Post deployment message
      run: echo "✅ Deploy realizado com sucesso!"
```

### 2. Obter o Publish Profile

No Azure Portal:
1. Vá para seu App Service (delivery)
2. Clique em "Download publish profile" (ícone no canto superior)
3. Copie o conteúdo do arquivo `.PublishSettings`

### 3. Adicionar ao GitHub Secrets

1. No GitHub, vá para: `Settings` → `Secrets and variables` → `Actions`
2. Clique em "New repository secret"
3. Nome: `AZURE_PUBLISH_PROFILE`
4. Valor: Cole o conteúdo do arquivo `.PublishSettings`
5. Clique em "Add secret"

### 4. Fazer Push para Disparar Deploy

```bash
git add .github/workflows/deploy.yml
git commit -m "Add: GitHub Actions workflow para deploy automatizado"
git push origin main
```

Agora, a cada `git push` para `main`, o deploy acontece automaticamente! 🚀

---

## 🔐 Gerenciar Secrets de Forma Segura

### Opção 1: Azure Key Vault (Recomendado para Produção)

1. **Criar Key Vault no Azure:**
   ```bash
   az keyvault create \
     --resource-group seu-resource-group \
     --name mamma-jamma-kv
   ```

2. **Adicionar secrets:**
   ```bash
   az keyvault secret set \
     --vault-name mamma-jamma-kv \
     --name "db-server" \
     --value "seu-servidor.database.windows.net"
   
   az keyvault secret set \
     --vault-name mamma-jamma-kv \
     --name "db-password" \
     --value "sua-senha-super-segura"
   ```

3. **No App Service, referenciar:**
   - Configuration → New application setting
   - Nome: `db_server`
   - Valor: `@Microsoft.KeyVault(SecretUri=https://mamma-jamma-kv.vault.azure.net/secrets/db-server/)`

### Opção 2: .streamlit/secrets.toml (Mais Simples)

1. Crie `.streamlit/secrets.toml` **localmente** (NÃO commite):
   ```toml
   db_server = "seu-servidor.database.windows.net"
   db_database = "seu-database"
   db_username = "seu-usuario"
   db_password = "sua-senha"
   ```

2. No App Service, upload manualmente via Azure Portal ou:
   ```bash
   az webapp config appsettings set \
     --resource-group seu-resource-group \
     --name mamma-jamma-delivery-prod \
     --settings db_server="seu-servidor.database.windows.net" \
     db_password="sua-senha"
   ```

---

## 📊 Verificar Deploy

Após o push:

1. **GitHub:** Vá em "Actions" → veja o workflow rodando
2. **Azure Portal:** Vá no App Service → "Deployment Center" → veja o histórico
3. **Logs ao vivo:**
   ```bash
   az webapp log tail \
     --resource-group seu-resource-group \
     --name mamma-jamma-delivery-prod
   ```

4. **Acessar a app:**
   ```
   https://mamma-jamma-delivery-prod.azurewebsites.net
   ```

---

## 🐛 Troubleshooting

### ❌ Erro: "Module not found"
```
FileNotFoundError: [Errno 2] No such file or directory: 'app_delivery.py'
```
**Solução:** Certifique-se que o arquivo está no repositório:
```bash
git add app_delivery.py
git commit -m "Add app_delivery.py"
git push
```

### ❌ Erro: "Connection refused" (banco de dados)
```
pymssql._mssql.MSSQLDatabaseException: Login failed for user
```
**Solução:** 
- Verificar credenciais em Configuration → Application settings
- Testar conexão localmente
- Verificar firewall do Azure SQL (permitir IP do App Service)

### ❌ Erro: "Streamlit command not found"
```
bash: streamlit: command not found
```
**Solução:** Verificar se `startup.sh` tem permissão de execução:
```bash
chmod +x startup.sh
git add startup.sh
git push
```

### ❌ App fica em branco ou demora muito para carregar
**Solução:**
- Aumentar memória: App Service Plan → Scale up para B2
- Verificar logs: `az webapp log tail`
- Limpar cache: Azure Portal → App Service → Restart

### ❌ Erro 502 Bad Gateway
**Solução:**
- Restart do App Service
- Verificar se `startup.sh` está rodando corretamente
- Ver logs: `az webapp log stream`

---

## 📈 Próximos Passos

1. **Monitoramento:**
   - Application Insights (Azure Portal → Add)
   - Alertas de performance

2. **Performance:**
   - Cache de dados (Redis)
   - Otimizar queries SQL

3. **Segurança:**
   - HTTPS automático (já incluso)
   - Rate limiting
   - Autenticação multi-fator

4. **Manutenção:**
   - Backup automático do banco
   - Logs centralizados
   - Plano de disaster recovery

---

## 🎯 Resumo Final

| Etapa | Comando | Status |
|-------|---------|--------|
| Preparar localmente | `git add . && git commit && git push` | ✅ |
| Criar App Service Delivery | Azure Portal | ✅ |
| Configurar secrets | `az keyvault` ou Portal | ✅ |
| GitHub Actions | `.github/workflows/deploy.yml` + Secret | ✅ |
| Deploy | `git push origin main` | ✅ |
| Testar em produção | Acessar URL do App Service | ✅ |

---

**Precisa de algo mais específico? Posso ajudar com comandos exatos ou troubleshooting!** 🚀
