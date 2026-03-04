import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
_COOKIE_PWD  = os.getenv("COOKIE_PASSWORD", "pytrain-2024-x7k")

cookies = EncryptedCookieManager(prefix="pt_", password=_COOKIE_PWD)
if not cookies.ready():
    st.stop()

fuso      = pytz.timezone("America/Sao_Paulo")
hoje_agora = datetime.now(fuso)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0 !important;
}
.block-container {
    padding: 1rem 1rem 2rem !important;
    max-width: 680px !important;
    margin: 0 auto !important;
}
header[data-testid="stHeader"],#MainMenu,footer { display:none !important; }

.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,
.stApp span,.stApp div,.stApp label {
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0 !important;
}

.stApp label,
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stWidgetLabel"] {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    opacity: 1 !important;
}

.stApp input[type="text"],
.stApp input[type="password"],
.stApp input[type="email"],
.stApp input[type="number"],
.stApp textarea,
.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="base-input"] input {
    background: #13131a !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.65rem 0.9rem !important;
    transition: border-color 0.2s !important;
}
.stApp [data-baseweb="input"],
.stApp [data-baseweb="base-input"] {
    background: #13131a !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 10px !important;
}
.stApp input:focus,
.stApp [data-baseweb="input"]:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}

.stApp .stNumberInput div div input {
    background: #13131a !important;
    color: #a78bfa !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 500 !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 10px !important;
}
.stApp [data-testid="stNumberInput"] button {
    background: #1e1e2e !important;
    color: #a78bfa !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 8px !important;
    font-size: 1.1rem !important;
}
.stApp [data-testid="stNumberInput"] button:hover {
    background: #2d2040 !important;
    border-color: #7c3aed !important;
}

.stApp [data-baseweb="select"] > div {
    background: #13131a !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stApp [data-baseweb="select"] span,
.stApp [data-baseweb="select"] div { color: #e2e8f0 !important; }

.stApp .stButton > button,
.stApp .stFormSubmitButton > button,
.stApp [data-testid="baseButton-primary"],
.stApp [data-testid="baseButton-secondary"],
.stApp [data-testid="baseButton-formSubmit"],
.stApp [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    height: 3em !important;
    width: 100% !important;
    transition: opacity 0.15s, transform 0.1s !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.3) !important;
}
.stApp .stButton > button:hover,
.stApp .stFormSubmitButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.4) !important;
}
.stApp .stButton > button:active { transform: translateY(0) !important; }
.stApp .stButton > button:disabled {
    background: #1e1e2e !important;
    color: #4a4a6a !important;
    box-shadow: none !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: #13131a !important;
    padding: 4px !important;
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 9px !important;
    color: #64748b !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: #7c3aed !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.4) !important;
}

.stApp [data-testid="stExpander"] {
    background: #13131a !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 0.5rem !important;
}
.stApp [data-testid="stExpander"] summary,
.stApp details summary,
.stApp .streamlit-expanderHeader {
    background: #13131a !important;
    color: #c4b5fd !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    padding: 0.9rem 1rem !important;
}
.stApp [data-testid="stExpander"] summary:hover { background: #1a1a2a !important; }
.stApp [data-testid="stExpander"] summary p { color: #c4b5fd !important; }

.stApp [data-testid="stAlert"],
.stApp [data-testid="stAlert"] * { color: #e2e8f0 !important; font-size: 0.9rem !important; }
.stApp [data-testid="stInfo"]    { background: #0d1f33 !important; border: none !important; border-left: 3px solid #3b82f6 !important; border-radius: 10px !important; }
.stApp [data-testid="stWarning"] { background: #1f1500 !important; border: none !important; border-left: 3px solid #f59e0b !important; border-radius: 10px !important; }
.stApp [data-testid="stError"]   { background: #1f0808 !important; border: none !important; border-left: 3px solid #ef4444 !important; border-radius: 10px !important; }
.stApp [data-testid="stSuccess"] { background: #071f10 !important; border: none !important; border-left: 3px solid #10b981 !important; border-radius: 10px !important; }

.stApp .stRadio > div { gap: 0.4rem !important; }
.stApp .stRadio label {
    background: #13131a !important;
    border: 1px solid #2d2d3d !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.8rem !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    color: #94a3b8 !important;
    font-size: 0.88rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}
.stApp .stRadio label:has(input:checked) {
    background: rgba(124,58,237,0.15) !important;
    border-color: #7c3aed !important;
    color: #c4b5fd !important;
}

[data-testid="stMetric"] {
    background: #13131a !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.6rem !important;
    color: #e2e8f0 !important;
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }

.stApp hr { border-color: #1e1e2e !important; margin: 1.5rem 0 !important; }

.stApp .stCaption, .stApp [data-testid="stCaptionContainer"] p {
    color: #475569 !important;
    font-size: 0.82rem !important;
}

/* Custom classes usadas via unsafe_allow_html — funcionam bem em desktop e mobile */
.pt-card {
    background: #13131a;
    border: 1px solid #1e1e2e;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.pt-card-accent {
    background: linear-gradient(135deg,#13131a,#170f2e);
    border: 1px solid #3b1f72;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.pt-label {
    color: #475569;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0 0 2px;
}
.pt-value {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
}
.pt-ex-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #13131a;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin: 0.35rem 0;
    transition: border-color 0.15s;
}
.pt-ex-row:hover { border-color: #3b1f72; }
.pt-ex-name { color: #e2e8f0; font-weight: 600; font-size: 0.95rem; }
.pt-ex-meta { color: #7c3aed; font-size: 0.82rem; font-family: 'DM Mono', monospace; }
.pt-timer {
    text-align: center;
    background: #0d0d14;
    border: 1px solid #1e1e2e;
    border-radius: 14px;
    padding: 1rem;
    margin: 1rem 0;
}
.pt-timer-label { color: #475569; font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; }
.pt-timer-val {
    font-family: 'DM Mono', monospace;
    font-size: 3.2rem;
    font-weight: 500;
    color: #e2e8f0;
    line-height: 1.1;
}
.pt-badge {
    display: inline-block;
    background: rgba(124,58,237,0.15);
    color: #a78bfa;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 8px;
}
.pt-section-title {
    color: #475569;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e1e2e;
}
/* Grid para perfil — responsivo no mobile */
.pt-perfil-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
@media (max-width: 480px) {
    .pt-perfil-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas.")
    st.stop()

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
supabase = get_supabase()

defaults = {
    "usuario": None, "access_token": None, "refresh_token": None,
    "treino_ativo": False, "serie_atual": "A", "indice_ex": 0, "inicio_timer": 0.0,
    "cardio_ativo": False, "params_cardio": None, "dist_real": 0.0,
    "t_cardio_start": 0.0, "cardio_salvo": False,
    "confirmar_historico": False, "perfil_completo": None,
    "sessao_restaurada": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _cookie_get(key: str) -> str:
    try:
        val = cookies[key]
        return val if val else ""
    except Exception:
        return ""

def _cookie_set(key: str, val: str):
    try:
        cookies[key] = val
        cookies.save()
    except Exception:
        pass

def fazer_login(email: str, senha: str) -> bool:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id": res.user.id, "email": res.user.email,
            "nome": res.user.user_metadata.get("nome", email.split("@")[0]),
        }
        _cookie_set("rt", res.session.refresh_token)
        return True
    except Exception:
        st.error("❌ Email ou senha incorretos.")
        return False

def restaurar_sessao() -> bool:
    if st.session_state.sessao_restaurada:
        return False
    st.session_state.sessao_restaurada = True
    rt = _cookie_get("rt")
    if not rt:
        return False
    try:
        res = supabase.auth.refresh_session(rt)
        if not res or not res.session or not res.user:
            _cookie_set("rt", "")
            return False
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id": res.user.id, "email": res.user.email,
            "nome": res.user.user_metadata.get("nome", res.user.email.split("@")[0]),
        }
        _cookie_set("rt", res.session.refresh_token)
        return True
    except Exception:
        _cookie_set("rt", "")
        return False

def fazer_logout():
    _cookie_set("rt", "")
    try: supabase.auth.sign_out()
    except Exception: pass
    for k in list(defaults.keys()):
        st.session_state[k] = defaults[k]
    st.rerun()

def user_id() -> str:
    return st.session_state.usuario["id"]

def verificar_perfil() -> bool:
    try:
        res = supabase.table("perfis").select("telefone,cidade").eq("user_id", user_id()).execute()
        return bool(res.data and res.data[0].get("telefone") and res.data[0].get("cidade"))
    except Exception:
        return False

def registrar_historico(ex_id, detalhes: str, tipo: str = "musculacao"):
    supabase.table("historico_treinos").insert({
        "user_id": user_id(), "exercicio_id": ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes": detalhes, "tipo": tipo,
    }).execute()

def extrair_stats(df: pd.DataFrame):
    if df.empty or "detalhes" not in df.columns:
        return 0.0, 0
    km = df["detalhes"].str.extract(r"([\d.]+)km").astype(float).sum()[0]
    mn = df["detalhes"].str.extract(r"(\d+)min").astype(float).sum()[0]
    return (float(km) if not pd.isna(km) else 0.0), (int(mn) if not pd.isna(mn) else 0)

def rodape():
    st.markdown("""
        <div style="margin-top:3rem;padding-top:1rem;border-top:1px solid #1e1e2e;text-align:center;">
            <p style="margin:0;color:#334155;font-size:0.78rem;">
                Dúvidas → <a href="mailto:nabevia@gmail.com" style="color:#7c3aed;text-decoration:none;">nabevia@gmail.com</a>
            </p>
        </div>
    """, unsafe_allow_html=True)

def tela_login():
    st.markdown("""
        <div style="text-align:center;padding:2.5rem 0 1.5rem;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">🏋️</div>
            <h1 style="font-size:1.8rem;font-weight:700;color:#e2e8f0;margin:0;">PyTrain PRO</h1>
            <p style="color:#475569;font-size:0.9rem;margin-top:0.4rem;">Seu treino, sua evolução.</p>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_reset = st.tabs(["Entrar", "Recuperar senha"])
        with tab_login:
            with st.form("form_login"):
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                email = st.text_input("Email", placeholder="seu@email.com")
                senha = st.text_input("Senha", type="password", placeholder="••••••••")
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                if email and senha:
                    with st.spinner(""):
                        if fazer_login(email, senha):
                            st.rerun()
                else:
                    st.warning("Preencha email e senha.")
        with tab_reset:
            st.caption("Enviaremos um link para redefinir sua senha.")
            with st.form("form_reset"):
                email_reset = st.text_input("Email", placeholder="seu@email.com")
                enviar = st.form_submit_button("Enviar link", use_container_width=True)
            if enviar:
                if email_reset and "@" in email_reset:
                    try:
                        supabase.auth.reset_password_email(email_reset.strip())
                        st.success(f"Link enviado para {email_reset}.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Digite um email válido.")

def tela_definir_senha(access_token: str, refresh_token: str):
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
            <div style="text-align:center;padding:2rem 0 1rem;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">🏋️</div>
                <h2 style="color:#e2e8f0;font-size:1.4rem;font-weight:700;margin:0;">Ativar conta</h2>
                <p style="color:#475569;font-size:0.88rem;margin-top:0.3rem;">Crie sua senha para começar.</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("form_definir_senha"):
            nova = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            conf = st.text_input("Confirmar senha", type="password")
            ok   = st.form_submit_button("Ativar conta", use_container_width=True)
        if ok:
            if not nova or len(nova) < 8:
                st.warning("Mínimo 8 caracteres.")
                return
            if nova != conf:
                st.error("Senhas não coincidem.")
                return
            try:
                supabase.auth.set_session(access_token, refresh_token)
                supabase.auth.update_user({"password": nova})
                user = supabase.auth.get_user()
                st.session_state.access_token  = access_token
                st.session_state.refresh_token = refresh_token
                st.session_state.usuario = {
                    "id": user.user.id, "email": user.user.email,
                    "nome": user.user.user_metadata.get("nome", user.user.email.split("@")[0]),
                }
                _cookie_set("rt", refresh_token)
                st.success("Conta ativada!")
                time.sleep(0.8)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

def tela_completar_perfil():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
            <div style="text-align:center;padding:2rem 0 1rem;">
                <div style="font-size:2rem;">👋</div>
                <h2 style="color:#e2e8f0;font-size:1.4rem;font-weight:700;margin:0.3rem 0 0;">Bem-vinda!</h2>
                <p style="color:#475569;font-size:0.88rem;margin-top:0.3rem;">Complete seu perfil para continuar.</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("form_perfil"):
            nome_p   = st.text_input("Nome completo", placeholder="Seu nome")
            telefone = st.text_input("Telefone com DDD", placeholder="(28) 99999-9999", max_chars=20)
            cidade   = st.text_input("Cidade", placeholder="Onde você mora")
            estado   = st.selectbox("Estado", [
                "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"], index=7)
            salvar = st.form_submit_button("Salvar e entrar →", use_container_width=True)
        if salvar:
            if not nome_p.strip() or not telefone.strip() or not cidade.strip():
                st.warning("Preencha todos os campos.")
            else:
                try:
                    supabase.auth.update_user({"data": {"nome": nome_p.strip()}})
                    st.session_state.usuario["nome"] = nome_p.strip()
                    supabase.table("perfis").upsert({
                        "user_id": user_id(), "nome": nome_p.strip(),
                        "telefone": telefone.strip(), "cidade": cidade.strip(), "estado": estado,
                    }).execute()
                    st.session_state.perfil_completo = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

qp = st.query_params
url_at = qp.get("access_token")
url_rt = qp.get("refresh_token")

if url_at and url_rt and not st.session_state.usuario:
    tela_definir_senha(url_at, url_rt)
    st.stop()

if not st.session_state.usuario and not st.session_state.sessao_restaurada:
    if restaurar_sessao():
        st.rerun()

if not st.session_state.usuario:
    tela_login()
    st.stop()

if st.session_state.perfil_completo is None:
    st.session_state.perfil_completo = verificar_perfil()

if not st.session_state.perfil_completo:
    tela_completar_perfil()
    st.stop()

nome_usuario = st.session_state.usuario["nome"].split()[0]
hora         = hoje_agora.hour
saudacao     = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
emoji_hora   = "🌅" if hora < 12 else "☀️" if hora < 18 else "🌙"

try:
    r = supabase.table("historico_treinos").select("data_execucao").eq("user_id", user_id())\
        .gte("data_execucao", hoje_agora.replace(day=1,hour=0,minute=0,second=0).isoformat()).execute()
    treinos_mes = len(r.data) if r.data else 0
except Exception:
    treinos_mes = 0

msg = (
    "Vamos começar o mês forte! 💪" if treinos_mes == 0 else
    f"{treinos_mes} treino{'s' if treinos_mes>1 else ''} este mês — continue! 🔥" if treinos_mes < 5 else
    f"{treinos_mes} treinos — você está em chamas! 🚀" if treinos_mes < 10 else
    f"{treinos_mes} treinos este mês. Lendária! 🏆"
)

st.markdown(f"""
    <div class="pt-card-accent" style="display:flex;align-items:center;gap:1rem;margin-bottom:0.25rem;">
        <div style="font-size:2.2rem;line-height:1;">{emoji_hora}</div>
        <div style="flex:1;min-width:0;">
            <div class="pt-badge">PyTrain PRO</div>
            <p style="margin:4px 0 2px;font-size:1.15rem;font-weight:700;color:#e2e8f0;">
                {saudacao}, <span style="color:#a78bfa;">{nome_usuario}</span>
            </p>
            <p style="margin:0;font-size:0.82rem;color:#64748b;">{msg}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

col_sair, _ = st.columns([1, 3])
with col_sair:
    if st.button("Sair →", key="btn_sair"):
        fazer_logout()

aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Perfil"])

# ═══════════════════════════════════════════════════════════════════
# ABA 1 — TREINO
# ═══════════════════════════════════════════════════════════════════
with aba1:
    if not st.session_state.treino_ativo:
        serie = st.radio("Série", ["A", "B", "C", "D"], horizontal=True, label_visibility="collapsed")

        exs = supabase.table("exercicios").select("id,nome,series,repeticoes,peso_kg")\
            .eq("serie_tipo", serie).eq("user_id", user_id()).execute()

        if exs.data:
            st.markdown(f'<p class="pt-section-title">Série {serie} · {len(exs.data)} exercícios</p>', unsafe_allow_html=True)
            for i, ex in enumerate(exs.data, 1):
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f"""
                        <div class="pt-ex-row">
                            <span class="pt-ex-name">{i}. {ex['nome']}</span>
                            <span class="pt-ex-meta">{ex['series']}×{ex['repeticoes']} · {ex['peso_kg']}kg</span>
                        </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"del_{ex['id']}", help="Remover"):
                        supabase.table("exercicios").delete().eq("id", ex["id"]).execute()
                        st.rerun()
            pode_iniciar = True
        else:
            st.markdown(f'<p class="pt-section-title">Série {serie} · vazia</p>', unsafe_allow_html=True)
            pode_iniciar = False

        with st.expander(f"＋ Adicionar exercício — Série {serie}", expanded=not pode_iniciar):
            with st.form(f"form_add_{serie}"):
                r_nome = st.text_input("Nome", placeholder="Ex: Supino Reto")
                c1, c2, c3 = st.columns(3)
                r_peso   = c1.number_input("Peso kg", value=0, min_value=0)
                r_series = c2.number_input("Séries",  value=3, min_value=1)
                r_reps   = c3.number_input("Reps",    value=12, min_value=1)
                if st.form_submit_button("Adicionar", use_container_width=True):
                    if r_nome.strip():
                        dup = supabase.table("exercicios").select("id")\
                            .ilike("nome", r_nome.strip()).eq("serie_tipo", serie)\
                            .eq("user_id", user_id()).execute()
                        if dup.data:
                            st.warning(f"'{r_nome}' já existe na Série {serie}.")
                        else:
                            supabase.table("exercicios").insert({
                                "user_id": user_id(), "nome": r_nome.strip(),
                                "serie_tipo": serie, "peso_kg": r_peso,
                                "series": r_series, "repeticoes": r_reps,
                            }).execute()
                            st.success(f"✓ '{r_nome}' adicionado!")
                            st.rerun()
                    else:
                        st.warning("Digite o nome.")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button(f"Iniciar Série {serie} →", use_container_width=True, disabled=not pode_iniciar):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual  = serie
            st.session_state.indice_ex    = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()

    else:
        res = supabase.table("exercicios").select("*")\
            .eq("serie_tipo", st.session_state.serie_atual).eq("user_id", user_id()).execute()

        if not res.data:
            st.warning("Nenhum exercício nesta série.")
            if st.button("Voltar"):
                st.session_state.treino_ativo = False
                st.rerun()
        else:
            total  = len(res.data)
            idx    = st.session_state.indice_ex

            if idx >= total:
                st.session_state.treino_ativo = False
                st.balloons()
                st.success("🎉 Treino concluído!")
                st.rerun()

            ex = res.data[idx]
            pct = int((idx / total) * 100)

            st.markdown(f"""
                <div class="pt-card-accent" style="text-align:center;padding:1.5rem;">
                    <div class="pt-badge">Série {st.session_state.serie_atual} · {idx+1} / {total}</div>
                    <div style="background:#1e1e2e;border-radius:6px;height:4px;margin:0.75rem 0;">
                        <div style="background:#7c3aed;width:{pct}%;height:100%;border-radius:6px;"></div>
                    </div>
                    <h2 style="color:#e2e8f0;font-size:1.4rem;font-weight:700;margin:0.5rem 0 0;">{ex['nome']}</h2>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg",   value=int(ex["peso_kg"]),   step=1, key=f"p{idx}")
            s = c2.number_input("Sets", value=int(ex["series"]),     step=1, key=f"s{idx}")
            r = c3.number_input("Reps", value=int(ex["repeticoes"]), step=1, key=f"r{idx}")

            elapsed = int(time.time() - st.session_state.inicio_timer)
            m, sg   = divmod(elapsed, 60)
            st.markdown(f"""
                <div class="pt-timer">
                    <div class="pt-timer-label">tempo de treino</div>
                    <div class="pt-timer-val">{m:02d}:{sg:02d}</div>
                </div>
            """, unsafe_allow_html=True)

            c_prox, c_cancel = st.columns(2)
            if c_prox.button("Próximo →", use_container_width=True):
                registrar_historico(ex["id"], f"{p}kg | {s}×{r} | {elapsed//60}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex["id"]).execute()
                st.session_state.indice_ex += 1
                st.rerun()
            if c_cancel.button("Cancelar", use_container_width=True):
                st.session_state.treino_ativo = False
                st.rerun()

            time.sleep(1)
            st.rerun()

    rodape()

# ═══════════════════════════════════════════════════════════════════
# ABA 2 — CARDIO
# ═══════════════════════════════════════════════════════════════════
with aba2:
    if not st.session_state.cardio_ativo:
        st.markdown('<p class="pt-section-title">Configurar esteira</p>', unsafe_allow_html=True)
        modo = st.radio("Modo", ["Distância (km)", "Número de ciclos"], horizontal=True, label_visibility="collapsed")

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Min. Andando",  value=5.0, step=1.0)
        v_anda  = c1.number_input("Vel. Andando",  value=5.0, step=0.5)
        t_corre = c2.number_input("Min. Correndo", value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo", value=9.0, step=0.5)

        dist_ciclo = (v_anda*(t_anda/60)) + (v_corre*(t_corre/60))
        if dist_ciclo <= 0:
            st.warning("Verifique velocidades e tempos.")
            st.stop()

        if modo == "Distância (km)":
            dist_alvo = st.number_input("Meta em km", value=5.0, step=0.5, min_value=0.1)
            n_ciclos  = max(1, round(dist_alvo / dist_ciclo))
        else:
            n_ciclos  = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos

        km_est  = dist_ciclo * n_ciclos
        min_est = int(n_ciclos * (t_anda + t_corre))
        st.info(f"{n_ciclos} ciclos · ~{km_est:.2f} km · ~{min_est} min")

        if st.button("Iniciar cardio →", use_container_width=True):
            etapas = []
            for i in range(int(n_ciclos)):
                etapas += [
                    (f"🚶 Caminhada {i+1}/{int(n_ciclos)}", int(t_anda*60), v_anda),
                    (f"⚡ Corrida {i+1}/{int(n_ciclos)}",   int(t_corre*60), v_corre),
                ]
            st.session_state.update({
                "cardio_ativo": True, "cardio_salvo": False,
                "dist_real": 0.0, "t_cardio_start": time.time(),
                "params_cardio": {"etapas": etapas, "dist_alvo": dist_alvo,
                                  "etapa_idx": 0, "seg_restantes": etapas[0][1]},
            })
            st.rerun()
    else:
        p  = st.session_state.params_cardio
        et = p["etapas"]; da = p["dist_alvo"]; idx = p["etapa_idx"]

        if st.button("Encerrar e salvar", use_container_width=True):
            if not st.session_state.cardio_salvo:
                tf = int((time.time()-st.session_state.t_cardio_start)/60)
                registrar_historico(None, f"Interrompido: {st.session_state.dist_real:.2f}km | {tf}min", tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.rerun()

        if idx >= len(et):
            if not st.session_state.cardio_salvo:
                tf = int((time.time()-st.session_state.t_cardio_start)/60)
                registrar_historico(None, f"Concluído: {st.session_state.dist_real:.2f}km | {tf}min", tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.balloons(); st.success("🎉 Objetivo concluído!")
            st.rerun()

        nome_et, _, vel_et = et[idx]
        seg = p["seg_restantes"]; m, s = divmod(seg, 60)
        pct = int((st.session_state.dist_real / da) * 100) if da > 0 else 0

        st.markdown(f"""
            <div class="pt-card-accent" style="text-align:center;padding:1.5rem;">
                <h3 style="color:#a78bfa;margin:0 0 0.5rem;font-size:1rem;">{nome_et}</h3>
                <div style="background:#1e1e2e;border-radius:6px;height:4px;margin:0.5rem auto;max-width:200px;">
                    <div style="background:#7c3aed;width:{min(pct,100)}%;height:100%;border-radius:6px;"></div>
                </div>
                <div class="pt-timer-val" style="font-size:4rem;">{m:02d}:{s:02d}</div>
                <p style="color:#10b981;font-family:'DM Mono',monospace;font-size:1.1rem;margin:0.5rem 0 0;">
                    {st.session_state.dist_real:.2f} / {da:.2f} km
                </p>
            </div>
        """, unsafe_allow_html=True)

        time.sleep(1)
        st.session_state.dist_real += vel_et / 3600
        if seg <= 1:
            p["etapa_idx"] += 1
            ni = p["etapa_idx"]
            p["seg_restantes"] = et[ni][1] if ni < len(et) else 0
        else:
            p["seg_restantes"] -= 1
        st.session_state.params_cardio = p
        st.rerun()

    rodape()

# ═══════════════════════════════════════════════════════════════════
# ABA 3 — PAINEL
# ═══════════════════════════════════════════════════════════════════
with aba3:
    try:
        res_h = supabase.table("historico_treinos").select("*,exercicios(nome)")\
            .eq("user_id", user_id()).order("data_execucao", desc=True).execute()

        if not res_h.data:
            st.info("Nenhum treino registado ainda.")
        else:
            df = pd.json_normalize(res_h.data)
            df["data_execucao"] = pd.to_datetime(df["data_execucao"]).dt.tz_convert("America/Sao_Paulo")

            anos = sorted(df["data_execucao"].dt.year.unique(), reverse=True)
            c1, c2 = st.columns(2)
            ano_sel = c1.selectbox("Ano", anos)
            meses_n = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
                       7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
            meses_d = sorted(df[df["data_execucao"].dt.year==ano_sel]["data_execucao"].dt.month.unique(), reverse=True)
            mes_sel = c2.selectbox("Mês", meses_d, format_func=lambda x: meses_n[x])

            df_f = df[(df["data_execucao"].dt.month==mes_sel)&(df["data_execucao"].dt.year==ano_sel)]
            km_f, min_f = extrair_stats(df_f)

            c1, c2, c3 = st.columns(3)
            c1.metric("Treinos", len(df_f))
            c2.metric("Distância", f"{km_f:.1f} km")
            c3.metric("Tempo", f"{min_f} min")

            df_h = df[df["data_execucao"].dt.date == hoje_agora.date()]
            ini_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
            df_s = df[df["data_execucao"] >= ini_sem]

            with st.expander("Hoje e esta semana"):
                km_h, min_h = extrair_stats(df_h)
                km_s, min_s = extrair_stats(df_s)
                col1, col2 = st.columns(2)
                # ── Substituído: usando st.metric em vez de HTML raw com grid ──
                with col1:
                    st.markdown('<p class="pt-label">Hoje</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="pt-value">{len(df_h)} atividades · {km_h:.1f}km · {min_h}min</p>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<p class="pt-label">Esta semana</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="pt-value">{len(df_s)} atividades · {km_s:.1f}km · {min_s}min</p>', unsafe_allow_html=True)

            st.markdown(f'<p class="pt-section-title">Atividades — {meses_n[mes_sel]}</p>', unsafe_allow_html=True)
            if df_f.empty:
                st.info(f"Nenhum registro em {meses_n[mes_sel]}.")
            else:
                df_show = df_f.copy()
                if "exercicios.nome" not in df_show.columns:
                    df_show["exercicios.nome"] = "Cardio"
                df_show["exercicios.nome"] = df_show["exercicios.nome"].fillna("Cardio")
                df_show["Data"] = df_show["data_execucao"].dt.strftime("%d/%m %H:%M")
                st.dataframe(df_show[["Data","exercicios.nome","detalhes"]].rename(
                    columns={"exercicios.nome":"Exercício","detalhes":"Detalhes"}),
                    use_container_width=True, hide_index=True)

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if st.button("Apagar histórico completo", use_container_width=True):
                st.session_state["confirmar_historico"] = True
            if st.session_state.get("confirmar_historico"):
                st.error("Esta ação apaga todo o seu histórico permanentemente.")
                c1, c2 = st.columns(2)
                if c1.button("Sim, apagar"):
                    supabase.table("historico_treinos").delete().eq("user_id", user_id()).execute()
                    st.session_state["confirmar_historico"] = False
                    st.success("Histórico apagado.")
                    st.rerun()
                if c2.button("Cancelar"):
                    st.session_state["confirmar_historico"] = False
                    st.rerun()

    except Exception as e:
        st.error(f"Erro: {e}")

    rodape()

# ═══════════════════════════════════════════════════════════════════
# ABA 4 — PERFIL
# ═══════════════════════════════════════════════════════════════════
with aba4:
    email_atual = st.session_state.usuario["email"]
    nome_atual  = st.session_state.usuario["nome"]

    try:
        rp = supabase.table("perfis").select("nome,telefone,cidade,estado").eq("user_id", user_id()).execute()
        dp = rp.data[0] if rp.data else {}
    except Exception:
        dp = {}

    # ── Card de perfil: HTML completo em um único st.markdown ────────
    st.markdown(f"""
        <div class="pt-card-accent">
            <p class="pt-label" style="margin-bottom:1rem;">Meu perfil</p>
            <div style="display:flex;flex-wrap:wrap;gap:1rem;">
                <div style="flex:1;min-width:120px;">
                    <p class="pt-label">Nome</p>
                    <p class="pt-value">{dp.get('nome', nome_atual)}</p>
                </div>
                <div style="flex:1;min-width:120px;">
                    <p class="pt-label">Email</p>
                    <p class="pt-value" style="font-size:0.88rem;word-break:break-all;">{email_atual}</p>
                </div>
                <div style="flex:1;min-width:120px;">
                    <p class="pt-label">Telefone</p>
                    <p class="pt-value">{dp.get('telefone','—')}</p>
                </div>
                <div style="flex:1;min-width:120px;">
                    <p class="pt-label">Cidade / Estado</p>
                    <p class="pt-value">{dp.get('cidade','—')} · {dp.get('estado','—')}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("Editar dados pessoais"):
        with st.form("form_dados"):
            ed_nome     = st.text_input("Nome", value=dp.get("nome", nome_atual))
            ed_tel      = st.text_input("Telefone", value=dp.get("telefone",""), placeholder="(28) 99999-9999")
            ed_cidade   = st.text_input("Cidade", value=dp.get("cidade",""))
            ests        = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                           "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
            idx_e       = ests.index(dp.get("estado","ES")) if dp.get("estado","ES") in ests else 7
            ed_estado   = st.selectbox("Estado", ests, index=idx_e)
            if st.form_submit_button("Salvar", use_container_width=True):
                if ed_nome.strip() and ed_tel.strip() and ed_cidade.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": ed_nome.strip()}})
                        supabase.table("perfis").upsert({
                            "user_id": user_id(), "nome": ed_nome.strip(),
                            "telefone": ed_tel.strip(), "cidade": ed_cidade.strip(), "estado": ed_estado,
                        }).execute()
                        st.session_state.usuario["nome"] = ed_nome.strip()
                        st.success("✓ Dados atualizados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha todos os campos.")

    with st.expander("Alterar email"):
        st.caption("Você receberá links de confirmação no email atual e no novo.")
        with st.form("form_email"):
            novo_email  = st.text_input("Novo email", placeholder="novo@email.com")
            senha_email = st.text_input("Sua senha atual", type="password")
            if st.form_submit_button("Enviar confirmações", use_container_width=True):
                if not novo_email.strip() or "@" not in novo_email:
                    st.warning("Email inválido.")
                elif not senha_email:
                    st.warning("Digite sua senha.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_email})
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success("Confirmações enviadas! Verifique ambos os emails.")
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else f"Erro: {e}")

    with st.expander("Alterar senha"):
        with st.form("form_senha"):
            s_antiga = st.text_input("Senha atual", type="password")
            s_nova   = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            s_conf   = st.text_input("Confirmar nova senha", type="password")
            if st.form_submit_button("Salvar senha", use_container_width=True):
                if not s_antiga:
                    st.warning("Digite a senha atual.")
                elif len(s_nova) < 8:
                    st.warning("Mínimo 8 caracteres.")
                elif s_nova != s_conf:
                    st.error("Senhas não coincidem.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": s_antiga})
                        supabase.auth.update_user({"password": s_nova})
                        st.success("✓ Senha alterada!")
                    except Exception:
                        st.error("Senha atual incorreta.")

    st.divider()

    with st.expander("⚠️ Apagar minha conta"):
        st.warning("Ação irreversível. Todos os dados serão removidos permanentemente.")
        with st.form("form_del_conta"):
            conf_txt   = st.text_input("Digite APAGAR para confirmar", placeholder="APAGAR")
            senha_conf = st.text_input("Sua senha", type="password")
            if st.form_submit_button("Apagar conta", use_container_width=True):
                if conf_txt.strip().upper() != "APAGAR":
                    st.error("Digite APAGAR em maiúsculas.")
                elif not senha_conf:
                    st.warning("Digite sua senha.")
                else:
                    try:
                        rl    = supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_conf})
                        token = rl.session.access_token
                        import urllib.request as _ur, json as _js, ssl as _ssl
                        req = _ur.Request(
                            f"{SUPABASE_URL}/functions/v1/delete-account",
                            data=b"{}",
                            headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"},
                            method="POST",
                        )
                        with _ur.urlopen(req, context=_ssl.create_default_context(), timeout=15) as rr:
                            body = _js.loads(rr.read())
                        if body.get("success"):
                            st.success("Conta apagada. Até logo! 👋")
                            time.sleep(1)
                            fazer_logout()
                        else:
                            st.error(f"Erro: {body.get('error', body)}")
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else f"Erro: {e}")

    rodape()