"""
OAuth Google Manual para Streamlit - MJ Delivery
Login direto com Google, valida apenas @gruponoz.com.br
SEM usar streamlit-oauth (biblioteca bugada)
SEM st.set_page_config() aqui (centralizado em main.py!)
⚠️ CREDENCIAIS VÃO VIA VARIÁVEIS DE AMBIENTE (.env)
"""

import streamlit as st
import requests
import json
import base64
import os
from urllib.parse import urlencode, parse_qs
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES GOOGLE OAUTH - VIA VARIÁVEIS DE AMBIENTE
# ════════════════════════════════════════════════════════════════════════════

# ⚠️ IMPORTANTE: Configure via .env ou variáveis de ambiente!
# NÃO coloque credenciais aqui!
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError(
        "❌ GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET não configurados!\n"
        "Configure via arquivo .env ou variáveis de ambiente do sistema."
    )

# Determinar redirect URI baseado no ambiente
if "WEBSITE_HOSTNAME" in os.environ:
    # Azure App Service
    REDIRECT_URI = f"https://{os.environ.get('WEBSITE_HOSTNAME')}"
else:
    # Localhost
    REDIRECT_URI = "http://localhost:8501"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

SCOPES = ["openid", "email", "profile"]

# ════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE EMAIL
# ════════════════════════════════════════════════════════════════════════════

def validar_email_empresa(email):
    """Valida se email é @gruponoz.com.br"""
    if email and email.endswith("@gruponoz.com.br"):
        return True
    return False

# ════════════════════════════════════════════════════════════════════════════
# DECODIFICAR JWT (para ID Token)
# ════════════════════════════════════════════════════════════════════════════

def decodificar_jwt(token):
    """Decodifica um token JWT sem validar assinatura (ID Token do Google)"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        # Decodificar o payload (segunda parte)
        payload = parts[1]
        # Adicionar padding se necessário
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        st.error(f"❌ Erro ao decodificar token: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════
# OBTER INFORMAÇÕES DO USUÁRIO
# ════════════════════════════════════════════════════════════════════════════

def obter_info_usuario(access_token):
    """Busca informações do usuário no Google"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"❌ Erro ao buscar informações do usuário: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════
# FLUXO OAUTH GOOGLE
# ════════════════════════════════════════════════════════════════════════════

def gerar_url_autorizacao():
    """Gera a URL para redirecionar o usuário ao Google"""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
    }
    
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return url

def trocar_codigo_por_token(codigo_autorizacao):
    """Troca o código de autorização por tokens"""
    try:
        data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': codigo_autorizacao,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        
        tokens = response.json()
        return tokens
    except requests.RequestException as e:
        st.error(f"❌ Erro ao trocar código por token: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════
# LOGOUT
# ════════════════════════════════════════════════════════════════════════════

def logout():
    """Remove sessão do usuário"""
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('oauth') or k in ['user_info', 'token', 'access_token']]
    for key in keys_to_remove:
        del st.session_state[key]
    st.success("✅ Logout realizado com sucesso!")
    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# TELA DE LOGIN
# ════════════════════════════════════════════════════════════════════════════

def main_login():
    """Tela principal de login com Google OAuth"""
    
    # ✅ CSS APENAS para a tela de login (main.py já tá aplicando o CSS global!)
    st.markdown("""
        <style>
        .login-box {
            background: #1a1a1a;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(255,107,53,0.2);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }
        .login-title {
            color: #ff6b35;
            margin-bottom: 30px;
            font-size: 28px;
            font-weight: bold;
        }
        .google-button {
            background: white;
            color: #333;
            padding: 12px 24px;
            border-radius: 6px;
            border: 2px solid white;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
            display: inline-block;
            margin: 10px 0;
            transition: all 0.3s;
            text-decoration: none;
        }
        .google-button:hover {
            background: #f0f0f0;
            transform: scale(1.05);
        }
        .google-button:active {
            transform: scale(0.98);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ✅ NOVO: Se já tem token, mostrar mensagem de já logado
    if "token" in st.session_state and st.session_state.token:
        st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh;">
                <div class="login-box">
                    <div class="login-title">🍕 MJ Delivery</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.success("✅ Usuário já logado, acesse a aba do Dashboard")
        st.info("🎉 Você já está autenticado! Acesse a outra aba aberta para ver seu dashboard.")
        return True
    
    # Verificar se voltou com código de autorização
    query_params = st.query_params
    
    if 'code' in query_params:
        # Google retornou o código, trocar por token
        codigo = query_params['code']
        
        with st.spinner("🔄 Autenticando..."):
            tokens = trocar_codigo_por_token(codigo)
            
            if tokens and 'id_token' in tokens:
                # Decodificar ID token
                user_info = decodificar_jwt(tokens['id_token'])
                
                if user_info:
                    email = user_info.get('email', '')
                    
                    # Validar email da empresa
                    if validar_email_empresa(email):
                        # Salvar na sessão
                        st.session_state.user_info = user_info
                        st.session_state.token = tokens.get('id_token')
                        st.session_state.access_token = tokens.get('access_token')
                        st.session_state.authentication_status = True
                        st.session_state.username = user_info.get('name', 'Usuário')
                        
                        # Limpar query params ANTES do success/balloons
                        st.query_params.clear()
                        
                        st.success(f"✅ Bem-vindo, {user_info.get('name', 'Usuário')}!")
                        st.balloons()
                        
                        st.info("🎉 Redirecionando para o dashboard...")
                        
                        # Rerun para ir pro dashboard
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Email não autorizado!\n\n**Seu email:** {email}\n\n**Apenas** emails @gruponoz.com.br podem acessar.")
                        if st.button("🔄 Tentar com outro email"):
                            st.query_params.clear()
                            st.rerun()
            else:
                st.error("❌ Erro ao autenticar. Tente novamente.")
                if st.button("🔄 Tentar Novamente"):
                    st.query_params.clear()
                    st.rerun()
    
    # ✅ Tela de login COMPLETA - MUDA A MENSAGEM QUANDO CLICA
    url_google = gerar_url_autorizacao()
    
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh;">
            <div class="login-box" id="login-box">
                <div class="login-title">🍕 MJ Delivery</div>
                <a href="{url_google}" target="_blank" onclick="mudarMensagem();" class="google-button">
                    🔐 Entrar com conta corporativa
                </a>
            </div>
        </div>
        
        <script>
        function mudarMensagem() {{
            document.getElementById('login-box').innerHTML = `
                <div class="login-title">🍕 MJ Delivery</div>
                <div style="color: #4CAF50; font-size: 18px; font-weight: 600; margin-top: 20px;">
                    ✅ Acesse o Dashboard
                </div>
            `;
        }}
        </script>
    """, unsafe_allow_html=True)
    
    return False

# ════════════════════════════════════════════════════════════════════════════
# RENDERIZAR USUÁRIO LOGADO
# ════════════════════════════════════════════════════════════════════════════

def renderizar_usuario_logado(pagina_principal):
    """Renderiza a interface quando usuário está logado"""
    
    user_info = st.session_state.get("user_info", {})
    
    # Sidebar com info do usuário
    with st.sidebar:
        st.markdown("---")
        
        # Mostrar foto se tiver
        if user_info.get("picture"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(user_info["picture"], width=50, use_column_width=False)
            with col2:
                st.markdown(f"**{user_info.get('name', 'Usuário')}**")
                st.caption(user_info.get("email", ""))
        else:
            st.markdown(f"**👤 {user_info.get('name', 'Usuário')}**")
            st.caption(user_info.get("email", ""))
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True, key="btn_logout"):
            logout()
    
    # Renderizar página principal
    pagina_principal()

if __name__ == "__main__":
    if main_login():
        st.write("✅ Login OK!")
