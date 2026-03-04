import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

fuso = pytz.timezone("America/Sao_Paulo")
hoje_agora = datetime.now(fuso)

# ── Cookie manager (deve ser inicializado logo após set_page_config) ─
COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD", "pytrain-secret-key-2024")
cookies = EncryptedCookieManager(prefix="pytrain_", password=COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>

/* ── BASE ─────────────────────────────────────────────────────── */
.stApp, .stApp * { color: #ffffff; }
.stApp { background-color: #0e1117 !important; }
.block-container { padding-top: 1rem !important; }

/* ── ESCONDE TOOLBAR ──────────────────────────────────────────── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

/* ── TODOS OS LABELS ──────────────────────────────────────────── */
label, .stTextInput label, .stNumberInput label,
.stSelectbox label, .stTextArea label,
.stRadio label, .stCheckbox label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
.stFormLabel, .stFormLabel p {
    color: #e2e2e2 !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}

/* ── INPUTS ───────────────────────────────────────────────────── */
input[type="text"], input[type="password"], input[type="email"],
input[type="number"], textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    border: 1px solid #4a4a6a !important;
    border-radius: 8px !important;
}
[data-baseweb="input"], [data-baseweb="base-input"],
[data-testid="stTextInput"] > div,
[data-testid="stNumberInput"] > div > div {
    background-color: #1e1e2e !important;
    border: 1px solid #4a4a6a !important;
}

/* ── NUMBER INPUT especial ────────────────────────────────────── */
.stNumberInput div div input {
    background-color: #1e1e2e !important;
    color: #e066ff !important;
    font-size: 1.4rem !important;
}
[data-testid="stNumberInput"] button {
    background-color: #2a2a3e !important;
    color: #ffffff !important;
    border: 1px solid #4a4a6a !important;
}

/* ── SELECTBOX ────────────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="select"] input {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
    border: 1px solid #4a4a6a !important;
}

/* ── BOTÕES — cobre TODOS os tipos do Streamlit ──────────────── */
div.stButton > button,
div.stFormSubmitButton > button,
button[kind="primary"],
button[kind="formSubmit"],
button[kind="secondary"],
[data-testid="stFormSubmitButton"] > button,
[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"],
[data-testid="baseButton-formSubmit"] {
    background-color: #7d33ff !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    height: 3.5em !important;
    width: 100% !important;
    font-weight: bold !important;
    font-size: 1rem !important;
    border: none !important;
    opacity: 1 !important;
}
div.stButton > button:hover,
div.stFormSubmitButton > button:hover { background-color: #9b55ff !important; }

/* Botão Sair — sobrescreve acima apenas para o btn_sair */
button[data-testid="baseButton-secondary"]:not([data-testid="stFormSubmitButton"] *) {
    background-color: transparent !important;
    border: 1px solid #7d33ff !important;
    color: #d0b8ff !important;
    height: 2.4em !important;
}

/* ── EXPANDERS ────────────────────────────────────────────────── */
.streamlit-expanderHeader,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
details summary, details summary span {
    background-color: #1e1e2e !important;
    color: #e2e2e2 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"],
details {
    background-color: #1a1a2e !important;
    border: 1px solid #3a3a5a !important;
    border-radius: 10px !important;
}

/* ── INFO / WARNING / ERROR ──────────────────────────────────── */
[data-testid="stInfo"],
[data-testid="stInfo"] p,
.stAlert p, .stAlert {
    color: #ffffff !important;
    font-size: 1rem !important;
}
[data-testid="stInfo"] { background-color: #1a2a3a !important; border-left: 4px solid #4a9eff !important; }
[data-testid="stWarning"] { background-color: #2a1f00 !important; border-left: 4px solid #ffaa00 !important; }
[data-testid="stError"] { background-color: #2a0a0a !important; border-left: 4px solid #ff4444 !important; }
[data-testid="stSuccess"] { background-color: #0a2a0a !important; border-left: 4px solid #44ff88 !important; }

/* ── TABS ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 5px; }
.stTabs [data-baseweb="tab"] {
    background-color: #1e1e2e !important;
    border-radius: 8px 8px 0 0 !important;
    color: #e2e2e2 !important;
    font-size: 0.95rem !important;
}
.stTabs [aria-selected="true"] { background-color: #7d33ff !important; color: #ffffff !important; }

/* ── RADIO ────────────────────────────────────────────────────── */
.stRadio > div > label { color: #e2e2e2 !important; font-size: 1rem !important; }

/* ── DATAFRAME ────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { color: #ffffff !important; }

/* ── MÉTRICAS ─────────────────────────────────────────────────── */
[data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #ffffff !important; }
[data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #cccccc !important; }

/* ── LAYOUT ───────────────────────────────────────────────────── */
.foco-container {
    background-color: #1e1e2e;
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #7d33ff;
    text-align: center;
    margin-bottom: 20px;
}
.login-box {
    max-width: 420px;
    margin: 40px auto;
    background: #1e1e2e;
    border: 2px solid #7d33ff;
    border-radius: 16px;
    padding: 32px 24px;
}
</style>
""", unsafe_allow_html=True)

# CSS extra via components.html para garantir aplicação no mobile
import streamlit.components.v1 as _components

_components.html("""
<style>
  /* Força escuro em TODOS os botões do Streamlit */
  button, [role="button"] {
    background-color: #7d33ff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: bold !important;
    opacity: 1 !important;
  }
  button:hover { background-color: #9b55ff !important; }

  /* Inputs */
  input, textarea {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
    border: 1px solid #4a4a6a !important;
    border-radius: 8px !important;
  }

  /* Labels */
  label { color: #e2e2e2 !important; opacity: 1 !important; }

  /* Expander header */
  summary, details > summary {
    background-color: #1e1e2e !important;
    color: #e2e2e2 !important;
  }
</style>
<script>
// Aplica estilos diretamente no documento pai (iframe → parent)
(function applyStyles() {
  try {
    const doc = window.parent.document;

    // Estilo injetado no parent
    let s = doc.getElementById('pytrain-css');
    if (!s) {
      s = doc.createElement('style');
      s.id = 'pytrain-css';
      doc.head.appendChild(s);
    }
    s.textContent = `
      /* Botões */
      .stApp button,
      .stApp [data-testid="baseButton-primary"],
      .stApp [data-testid="baseButton-secondary"],
      .stApp [data-testid="baseButton-formSubmit"],
      .stApp div.stFormSubmitButton button,
      .stApp div.stButton button {
        background-color: #7d33ff !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
      }
      .stApp button:hover { background-color: #9b55ff !important; }

      /* Inputs */
      .stApp input[type="text"],
      .stApp input[type="password"],
      .stApp input[type="email"],
      .stApp input[type="number"],
      .stApp textarea,
      .stApp [data-baseweb="input"] input,
      .stApp [data-baseweb="base-input"] input {
        background-color: #1e1e2e !important;
        color: #ffffff !important;
        border: 1px solid #5a5a8a !important;
      }

      /* Labels */
      .stApp label,
      .stApp [data-testid="stWidgetLabel"] p {
        color: #e2e2e2 !important;
        opacity: 1 !important;
        font-size: 1rem !important;
      }

      /* Expanders */
      .stApp details summary,
      .stApp .streamlit-expanderHeader {
        background-color: #1e1e2e !important;
        color: #e2e2e2 !important;
        font-weight: 600 !important;
      }
      .stApp details {
        background-color: #1a1a2e !important;
        border: 1px solid #3a3a5a !important;
        border-radius: 10px !important;
      }

      /* Alertas */
      .stApp [data-testid="stAlert"] p,
      .stApp [data-testid="stAlert"] {
        color: #ffffff !important;
      }
    `;
  } catch(e) {}
  // Retry caso o DOM ainda esteja carregando
  setTimeout(applyStyles, 800);
  setTimeout(applyStyles, 2000);
})();
</script>
""", height=0)

# ─────────────────────────────────────────────
# CONEXÃO SUPABASE
# ─────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas no .env")
    st.stop()


@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase()

# ─────────────────────────────────────────────
# INICIALIZAÇÃO DO SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    # Auth
    "usuario": None,  # dict com id, email, nome
    "access_token": None,
    "refresh_token": None,
    # Treino
    "treino_ativo": False,
    "serie_atual": "A",
    "indice_ex": 0,
    "inicio_timer": 0.0,
    # Cardio
    "cardio_ativo": False,
    "params_cardio": None,
    "dist_real": 0.0,
    "t_cardio_start": 0.0,
    "cardio_salvo": False,
    # UI
    "confirmar_historico": False,
    # Perfil
    "perfil_completo": None,  # None = ainda não verificado, True/False após check
    # Sessão persistente
    "sessao_restaurada": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# HELPERS — AUTH
# ─────────────────────────────────────────────
def fazer_login(email: str, senha: str) -> bool:
    """Autentica com Supabase Auth e guarda sessão."""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state.access_token = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id": res.user.id,
            "email": res.user.email,
            "nome": res.user.user_metadata.get("nome", email.split("@")[0]),
        }
        # Persiste tokens no localStorage do browser
        salvar_sessao_local(res.session.access_token, res.session.refresh_token)
        return True
    except Exception as e:
        st.error(f"❌ Email ou senha incorretos.")
        return False


def salvar_sessao_local(access_token: str, refresh_token: str):
    """Salva tokens em cookies criptografados."""
    try:
        cookies["access_token"] = access_token
        cookies["refresh_token"] = refresh_token
        cookies.save()
    except Exception:
        pass


def limpar_sessao_local():
    """Remove cookies de sessão."""
    try:
        cookies["access_token"] = ""
        cookies["refresh_token"] = ""
        cookies.save()
    except Exception:
        pass


def restaurar_sessao() -> bool:
    """Tenta restaurar sessão a partir dos cookies."""
    if st.session_state.sessao_restaurada:
        return False
    st.session_state.sessao_restaurada = True
    try:
        at = cookies.get("access_token", "")
        rt = cookies.get("refresh_token", "")
        if not at or not rt:
            return False
        res = supabase.auth.set_session(at, rt)
        if not res or not res.user:
            limpar_sessao_local()
            return False
        # Renova tokens
        try:
            res2 = supabase.auth.refresh_session(rt)
            novo_at = res2.session.access_token
            novo_rt = res2.session.refresh_token
        except Exception:
            novo_at, novo_rt = at, rt
        st.session_state.access_token = novo_at
        st.session_state.refresh_token = novo_rt
        st.session_state.usuario = {
            "id": res.user.id,
            "email": res.user.email,
            "nome": res.user.user_metadata.get("nome", res.user.email.split("@")[0]),
        }
        salvar_sessao_local(novo_at, novo_rt)
        return True
    except Exception:
        limpar_sessao_local()
        return False


def fazer_logout():
    limpar_sessao_local()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k in ["usuario", "access_token", "refresh_token",
              "treino_ativo", "cardio_ativo", "params_cardio",
              "sessao_restaurada", "perfil_completo"]:
        st.session_state[k] = defaults[k]
    # Limpa query params de sessão
    for p in ["_at", "_rt"]:
        if p in st.query_params:
            del st.query_params[p]
    st.rerun()


def user_id() -> str:
    """Retorna o UUID do utilizador logado."""
    return st.session_state.usuario["id"]


def verificar_perfil() -> bool:
    """Retorna True se o perfil já foi preenchido (tem telefone e cidade)."""
    try:
        res = (
            supabase.table("perfis")
            .select("telefone, cidade")
            .eq("user_id", user_id())
            .execute()
        )
        if res.data and res.data[0].get("telefone") and res.data[0].get("cidade"):
            return True
        return False
    except Exception:
        return False


def tela_completar_perfil():
    """Tela exibida uma única vez após o primeiro login."""
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
            <div style="background:#1e1e2e;border:2px solid #7d33ff;border-radius:16px;
                        padding:32px;text-align:center;margin-bottom:20px;">
                <h2 style="color:#e066ff;margin-bottom:6px;">🏋️ Bem-vinda ao PyTrain PRO!</h2>
                <p style="color:#cccccc;font-size:1rem;">Complete o seu perfil para continuar.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_perfil"):
            nome_p = st.text_input("👤 Nome completo", placeholder="Seu nome completo")
            telefone = st.text_input("📱 Telefone com DDD", placeholder="(28) 99999-9999", max_chars=20)
            cidade = st.text_input("🏙️ Cidade", placeholder="Cidade onde mora")
            estado = st.selectbox("🗺️ Estado", [
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                "RS", "RO", "RR", "SC", "SP", "SE", "TO"
            ], index=7)  # ES por padrão

            salvar = st.form_submit_button("Salvar e Entrar 🚀", use_container_width=True)

        if salvar:
            if not nome_p.strip() or not telefone.strip() or not cidade.strip():
                st.warning("Preencha todos os campos para continuar.")
            else:
                try:
                    # Atualiza nome nos metadados do Auth
                    supabase.auth.update_user({"data": {"nome": nome_p.strip()}})
                    st.session_state.usuario["nome"] = nome_p.strip()

                    # Upsert na tabela perfis
                    supabase.table("perfis").upsert({
                        "user_id": user_id(),
                        "nome": nome_p.strip(),
                        "telefone": telefone.strip(),
                        "cidade": cidade.strip(),
                        "estado": estado,
                    }).execute()

                    st.session_state.perfil_completo = True
                    st.success("✅ Perfil salvo!")
                    time.sleep(0.8)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar perfil: {e}")


# ─────────────────────────────────────────────
# HELPERS — DADOS
# Todas as queries incluem user_id para isolamento
# ─────────────────────────────────────────────
def registrar_historico(ex_id, detalhes: str, tipo: str = "musculacao") -> None:
    supabase.table("historico_treinos").insert({
        "user_id": user_id(),
        "exercicio_id": ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes": detalhes,
        "tipo": tipo,
    }).execute()


def extrair_stats(dataframe: pd.DataFrame) -> tuple[float, int]:
    if dataframe.empty or "detalhes" not in dataframe.columns:
        return 0.0, 0
    kms = dataframe["detalhes"].str.extract(r"([\d.]+)km").astype(float).sum()[0]
    mins = dataframe["detalhes"].str.extract(r"(\d+)min").astype(float).sum()[0]
    return (float(kms) if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)


# ─────────────────────────────────────────────
# TELA DE LOGIN
# ─────────────────────────────────────────────
def tela_login():
    st.markdown("""
        <div class="login-box">
            <h2 style="text-align:center;color:#e066ff;margin-bottom:8px;">🏋️ PyTrain PRO</h2>
            <p style="text-align:center;color:#bbbbbb;margin-bottom:24px;font-size:1rem;">Entre com sua conta para continuar</p>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        # Tabs: Entrar | Esqueci a Senha
        tab_login, tab_reset = st.tabs(["🔑 Entrar", "🔓 Esqueci a Senha"])

        with tab_login:
            with st.form("form_login"):
                email = st.text_input("📧 Email", placeholder="seu@email.com")
                senha = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
                entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                if email and senha:
                    with st.spinner("Autenticando..."):
                        if fazer_login(email, senha):
                            st.rerun()
                else:
                    st.warning("Preencha email e senha.")

        with tab_reset:
            st.caption("Insere o teu email e enviaremos um link para redefinir a senha.")
            with st.form("form_reset"):
                email_reset = st.text_input("📧 Email cadastrado", placeholder="seu@email.com")
                enviar = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
            if enviar:
                if email_reset and "@" in email_reset:
                    try:
                        supabase.auth.reset_password_email(email_reset.strip())
                        st.success(f"✅ Link enviado para **{email_reset}**. Verifique a caixa de entrada.")
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
                else:
                    st.warning("Digite um email válido.")


# ─────────────────────────────────────────────
# FLUXO DE CONVITE — define senha pela primeira vez
# Recebe access_token + refresh_token via query params
# vindos da página de redirect no GitHub Pages
# ─────────────────────────────────────────────
def tela_definir_senha(access_token: str, refresh_token: str):
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
            <div style="background:#1e1e2e;border:2px solid #7d33ff;border-radius:16px;
                        padding:40px 32px;text-align:center;margin-bottom:24px;">
                <h2 style="color:#e066ff;">🏋️ PyTrain PRO</h2>
                <p style="color:#cccccc;font-size:1rem;">Bem-vinda! Define a tua senha para activar a conta.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_definir_senha"):
            nova_senha = st.text_input("🔒 Nova Senha", type="password", placeholder="mínimo 8 caracteres")
            conf_senha = st.text_input("🔒 Confirmar Senha", type="password", placeholder="repita a senha")
            salvar = st.form_submit_button("Activar Conta", use_container_width=True)

        if salvar:
            if not nova_senha or len(nova_senha) < 8:
                st.warning("A senha deve ter pelo menos 8 caracteres.")
                return
            if nova_senha != conf_senha:
                st.error("As senhas não coincidem.")
                return

            try:
                # Autentica com o token do convite
                supabase.auth.set_session(access_token, refresh_token)
                # Actualiza a senha
                supabase.auth.update_user({"password": nova_senha})

                # Faz login imediato com a nova sessão
                user = supabase.auth.get_user()
                st.session_state.access_token = access_token
                st.session_state.refresh_token = refresh_token
                st.session_state.usuario = {
                    "id": user.user.id,
                    "email": user.user.email,
                    "nome": user.user.user_metadata.get("nome", user.user.email.split("@")[0]),
                }
                st.success("✅ Senha definida! A entrar...")
                time.sleep(1)
                # Limpa os query params e reentra no app
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao definir senha: {e}")


# ─────────────────────────────────────────────
# FLUXO PRINCIPAL
# ─────────────────────────────────────────────
qp = st.query_params
url_token = qp.get("access_token")
url_refresh = qp.get("refresh_token")

# Convite / recuperação de senha vindo do GitHub Pages
if url_token and url_refresh and not st.session_state.usuario:
    tela_definir_senha(url_token, url_refresh)
    st.stop()

# Tenta restaurar sessão via cookie (só uma vez por sessão Python)
if not st.session_state.usuario and not st.session_state.sessao_restaurada:
    if restaurar_sessao():
        st.rerun()

if not st.session_state.usuario:
    tela_login()
    st.stop()

# Verifica se o perfil está completo (apenas uma vez por sessão)
if st.session_state.perfil_completo is None:
    st.session_state.perfil_completo = verificar_perfil()

if not st.session_state.perfil_completo:
    tela_completar_perfil()
    st.stop()

# ─────────────────────────────────────────────
# APP PRINCIPAL (só chega aqui se estiver logado e com perfil completo)
# ─────────────────────────────────────────────
nome_usuario = st.session_state.usuario["nome"]
hora_atual = hoje_agora.hour

# Saudação baseada no horário
if hora_atual < 12:
    saudacao = "Bom dia"
    emoji_hora = "🌅"
elif hora_atual < 18:
    saudacao = "Boa tarde"
    emoji_hora = "☀️"
else:
    saudacao = "Boa noite"
    emoji_hora = "🌙"

# Contagem de treinos do mês atual para motivação
try:
    res_streak = (
        supabase.table("historico_treinos")
        .select("data_execucao")
        .eq("user_id", user_id())
        .gte("data_execucao", hoje_agora.replace(day=1, hour=0, minute=0, second=0).isoformat())
        .execute()
    )
    treinos_mes = len(res_streak.data) if res_streak.data else 0
except Exception:
    treinos_mes = 0

if treinos_mes == 0:
    msg_motivacao = "Que tal começar o mês com tudo? 💪"
elif treinos_mes < 5:
    msg_motivacao = f"Já tens <b>{treinos_mes}</b> treinos** este mês. Continue assim! 🔥"
elif treinos_mes < 10:
    msg_motivacao = f"**{treinos_mes} treinos** este mês — você está voando! 🚀"
else:
    msg_motivacao = f"Impressionante! **{treinos_mes} treinos** este mês. Você é uma máquina! 🏆"

# ── Banner de saudação ───────────────────────────────────────────
# Botão Sair como link HTML dentro do banner para evitar corte em mobile
st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#1e1e2e 0%,#2a1a3e 100%);
        border:2px solid #7d33ff;
        border-radius:14px;
        padding:16px 20px;
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        box-sizing:border-box;
        margin-bottom:8px;
    ">
        <div style="display:flex;align-items:center;gap:14px;min-width:0;flex:1;">
            <div style="font-size:2em;line-height:1;flex-shrink:0;">{emoji_hora}</div>
            <div style="min-width:0;">
                <p style="margin:0;color:#c4b0ff;font-size:0.78em;letter-spacing:1px;text-transform:uppercase;">
                    🏋️ PyTrain PRO
                </p>
                <p style="margin:2px 0 3px;color:#ffffff;font-size:1.2em;font-weight:700;">
                    {saudacao}, <span style="color:#e066ff;">{nome_usuario}</span>!
                </p>
                <p style="margin:0;color:#cccccc;font-size:0.88em;">
                    {msg_motivacao}
                </p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Botão Sair separado, abaixo do banner — único jeito confiável no Streamlit
if st.button("🚪 Sair", key="btn_sair"):
    fazer_logout()

# Se veio do botão "Cadastrar exercícios agora", abre direto na aba Menu
_tab_default = 3 if st.session_state.get("ir_para_menu") else 0
if st.session_state.get("ir_para_menu"):
    st.session_state["ir_para_menu"] = False

aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])


# ── Rodapé global (aparece em todas as abas) ─────────────────────────
def rodape():
    st.markdown("""
        <div style="margin-top:48px;padding:16px 0 8px;border-top:1px solid #2a2a3e;
                    text-align:center;">
            <p style="margin:0;color:#aaaaaa;font-size:0.85em;">
                Dúvidas ou sugestões? Entre em contato →
                <a href="mailto:nabevia@gmail.com" style="color:#c4b0ff;text-decoration:underline;">
                    nabevia@gmail.com
                </a>
            </p>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# ABA 1 — TREINO
# ═══════════════════════════════════════════
with aba1:
    if not st.session_state.treino_ativo:
        st.subheader("Escolha sua Série")
        serie = st.radio("Selecione:", ["A", "B", "C", "D"], horizontal=True)

        # Exercícios filtrados pelo user_id
        preview = (
            supabase.table("exercicios")
            .select("nome, series, repeticoes, peso_kg")
            .eq("serie_tipo", serie)
            .eq("user_id", user_id())
            .execute()
        )

        # Busca com id para poder deletar
        preview_full = (
            supabase.table("exercicios")
            .select("id, nome, series, repeticoes, peso_kg")
            .eq("serie_tipo", serie)
            .eq("user_id", user_id())
            .execute()
        )

        if preview_full.data:
            st.markdown(f"#### 📋 Série {serie} — {len(preview_full.data)} exercícios")
            for i, ex in enumerate(preview_full.data, 1):
                col_ex, col_del = st.columns([5, 1])
                with col_ex:
                    st.markdown(
                        f"""<div style="background:#1e1e2e;border-left:3px solid #7d33ff;
                            border-radius:8px;padding:10px 16px;margin:4px 0;
                            display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#ffffff;font-weight:700;font-size:1rem;">{i}. {ex['nome']}</span>
                            <span style="color:#d0b8ff;font-size:0.9em;">
                                {ex['series']}x{ex['repeticoes']} &nbsp;|&nbsp; {ex['peso_kg']} kg
                            </span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with col_del:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_prev_{ex['id']}", help=f"Remover {ex['nome']}"):
                        supabase.table("exercicios").delete().eq("id", ex["id"]).execute()
                        st.rerun()
            pode_iniciar = True
        else:
            st.info(f"Série {serie} vazia.")
            pode_iniciar = False

        # Formulário de cadastro sempre visível na aba Treino
        with st.expander("➕ Adicionar exercício à Série " + serie, expanded=not pode_iniciar):
            with st.form(f"form_treino_cadastro_{serie}"):
                r_nome = st.text_input("Nome do exercício", placeholder="Ex: Supino Reto")
                c1r, c2r, c3r = st.columns(3)
                r_peso = c1r.number_input("Peso (kg)", value=0, min_value=0)
                r_series = c2r.number_input("Séries", value=3, min_value=1)
                r_reps = c3r.number_input("Reps", value=12, min_value=1)
                if st.form_submit_button("✅ Adicionar", use_container_width=True):
                    if r_nome.strip():
                        existe = (
                            supabase.table("exercicios")
                            .select("id")
                            .ilike("nome", r_nome.strip())
                            .eq("serie_tipo", serie)
                            .eq("user_id", user_id())
                            .execute()
                        )
                        if existe.data:
                            st.warning(f"'{r_nome}' já existe na Série {serie}.")
                        else:
                            supabase.table("exercicios").insert({
                                "user_id": user_id(),
                                "nome": r_nome.strip(),
                                "serie_tipo": serie,
                                "peso_kg": r_peso,
                                "series": r_series,
                                "repeticoes": r_reps,
                            }).execute()
                            st.success(f"✅ '{r_nome}' adicionado!")
                            st.rerun()
                    else:
                        st.warning("Digite o nome do exercício.")

        if st.button(f"🚀 INICIAR TREINO — SÉRIE {serie}", use_container_width=True, disabled=not pode_iniciar):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual = serie
            st.session_state.indice_ex = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()

    else:
        res = (
            supabase.table("exercicios")
            .select("*")
            .eq("serie_tipo", st.session_state.serie_atual)
            .eq("user_id", user_id())
            .execute()
        )

        if not res.data:
            st.warning("Nenhum exercício cadastrado para esta série.")
            if st.button("Voltar"):
                st.session_state.treino_ativo = False
                st.rerun()
        else:
            total_ex = len(res.data)
            indice = st.session_state.indice_ex

            if indice >= total_ex:
                st.session_state.treino_ativo = False
                st.balloons()
                st.success("🎉 Treino concluído!")
                st.rerun()

            ex_atual = res.data[indice]

            st.markdown(f"""
                <div class="foco-container">
                    <h4 style="color:#cccccc;margin:0;">
                        Série {st.session_state.serie_atual} | {indice + 1} de {total_ex}
                    </h4>
                    <h1 style="color:#e066ff;margin:10px 0;font-size:28px;">{ex_atual['nome']}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg", value=int(ex_atual["peso_kg"]), step=1, key=f"p_{indice}")
            s = c2.number_input("Sets", value=int(ex_atual["series"]), step=1, key=f"s_{indice}")
            r = c3.number_input("Reps", value=int(ex_atual["repeticoes"]), step=1, key=f"r_{indice}")

            tempo_total_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_total_seg, 60)
            st.markdown(f"""
                <div style="text-align:center;padding:15px;border:1px solid #7d33ff;
                            border-radius:12px;margin:15px 0;">
                    <small style="color:#cccccc;font-size:0.85rem;">TEMPO TOTAL</small><br>
                    <span style="font-size:40px;font-weight:bold;color:#ffffff;">{m:02d}:{seg:02d}</span>
                </div>
            """, unsafe_allow_html=True)

            col_prox, col_cancel = st.columns(2)

            if col_prox.button("PRÓXIMO ➡️", use_container_width=True):
                registrar_historico(ex_atual["id"], f"{p}kg | {s}x{r} | {tempo_total_seg // 60}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual["id"]).execute()
                st.session_state.indice_ex += 1
                st.rerun()

            if col_cancel.button("🛑 CANCELAR", type="secondary", use_container_width=True):
                st.session_state.treino_ativo = False
                st.rerun()

            time.sleep(1)
            st.rerun()

    rodape()

# ═══════════════════════════════════════════
# ABA 2 — CARDIO
# ═══════════════════════════════════════════
with aba2:
    if not st.session_state.cardio_ativo:
        st.subheader("Configurar Esteira")
        modo = st.radio("Objetivo:", ["Distância Alvo (km)", "Número de Ciclos"], horizontal=True)

        c1, c2 = st.columns(2)
        t_anda = c1.number_input("Minutos Andando", value=5.0, step=1.0)
        v_anda = c1.number_input("Vel. Andando", value=5.0, step=0.5)
        t_corre = c2.number_input("Minutos Correndo", value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo", value=9.0, step=0.5)

        dist_ciclo = (v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60))
        if dist_ciclo <= 0:
            st.warning("Verifique as velocidades e tempos configurados.")
            st.stop()

        if modo == "Distância Alvo (km)":
            dist_alvo = st.number_input("Meta (km)", value=5.0, step=0.5, min_value=0.1)
            n_ciclos = max(1, round(dist_alvo / dist_ciclo))
            tempo_total_min = n_ciclos * (t_anda + t_corre)
            st.info(
                f"Estimativa: **{n_ciclos} ciclos** → ~{dist_ciclo * n_ciclos:.2f} km | ~{int(tempo_total_min)} min")
        else:
            n_ciclos = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos
            tempo_total_min = n_ciclos * (t_anda + t_corre)
            st.info(f"Estimativa: ~{dist_alvo:.2f} km | ~{int(tempo_total_min)} min")

        if st.button("🚀 INICIAR CARDIO", use_container_width=True):
            etapas = []
            for i in range(int(n_ciclos)):
                etapas.append((f"🚶 Caminhada ({i + 1}/{int(n_ciclos)})", int(t_anda * 60), v_anda))
                etapas.append((f"⚡ Corrida   ({i + 1}/{int(n_ciclos)})", int(t_corre * 60), v_corre))

            st.session_state.cardio_ativo = True
            st.session_state.cardio_salvo = False
            st.session_state.dist_real = 0.0
            st.session_state.t_cardio_start = time.time()
            st.session_state.params_cardio = {
                "etapas": etapas,
                "dist_alvo": dist_alvo,
                "etapa_idx": 0,
                "seg_restantes": etapas[0][1] if etapas else 0,
            }
            st.rerun()

    else:
        params = st.session_state.params_cardio
        etapas = params["etapas"]
        dist_alvo = params["dist_alvo"]
        idx = params["etapa_idx"]

        if st.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(None, f"Interrompido: {st.session_state.dist_real:.2f}km | {t_final}min",
                                    tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.rerun()

        if idx >= len(etapas):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(None, f"Concluído: {st.session_state.dist_real:.2f}km | {t_final}min",
                                    tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.success("🎉 Objetivo concluído!")
            st.balloons()
            st.rerun()

        nome_etapa, _, vel_etapa = etapas[idx]
        seg = params["seg_restantes"]
        m, s = divmod(seg, 60)

        st.markdown(f"""
            <div class="foco-container" style="border-color:#e066ff;background:black;">
                <h2 style="color:#e066ff;margin:0;">{nome_etapa}</h2>
                <h1 style="font-size:70px;margin:10px 0;">{m:02d}:{s:02d}</h1>
                <h3 style="color:#5fffdc;font-size:1.3em;">
                    {st.session_state.dist_real:.2f} / {dist_alvo:.2f} km
                </h3>
            </div>
        """, unsafe_allow_html=True)

        time.sleep(1)
        st.session_state.dist_real += vel_etapa / 3600

        if seg <= 1:
            params["etapa_idx"] += 1
            next_idx = params["etapa_idx"]
            params["seg_restantes"] = etapas[next_idx][1] if next_idx < len(etapas) else 0
        else:
            params["seg_restantes"] -= 1

        st.session_state.params_cardio = params
        st.rerun()

    rodape()

# ═══════════════════════════════════════════
# ABA 3 — PAINEL
# ═══════════════════════════════════════════
with aba3:
    st.header("📊 Performance & Histórico")

    try:
        # Histórico filtrado pelo user_id
        res_h = (
            supabase.table("historico_treinos")
            .select("*, exercicios(nome)")
            .eq("user_id", user_id())
            .order("data_execucao", desc=True)
            .execute()
        )

        if not res_h.data:
            st.info("Nenhum treino registado ainda.")
        else:
            df = pd.json_normalize(res_h.data)
            df["data_execucao"] = pd.to_datetime(df["data_execucao"]).dt.tz_convert("America/Sao_Paulo")

            st.subheader("📅 Filtrar Período")
            col_f1, col_f2 = st.columns(2)

            anos = sorted(df["data_execucao"].dt.year.unique(), reverse=True)
            ano_sel = col_f1.selectbox("Ano", anos)

            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
            }
            meses_disp = sorted(
                df[df["data_execucao"].dt.year == ano_sel]["data_execucao"].dt.month.unique(),
                reverse=True,
            )
            mes_sel = col_f2.selectbox("Mês", meses_disp, format_func=lambda x: meses_nomes[x])

            df_filtrado = df[
                (df["data_execucao"].dt.month == mes_sel) &
                (df["data_execucao"].dt.year == ano_sel)
                ]

            st.markdown(f"#### 📈 Resumo de {meses_nomes[mes_sel]}/{ano_sel}")
            c1, c2, c3 = st.columns(3)
            km_f, min_f = extrair_stats(df_filtrado)
            c1.metric("Treinos", len(df_filtrado))
            c2.metric("Distância", f"{km_f:.2f} km")
            c3.metric("Tempo Total", f"{min_f} min")

            df_hoje = df[df["data_execucao"].dt.date == hoje_agora.date()]
            inicio_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0, minute=0, second=0,
                                                                                     microsecond=0)
            df_semana = df[df["data_execucao"] >= inicio_sem]

            with st.expander("📌 Ver Hoje e Esta Semana"):
                km_h, min_h = extrair_stats(df_hoje)
                km_s, min_s = extrair_stats(df_semana)
                st.markdown(f"""
**Hoje:** {len(df_hoje)} atividades | {km_h:.2f} km | {min_h} min
**Esta Semana:** {len(df_semana)} atividades | {km_s:.2f} km | {min_s} min
                """)

            st.divider()
            st.subheader(f"📜 Atividades em {meses_nomes[mes_sel]}")

            if df_filtrado.empty:
                st.info(f"Nenhum registo em {meses_nomes[mes_sel]}.")
            else:
                df_show = df_filtrado.copy()
                if "exercicios.nome" not in df_show.columns:
                    df_show["exercicios.nome"] = "🏃 Cardio"
                df_show["exercicios.nome"] = df_show["exercicios.nome"].fillna("🏃 Cardio")
                df_show["Data"] = df_show["data_execucao"].dt.strftime("%d/%m/%Y %H:%M")
                st.dataframe(df_show[["Data", "exercicios.nome", "detalhes"]], use_container_width=True,
                             hide_index=True)

            st.divider()
            if st.button("🗑️ Apagar todo o histórico", use_container_width=True):
                st.session_state["confirmar_historico"] = True

            if st.session_state.get("confirmar_historico"):
                st.error("Tens a certeza? Esta acção apaga **todo** o teu histórico.")
                c_sim, c_nao = st.columns(2)
                if c_sim.button("✅ Sim, apagar"):
                    supabase.table("historico_treinos").delete().eq("user_id", user_id()).execute()
                    st.session_state["confirmar_historico"] = False
                    st.success("Histórico limpo.")
                    st.rerun()
                if c_nao.button("❌ Cancelar"):
                    st.session_state["confirmar_historico"] = False
                    st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

    rodape()

# ═══════════════════════════════════════════
# ABA 4 — MENU / PERFIL
# ═══════════════════════════════════════════
with aba4:
    email_atual = st.session_state.usuario["email"]
    nome_atual = st.session_state.usuario["nome"]

    # ── Busca dados do perfil no banco ───────────────────────────────
    try:
        res_perfil = (
            supabase.table("perfis")
            .select("nome, telefone, cidade, estado")
            .eq("user_id", user_id())
            .execute()
        )
        dados_perfil = res_perfil.data[0] if res_perfil.data else {}
    except Exception:
        dados_perfil = {}

    # ── Card com dados actuais ────────────────────────────────────────
    st.markdown(f"""
        <div style="background:#1e1e2e;border:2px solid #7d33ff;border-radius:14px;
                    padding:24px 28px;margin-bottom:20px;">
            <p style="margin:0 0 16px;color:#c4b0ff;font-size:0.85em;
                      text-transform:uppercase;letter-spacing:1px;font-weight:700;">👤 Meus Dados</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div>
                    <p style="margin:0;color:#bbbbbb;font-size:0.82em;font-weight:600;letter-spacing:0.5px;">NOME</p>
                    <p style="margin:0;color:white;font-weight:600;">{dados_perfil.get('nome', nome_atual)}</p>
                </div>
                <div>
                    <p style="margin:0;color:#bbbbbb;font-size:0.82em;font-weight:600;letter-spacing:0.5px;">EMAIL</p>
                    <p style="margin:0;color:white;font-weight:600;">{email_atual}</p>
                </div>
                <div>
                    <p style="margin:0;color:#bbbbbb;font-size:0.82em;font-weight:600;letter-spacing:0.5px;">TELEFONE</p>
                    <p style="margin:0;color:white;font-weight:600;">{dados_perfil.get('telefone', '—')}</p>
                </div>
                <div>
                    <p style="margin:0;color:#bbbbbb;font-size:0.82em;font-weight:600;letter-spacing:0.5px;">CIDADE / ESTADO</p>
                    <p style="margin:0;color:white;font-weight:600;">
                        {dados_perfil.get('cidade', '—')} / {dados_perfil.get('estado', '—')}
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Formulário de edição ──────────────────────────────────────────
    with st.expander("✏️ Alterar dados pessoais"):
        with st.form("form_dados_pessoais"):
            ed_nome = st.text_input("Nome completo", value=dados_perfil.get("nome", nome_atual))
            ed_telefone = st.text_input("Telefone com DDD", value=dados_perfil.get("telefone", ""),
                                        placeholder="(28) 99999-9999")
            ed_cidade = st.text_input("Cidade", value=dados_perfil.get("cidade", ""))
            estados = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                       "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                       "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
            idx_estado = estados.index(dados_perfil.get("estado", "ES")) if dados_perfil.get("estado",
                                                                                             "ES") in estados else 7
            ed_estado = st.selectbox("Estado", estados, index=idx_estado)
            if st.form_submit_button("💾 Salvar alterações", use_container_width=True):
                if ed_nome.strip() and ed_telefone.strip() and ed_cidade.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": ed_nome.strip()}})
                        supabase.table("perfis").upsert({
                            "user_id": user_id(),
                            "nome": ed_nome.strip(),
                            "telefone": ed_telefone.strip(),
                            "cidade": ed_cidade.strip(),
                            "estado": ed_estado,
                        }).execute()
                        st.session_state.usuario["nome"] = ed_nome.strip()
                        st.success("✅ Dados atualizados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha todos os campos.")

    # ── Alterar email ─────────────────────────────────────────────────
    with st.expander("📧 Alterar email"):
        st.info(
            "O processo tem **2 etapas**:\n"
            "1. Você recebe um link de confirmação no **email atual**\n"
            "2. Após confirmar, recebe outro link no **novo email**\n\n"
            "Só após as duas confirmações o email será alterado."
        )
        with st.form("form_email"):
            novo_email = st.text_input("Novo email", placeholder="novo@email.com")
            senha_email = st.text_input("Confirme sua senha", type="password")
            if st.form_submit_button("Enviar confirmações", use_container_width=True):
                if not novo_email.strip() or "@" not in novo_email:
                    st.warning("Digite um email válido.")
                elif not senha_email:
                    st.warning("Confirme sua senha para continuar.")
                else:
                    try:
                        # Valida senha antes de iniciar troca de email
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_email})
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success(
                            f"✅ Confirmações enviadas! Verifique **{email_atual}** "
                            f"e depois **{novo_email.strip()}** para concluir a alteração."
                        )
                    except Exception as e:
                        if "Invalid login" in str(e) or "invalid_credentials" in str(e):
                            st.error("❌ Senha incorreta.")
                        else:
                            st.error(f"Erro: {e}")

    # ── Alterar senha ─────────────────────────────────────────────────
    with st.expander("🔒 Alterar senha"):
        with st.form("form_senha"):
            senha_antiga = st.text_input("Senha atual", type="password")
            nova_senha = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            conf_senha = st.text_input("Confirmar nova senha", type="password")
            if st.form_submit_button("Salvar senha", use_container_width=True):
                if not senha_antiga:
                    st.warning("Digite a senha atual.")
                elif len(nova_senha) < 8:
                    st.warning("A nova senha deve ter pelo menos 8 caracteres.")
                elif nova_senha != conf_senha:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_antiga})
                        supabase.auth.update_user({"password": nova_senha})
                        st.success("✅ Senha alterada!")
                    except Exception:
                        st.error("❌ Senha atual incorreta.")

    st.divider()

    # ── Apagar conta ──────────────────────────────────────────────────
    with st.expander("🚨 Apagar minha conta"):
        st.warning(
            "Esta acção é **irreversível**. Todos os teus treinos, histórico e acesso serão removidos permanentemente.")
        with st.form("form_apagar_conta"):
            conf_texto = st.text_input("Digite **APAGAR** para confirmar", placeholder="APAGAR")
            senha_conf = st.text_input("Confirme sua senha", type="password")
            if st.form_submit_button("🗑️ Apagar conta permanentemente", use_container_width=True):
                if conf_texto.strip().upper() != "APAGAR":
                    st.error("Digite APAGAR em maiúsculas para confirmar.")
                elif not senha_conf:
                    st.warning("Confirme sua senha.")
                else:
                    try:
                        # 1. Valida senha e obtém token fresco
                        res_login = supabase.auth.sign_in_with_password({
                            "email": email_atual, "password": senha_conf
                        })
                        token = res_login.session.access_token
                        uid = user_id()

                        # 2. Tenta chamar a Edge Function
                        edge_ok = False
                        edge_url = f"{SUPABASE_URL}/functions/v1/delete-account"
                        try:
                            import urllib.request as _ur, json as _json, ssl as _ssl

                            _req = _ur.Request(
                                edge_url,
                                data=b"{}",
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "apikey": SUPABASE_KEY,
                                    "Content-Type": "application/json",
                                },
                                method="POST",
                            )
                            ctx = _ssl.create_default_context()
                            with _ur.urlopen(_req, context=ctx, timeout=15) as _r:
                                _body = _json.loads(_r.read())
                            if _body.get("success"):
                                edge_ok = True
                            else:
                                st.error(f"Erro na Edge Function: {_body.get('error', _body)}")
                        except Exception as edge_err:
                            st.error(f"❌ Erro: {edge_err}")

                        # 3. Se Edge Function OK, faz logout
                        if edge_ok:
                            st.success("✅ Conta apagada. Até logo! 👋")
                            time.sleep(1)
                            fazer_logout()

                    except Exception as e:
                        err = str(e)
                        if "invalid_credentials" in err or "Invalid login" in err or "invalid" in err.lower():
                            st.error("❌ Senha incorreta.")
                        else:
                            st.error(f"Erro inesperado: {err}")

    rodape()