# 🖥️ Rodar app_delivery.py Localmente

Guia rápido para testar no seu PC antes de mandar pro Azure.

---

## 📋 Pré-requisitos

- Python 3.9+ instalado
- Git instalado (opcional, mas recomendado)
- Acesso ao banco Azure SQL (conexão via VPN ou liberada)
- `config.yaml` com suas credenciais de usuário

---

## 🚀 Passo 1: Preparar a Pasta Local

```bash
# Crie uma pasta para o projeto
mkdir mamma-jamma-delivery
cd mamma-jamma-delivery

# Se tiver git, inicie um repo
git init
```

---

## 📥 Passo 2: Copiar Arquivos Necessários

Copie para essa pasta:
```
mamma-jamma-delivery/
├── app_delivery.py          ← O app novo (você já tem)
├── config.yaml              ← Autenticação (copie do seu projeto atual)
├── requirements.txt         ← Dependências (copie do seu projeto atual)
└── .gitignore              ← Ignorar arquivos sensíveis
```

**Conteúdo do `.gitignore`:**
```
__pycache__/
*.pyc
.streamlit/
.env
secrets.toml
config.yaml
*.csv
.DS_Store
venv/
env/
```

---

## 🔧 Passo 3: Criar Ambiente Virtual (Python)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Você deve ver `(venv)` no terminal.

---

## 📦 Passo 4: Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Vai demora um pouco (primeira vez).

---

## 🗄️ Passo 5: Configurar Acesso ao Banco (Importante!)

### Opção A: Via `secrets.toml` do Streamlit (RECOMENDADO)

1. Crie a pasta `.streamlit`:
```bash
mkdir .streamlit
```

2. Crie o arquivo `.streamlit/secrets.toml`:
```toml
db_server = "seu-servidor-azure.database.windows.net"
db_database = "seu-database"
db_username = "seu-usuario"
db_password = "sua-senha-super-segura"
```

3. **NÃO commite** esse arquivo (já está no .gitignore)

### Opção B: Direto no código

Se preferir, edite no `app_delivery.py`:

```python
# Procure por get_db_connection() e substitua:
@st.cache_resource
def get_db_connection():
    if not DB_AVAILABLE:
        return None
    try:
        # ← Coloque seus dados aqui
        server = "seu-servidor-azure.database.windows.net"
        database = "seu-database"
        username = "seu-usuario"
        password = "sua-senha"
        
        connection_string = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        engine = create_engine(connection_string, echo=False)
        return engine
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return None
```

---

## ▶️ Passo 6: Rodar a App Localmente

```bash
streamlit run app_delivery.py
```

Deve abrir automaticamente no navegador: `http://localhost:8501`

Se não abrir, acesse manualmente.

---

## 🔐 Passo 7: Fazer Login

Na tela de login, use credenciais do seu `config.yaml`:

```yaml
# Exemplo (do seu config.yaml atual)
junior:
  email: junior@gruponoz.com.br
  name: Junior Silva
  password: $2b$12$...
  role: gerente_geral
```

**Username:** `junior`  
**Senha:** Aquela que você usa no app atual

---

## ✅ Passo 8: Testar as Features

### ✔️ Testes básicos:

- [ ] Login funciona
- [ ] Carrega dados sem erro
- [ ] Filtros funcionam (data, loja)
- [ ] Gráficos aparecem
- [ ] Abas (tabs) trocam
- [ ] Tabelas são exibidas
- [ ] Cores estão boas
- [ ] Performance é aceitável (não trava)

### 🐛 Se algo der errado:

```bash
# Terminal vai mostrar o erro
# Exemplo:
# FileNotFoundError: No such file or directory: 'config.yaml'
# → Significa que config.yaml não está na mesma pasta do app_delivery.py

# Outro erro comum:
# pymssql._mssql.MSSQLDatabaseException: Login failed
# → Significa que credenciais estão erradas ou servidor não está acessível
```

---

## 🔧 Debugar Conexão ao Banco

Se a app abre mas não carrega dados:

### 1. Testar conexão localmente

```python
# Crie um arquivo test_connection.py:

from sqlalchemy import create_engine

server = "seu-servidor.database.windows.net"
database = "seu-database"
username = "seu-usuario"
password = "sua-senha"

try:
    connection_string = f"mssql+pymssql://{username}:{password}@{server}/{database}"
    engine = create_engine(connection_string, echo=False)
    
    # Teste a conexão
    with engine.connect() as connection:
        result = connection.execute("SELECT 1")
        print("✅ Conexão OK!")
except Exception as e:
    print(f"❌ Erro: {e}")
```

Rode:
```bash
python test_connection.py
```

### 2. Verificar se as views existem

```sql
-- Rode no SQL Server Management Studio
SELECT * FROM vw_BI_fVendas WHERE ModoVenda = 'Delivery' LIMIT 10;
SELECT * FROM vw_BI_dFuncionario LIMIT 5;
SELECT * FROM vw_BI_dLoja LIMIT 5;
SELECT * FROM vw_BI_dMaterial LIMIT 5;
```

Se não retornar nada, significa que:
- Views não existem ainda
- Database está vazio
- Credenciais estão erradas

---

## 🛑 Parar a App

No terminal, pressione: **CTRL + C**

---

## 📝 Checklist Antes de Fazer Deploy

- [ ] App roda sem erros localmente
- [ ] Login funciona
- [ ] Dados carregam (pelo menos alguns)
- [ ] Gráficos aparecem
- [ ] Você testou as 5 abas
- [ ] Comparativo Delivery vs Mesa funciona
- [ ] Sem erros no terminal
- [ ] Performance é aceitável
- [ ] Botão "Sair" funciona

---

## 🔄 Se Precisar Fazer Mudanças

```bash
# 1. Edite o arquivo app_delivery.py com seu editor preferido (VS Code, etc)
# 2. Salve
# 3. Reload automático no navegador (Streamlit recarrega sozinho)
# 4. Se não recarregar, pressione R no navegador
```

---

## 📊 Exemplo de Saída Esperada

Quando funcionar corretamente, você deve ver:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://seu-ip:8501

  Press CTRL+C to quit
```

E no navegador:

```
🛵 Mamma Jamma Delivery

👤 Usuário: [campo de input]
🔐 Senha: [campo de input]
[Botão Entrar]
```

---

## 💡 Dicas

1. **Deixe o terminal aberto** enquanto testa
2. **Erros aparecem no terminal**, não só no navegador
3. **Limpar cache do navegador** se algo parecer "congelado"
4. **Usar incognito/private** para limpar session (logout + login)
5. **Rodar em outra porta** se quiser testar os dois apps ao mesmo tempo:
   ```bash
   streamlit run app.py --server.port 8500
   streamlit run app_delivery.py --server.port 8501
   ```

---

## ❓ Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
```bash
# Solução:
pip install streamlit
```

### Erro: "No such file: config.yaml"
```bash
# Solução: config.yaml precisa estar no mesmo diretório
# Ou mude o caminho no código:
with open('../seu-outro-projeto/config.yaml') as f:
    ...
```

### Erro: "Connection refused" ao banco
```bash
# Solução:
# 1. Testar se consegue pingar o servidor:
ping seu-servidor.database.windows.net

# 2. Verificar firewall do Windows
# 3. Verificar VPN (se precisa)
# 4. Testar credenciais no SQL Server Management Studio
```

### App fica carregando para sempre
```bash
# Solução:
# 1. Verificar se query SQL está muito pesada
# 2. Adicionar filtro de data mais restritivo
# 3. Aumentar timeout:
engine = create_engine(connection_string, connect_args={"timeout": 30})
```

---

## ✅ Pronto!

Se passou por todos os checklist acima, está pronto para mandar pro Azure! 🚀

**Próximo passo:** [DEPLOYMENT_GUIDE_DELIVERY.md](./DEPLOYMENT_GUIDE_DELIVERY.md)
