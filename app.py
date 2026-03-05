import streamlit as st
import time
import os
import random
import pandas as pd
from datetime import datetime, timedelta, date
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client
from streamlit_cookies_manager import EncryptedCookieManager

# ── Biblioteca interna ─────────────────────────────────────────────────────────
from pytrain import (
    # utils
    FRASES, CONQUISTAS_DEF,
    fmt_tempo, fmt_mm_ss, extrair_stats,
    calcular_streak, frase_aba,
    # auth
    cookie_get, cookie_set,
    fazer_login, restaurar_sessao, fazer_logout, verificar_perfil,
    # db
    registrar_historico, buscar_historico_completo,
    ultima_carga, verificar_pr,
    desbloquear_conquista, verificar_conquistas_treino,
    # cardio
    gerar_etapas, distancia_ciclo, calcular_estado_cardio,
)

import re as _re

# ── Config ─────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
_COOKIE_PWD  = os.getenv("COOKIE_PASSWORD", "pytrain-2024-x7k")

cookies = EncryptedCookieManager(prefix="pt_", password=_COOKIE_PWD)
if not cookies.ready():
    st.stop()

fuso       = pytz.timezone("America/Sao_Paulo")
hoje_agora = datetime.now(fuso)

# ── Supabase ───────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Variáveis de ambiente não encontradas.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ── Session state defaults ─────────────────────────────────────────────────────

DEFAULTS = {
    "usuario": None, "access_token": None, "refresh_token": None,
    "treino_ativo": False, "serie_atual": "A", "indice_ex": 0, "inicio_timer": 0.0,
    "timer_descanso": 0, "timer_descanso_inicio": 0.0, "timer_descanso_ativo": False,
    "cardio_ativo": False, "params_cardio": None, "dist_real": 0.0,
    "t_cardio_start": 0.0, "cardio_salvo": False,
    "confirmar_historico": False, "perfil_completo": None,
    "sessao_restaurada": False,
    "frase_idx": 0, "aba_anterior": None,
    "treino_livre_exs": [],
    "ultimo_idx_registrado": -1,
    "n_adds": 0,  # contador para resetar form de adicionar
    "ordem_exercicios": [],  # IDs na ordem atual do treino
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers locais ─────────────────────────────────────────────────────────────

def uid() -> str:
    return st.session_state.usuario["id"]

def _registrar(ex_id, detalhes, tipo="musculacao"):
    registrar_historico(supabase, uid(), fuso, ex_id, detalhes, tipo)

def _desbloquear(conquista_id):
    desbloquear_conquista(supabase, uid(), fuso, conquista_id)

def _ultima_carga(ex_id):
    return ultima_carga(supabase, uid(), fuso, ex_id)

def _verificar_pr(ex_id, peso):
    return verificar_pr(supabase, uid(), ex_id, peso)

def _frase(nome_aba):
    return frase_aba(nome_aba, st.session_state)

def rodape():
    st.divider()
    st.caption("Dúvidas: nabevia@gmail.com")

# ═══════════════════════════════
# TELAS PRÉ-LOGIN
# ═══════════════════════════════

def tela_login():
    st.markdown("""
    <style>
    .block-container { max-width:420px !important; margin:0 auto !important;
        padding-left:1rem !important; padding-right:1rem !important; }
    input { font-size:16px !important; min-height:44px !important; }
    button, [role="button"] { min-height:44px !important; }
    #MainMenu, header, footer { display:none !important; }
    </style>""", unsafe_allow_html=True)
    st.title("🏋️ PyTrain PRO")
    st.caption("Seu treino, sua evolução.")
    st.divider()
    with st.container():
        tab_login, tab_reset = st.tabs(["Entrar", "Recuperar senha"])
        with tab_login:
            with st.form("form_login"):
                email  = st.text_input("Email", placeholder="seu@email.com")
                senha  = st.text_input("Senha", type="password", placeholder="••••••••")
                entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                if email and senha:
                    with st.spinner(""):
                        if fazer_login(supabase, cookies, email, senha):
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
                        st.success("Link enviado para " + email_reset)
                    except Exception as e:
                        st.error("Erro: " + str(e))
                else:
                    st.warning("Digite um email válido.")


def tela_definir_senha(access_token, refresh_token):
    st.markdown("""
    <style>
    .block-container { max-width:420px !important; margin:0 auto !important;
        padding-left:1rem !important; padding-right:1rem !important; }
    input { font-size:16px !important; min-height:44px !important; }
    button, [role="button"] { min-height:44px !important; }
    #MainMenu, header, footer { display:none !important; }
    </style>""", unsafe_allow_html=True)
    with st.container():
        st.title("🏋️ Ativar conta")
        st.caption("Crie sua senha para começar.")
        with st.form("form_definir_senha"):
            nova = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            conf = st.text_input("Confirmar senha", type="password")
            ok   = st.form_submit_button("Ativar conta", use_container_width=True)
        if ok:
            if not nova or len(nova) < 8:
                st.warning("Mínimo 8 caracteres."); return
            if nova != conf:
                st.error("Senhas não coincidem."); return
            try:
                supabase.auth.set_session(access_token, refresh_token)
                supabase.auth.update_user({"password": nova})
                user = supabase.auth.get_user()
                st.session_state.access_token  = access_token
                st.session_state.refresh_token = refresh_token
                st.session_state.usuario = {
                    "id":    user.user.id,
                    "email": user.user.email,
                    "nome":  user.user.user_metadata.get("nome", user.user.email.split("@")[0]),
                }
                cookie_set(cookies, "rt", refresh_token)
                st.success("Conta ativada!")
                time.sleep(0.8)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error("Erro: " + str(e))


def tela_completar_perfil():
    st.markdown("""
    <style>
    .block-container { max-width:420px !important; margin:0 auto !important;
        padding-left:1rem !important; padding-right:1rem !important; }
    input, select { font-size:16px !important; min-height:44px !important; }
    button, [role="button"] { min-height:44px !important; }
    #MainMenu, header, footer { display:none !important; }
    </style>""", unsafe_allow_html=True)
    with st.container():
        st.title("👋 Bem-vinda!")
        st.caption("Complete seu perfil para continuar.")
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
                        "user_id":  uid(), "nome":     nome_p.strip(),
                        "telefone": telefone.strip(), "cidade": cidade.strip(), "estado": estado,
                    }).execute()
                    st.session_state.perfil_completo = True
                    st.rerun()
                except Exception as e:
                    st.error("Erro: " + str(e))

# ═══════════════════════════════
# FLUXO PRINCIPAL
# ═══════════════════════════════

qp    = st.query_params
url_at = qp.get("access_token")
url_rt = qp.get("refresh_token")

if url_at and url_rt and not st.session_state.usuario:
    tela_definir_senha(url_at, url_rt)
    st.stop()

if not st.session_state.usuario and not st.session_state.sessao_restaurada:
    if restaurar_sessao(supabase, cookies):
        st.rerun()

if not st.session_state.usuario:
    tela_login(); st.stop()

if st.session_state.perfil_completo is None:
    st.session_state.perfil_completo = verificar_perfil(supabase, uid())

if not st.session_state.perfil_completo:
    tela_completar_perfil(); st.stop()

# ═══════════════════════════════
# CABEÇALHO
# ═══════════════════════════════

nome_usuario = st.session_state.usuario["nome"].split()[0]
hora         = hoje_agora.hour
saudacao     = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
emoji_hora   = "🌅" if hora < 12 else "☀️" if hora < 18 else "🌙"

try:
    r = supabase.table("historico_treinos").select("data_execucao").eq("user_id", uid())\
        .gte("data_execucao", hoje_agora.replace(day=1, hour=0, minute=0, second=0).isoformat()).execute()
    treinos_mes = len(r.data) if r.data else 0
except Exception:
    treinos_mes = 0

if treinos_mes == 0:   msg_treinos = "Nenhum treino este mês ainda — bora começar! 💪"
elif treinos_mes < 5:  msg_treinos = str(treinos_mes) + " treino(s) este mês. Continue assim! 🔥"
elif treinos_mes < 10: msg_treinos = str(treinos_mes) + " treinos este mês. Você está em chamas! 🚀"
else:                  msg_treinos = str(treinos_mes) + " treinos este mês. Lendária! 🏆"

st.markdown("""
<style>
/* ── Reset e base ── */
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Container responsivo ── */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 480px !important;
    margin: 0 auto !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* ── Tipografia global — fontes maiores e melhor contraste ── */
p, span, label, div, li {
    font-size: 0.95rem !important;
    color: #e2e8f0 !important;
}
.stCaption, [data-testid="stCaptionContainer"] p {
    font-size: 0.82rem !important;
    color: #b0b8c8 !important;
}

/* ── Selectbox (nav) compacto ── */
div[data-testid="stSelectbox"] > div { min-height: 38px !important; }
div[data-testid="stSelectbox"] > div > div {
    padding: 4px 10px !important;
    font-size: 0.85rem !important;
    color: #e2e8f0 !important;
}

/* ── Touch targets mínimos 44px ── */
button, a, [role="button"],
div[data-testid="stButton"] > button {
    min-height: 44px !important;
    min-width: 44px !important;
}

/* ── Inputs mobile-friendly ── */
input, textarea, select,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    font-size: 16px !important;   /* evita zoom no iOS */
    min-height: 44px !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── Botões com cantos arredondados e espaçamento ── */
div[data-testid="stButton"] > button {
    border-radius: 12px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}

/* ── Tabs responsivos ── */
div[data-testid="stTabs"] button {
    font-size: 0.88rem !important;
    padding: 8px 14px !important;
    min-height: 44px !important;
}

/* ── Expanders ── */
details[data-testid="stExpander"] summary {
    min-height: 44px !important;
    font-size: 0.95rem !important;
    padding: 8px 12px !important;
}

/* ── Métricas ── */
div[data-testid="stMetric"] {
    padding: 6px !important;
}
div[data-testid="stMetric"] label {
    font-size: 0.78rem !important;
    color: #b0b8c8 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
    color: #f0f0f5 !important;
}

/* ── DataFrames scroll horizontal ── */
div[data-testid="stDataFrame"] {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

/* ── Espaçamento entre colunas mobile ── */
div[data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
    flex-wrap: wrap !important;
}

/* ── Responsividade extra para telas < 480px ── */
@media (max-width: 480px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
    }
}
</style>""", unsafe_allow_html=True)

# ── Navegação ────────────────────────────────────────────────────────────────
for _k, _v in {"aba_ativa":"home"}.items():
    if _k not in st.session_state: st.session_state[_k] = _v

# Header + dropdown compacto
_a = st.session_state.aba_ativa
titulo_aba = {"home":"🏠","treino":"🚀 Treino","cardio":"🏃 Cardio",
              "painel":"📊 Painel","evolucao":"📈 Evolução",
              "conquistas":"🏆 Conquistas","perfil":"⚙️ Perfil"}.get(_a,"")

ABAS = [("🏠 Home","home"),("🚀 Treino","treino"),("🏃 Cardio","cardio"),
        ("📊 Painel","painel"),("📈 Evolução","evolucao"),
        ("🏆 Conquistas","conquistas"),("⚙️ Perfil","perfil"),("🚪 Sair","__sair__")]

col_header, col_nav = st.columns([3, 2])
with col_header:
    st.markdown(
        f"<div style='font-size:1.1rem;font-weight:800;line-height:1.2;color:#f0f0f5'>{emoji_hora} {saudacao}, {nome_usuario}!</div>"
        f"<div style='font-size:0.75rem;color:#a0a8b8;margin-top:2px'>{msg_treinos}</div>",
        unsafe_allow_html=True)
with col_nav:
    escolha = st.selectbox("Navegar", [l for l,_ in ABAS],
        index=[k for _,k in ABAS].index(_a) if _a in [k for _,k in ABAS] else 0,
        label_visibility="collapsed", key="nav_select")
_nav_key = dict(ABAS).get(escolha, "")
if _nav_key == "__sair__":
    fazer_logout(supabase, cookies, DEFAULTS)
elif _nav_key and _nav_key != _a:
    st.session_state.aba_ativa = _nav_key
    st.rerun()

# Contexto manager
class _FakeCtx:
    def __init__(self, ativa): self.ativa = ativa
    def __enter__(self): return self
    def __exit__(self, *a): pass

aba0 = _FakeCtx(_a == "home")
aba1 = _FakeCtx(_a == "treino")
aba2 = _FakeCtx(_a == "cardio")
aba3 = _FakeCtx(_a == "painel")
aba4 = _FakeCtx(_a == "evolucao")
aba5 = _FakeCtx(_a == "conquistas")
aba6 = _FakeCtx(_a == "perfil")

# ═══════════════════════════════
# HOME
# ═══════════════════════════════

if aba0.ativa:
    # Calcula dados para o painel Home
    _treinos_mes = treinos_mes
    _frase_home  = FRASES[(hoje_agora.day + hoje_agora.month) % len(FRASES)]

    # Streak e dados de hoje
    try:
        _res_all = supabase.table("historico_treinos").select("data_execucao")\
            .eq("user_id", uid()).execute()
        _df_all = pd.json_normalize(_res_all.data) if _res_all.data else pd.DataFrame()
        if not _df_all.empty:
            _df_all["data_execucao"] = pd.to_datetime(_df_all["data_execucao"])
        _streak = calcular_streak(_df_all, hoje_agora.date())
        _hoje_dt = hoje_agora.replace(hour=0, minute=0, second=0, microsecond=0)
        _df_hoje = _df_all[_df_all["data_execucao"] >= _hoje_dt] if not _df_all.empty else pd.DataFrame()
        _n_hoje = len(_df_hoje)
        if not _df_all.empty:
            _ult_data = _df_all["data_execucao"].max().astimezone(fuso).strftime("%d/%m %H:%M")
        else:
            _ult_data = ""
    except Exception:
        _streak = 0
        _n_hoje = 0
        _ult_data = ""

    # Meta semanal — conta dias distintos com exercício
    try:
        _ini_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        _res_sem = supabase.table("historico_treinos").select("data_execucao")\
            .eq("user_id", uid()).gte("data_execucao", _ini_sem.isoformat()).execute()
        if _res_sem.data:
            _dias_sem = len(set(
                pd.to_datetime(r["data_execucao"]).date() for r in _res_sem.data
            ))
        else:
            _dias_sem = 0
    except Exception:
        _dias_sem = 0
    if "meta_sem_dias" not in st.session_state:
        st.session_state.meta_sem_dias = 5
    _meta_sem = st.session_state.meta_sem_dias
    _pct_meta = min(int((_dias_sem / _meta_sem) * 100), 100) if _meta_sem > 0 else 0

    streak_cor   = "#4ade80" if _streak >= 3 else "#facc15" if _streak >= 1 else "#888"
    hoje_txt     = f"✅ {_n_hoje} exercício(s) hoje" if _n_hoje > 0 else "Nenhum treino hoje ainda"
    ult_txt      = f"Último: {_ult_data}" if _ult_data else ""

    st.markdown(f"""
<div style="background:#13132a;border-radius:14px;padding:14px;margin-bottom:10px">
  <div style="font-size:0.78rem;color:#b0b8c8;margin-bottom:8px;letter-spacing:1px">ESTE MÊS</div>
  <div style="display:flex;gap:8px">
    <div style="flex:1;background:#0f0f1a;border-radius:10px;padding:10px;text-align:center">
      <div style="font-size:0.72rem;color:#b0b8c8">TREINOS</div>
      <div style="font-size:1.8rem;font-weight:900;color:#a78bfa">{_treinos_mes}</div>
    </div>
    <div style="flex:1;background:#0f0f1a;border-radius:10px;padding:10px;text-align:center">
      <div style="font-size:0.72rem;color:#b0b8c8">SEQUÊNCIA</div>
      <div style="font-size:1.8rem;font-weight:900;color:{streak_cor}">{_streak}🔥</div>
    </div>
  </div>
</div>

<div style="background:#13132a;border-radius:14px;padding:14px;margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
    <div style="font-size:0.78rem;color:#b0b8c8;letter-spacing:1px">META DA SEMANA (dias)</div>
    <div style="font-size:0.75rem;color:#a78bfa;font-weight:700">{_dias_sem}/{_meta_sem} dias</div>
  </div>
  <div style="height:8px;background:#1a1a3e;border-radius:4px">
    <div style="height:8px;background:{'#4ade80' if _pct_meta >= 100 else '#7c3aed'};border-radius:4px;width:{_pct_meta}%;transition:width .3s"></div>
  </div>
  <div style="font-size:0.78rem;color:#9ca3b0;margin-top:4px">{hoje_txt} · {ult_txt}</div>
</div>

<div style="background:#13132a;border-radius:14px;padding:12px;margin-bottom:10px">
  <div style="font-size:0.8rem;color:#a78bfa;font-style:italic">✨ {_frase_home}</div>
</div>""", unsafe_allow_html=True)

    with st.expander("⚙️ Alterar meta semanal"):
        nova_meta = st.number_input(
            "Meta (dias por semana)", value=_meta_sem,
            min_value=1, max_value=7, step=1, key="input_meta_sem")
        if nova_meta != st.session_state.meta_sem_dias:
            st.session_state.meta_sem_dias = nova_meta
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 Treino", use_container_width=True, type="primary"):
        st.session_state.aba_ativa = "treino"; st.rerun()
    if c2.button("🏃 Cardio", use_container_width=True):
        st.session_state.aba_ativa = "cardio"; st.rerun()

# ═══════════════════════════════
# ABA 1 — TREINO
# ═══════════════════════════════

if aba1.ativa:
    st.info("✨ " + _frase("treino"))

    modo_treino = st.radio("Modo", ["Série", "Treino Livre"], horizontal=True, label_visibility="collapsed")

    # ── Treino Livre ──────────────────────────────────────────────────────────
    if modo_treino == "Treino Livre":
        st.caption("TREINO LIVRE — adicione exercícios na hora")

        # Delete treino livre via query param
        _qp2 = st.query_params
        _del_livre = _qp2.get("del_livre", "")
        if _del_livre != "":
            try:
                i_del = int(_del_livre)
                if 0 <= i_del < len(st.session_state.treino_livre_exs):
                    st.session_state.treino_livre_exs.pop(i_del)
                st.query_params.clear(); st.rerun()
            except: st.query_params.clear()

        with st.form("form_livre"):
            tl_nome   = st.text_input("Exercício", placeholder="Ex: Agachamento")
            c_kg, c_s, c_r = st.columns(3)
            tl_peso   = c_kg.number_input("Kg",     value=0, min_value=0)
            tl_series = c_s.number_input("Séries",  value=3, min_value=1)
            tl_reps   = c_r.number_input("Reps",    value=12, min_value=1)
            tl_nota   = st.text_input("Nota (opcional)", placeholder="Observações...")
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if tl_nome.strip():
                    st.session_state.treino_livre_exs.append({
                        "nome": tl_nome.strip(), "peso": tl_peso,
                        "series": tl_series, "reps": tl_reps, "nota": tl_nota.strip(),
                    })
                    st.rerun()

        if st.session_state.treino_livre_exs:
            st.caption(str(len(st.session_state.treino_livre_exs)) + " exercício(s)")
            for i, ex in enumerate(st.session_state.treino_livre_exs):
                nota_txt = f"<div style='font-size:0.82rem;color:#c8cdd5;margin-top:2px'>{ex['nota']}</div>" if ex.get("nota") else ""
                st.markdown(f"""
<div style="background:#1a237e22;border:1px solid #3949ab55;border-radius:10px;padding:10px 14px;margin-bottom:6px;position:relative">
  <a href="?del_livre={i}" style="position:absolute;top:8px;right:10px;color:#9ca3b0;font-size:1.1rem;text-decoration:none">✕</a>
  <div style="font-size:0.9rem;font-weight:700;color:#90caf9;padding-right:24px">{i+1}. {ex['nome']}</div>
  <div style="font-size:0.88rem;color:#c8cdd5">{ex['series']}×{ex['reps']} · {ex['peso']} kg</div>
  {nota_txt}
</div>""", unsafe_allow_html=True)

            st.write("")
            if st.button("✅ Salvar treino livre", use_container_width=True):
                for ex in st.session_state.treino_livre_exs:
                    det = f"{ex['peso']}kg | {ex['series']}x{ex['reps']}"
                    if ex.get("nota"):
                        det += f" | {ex['nota']}"
                    _registrar(None, det, tipo="musculacao")
                st.session_state.treino_livre_exs = []
                st.success("✅ Treino salvo!")
                st.balloons()
        else:
            st.caption("Nenhum exercício adicionado ainda.")

    # ── Treino por Série ──────────────────────────────────────────────────────
    else:
        if not st.session_state.treino_ativo:
            serie = st.radio("Série", ["A", "B", "C", "D"], horizontal=True, label_visibility="collapsed")
            exs   = supabase.table("exercicios").select("id,nome,series,repeticoes,peso_kg")\
                .eq("serie_tipo", serie).eq("user_id", uid()).order("id").execute()

            # Delete via session_state (sem navegar pra nova URL)
            if st.session_state.get("del_ex_pending"):
                supabase.table("exercicios").delete().eq("id", st.session_state.del_ex_pending).execute()
                st.session_state.del_ex_pending = None
                st.rerun()

            if exs.data:
                n_exs = len(exs.data)
                nomes_resumo = " · ".join(e["nome"] for e in exs.data[:3])
                if n_exs > 3: nomes_resumo += f" +{n_exs-3}"

                # Botão iniciar ANTES da lista
                if st.button(f"🚀 Iniciar Série {serie} — {n_exs} exercícios", use_container_width=True):
                    st.session_state.treino_ativo = True
                    st.session_state.serie_atual  = serie
                    st.session_state.indice_ex    = 0
                    st.session_state.inicio_timer = time.time()
                    st.session_state.timer_descanso_ativo = False
                    st.session_state.ordem_exercicios = [e["id"] for e in exs.data]
                    st.rerun()

                with st.expander(f"👁 Ver {n_exs} exercícios da Série {serie}", expanded=False):
                    for i, ex in enumerate(exs.data, 1):
                        ult_det, ult_data = _ultima_carga(ex["id"])
                        ult_txt = f"<div style='font-size:0.72rem;color:#a78bfa;margin-top:3px'>📌 {ult_data}: {ult_det}</div>" if ult_det else ""
                        c_card, c_del = st.columns([10, 1])
                        with c_card:
                            st.markdown(f"""
<div style="background:#1a237e22;border:1px solid #3949ab55;border-radius:10px;padding:8px 12px;margin-bottom:2px">
  <div style="font-size:0.9rem;font-weight:700;color:#90caf9">{i}. {ex['nome']}</div>
  <div style="font-size:0.85rem;color:#c8cdd5;margin-top:1px">{ex['series']}×{ex['repeticoes']} · {ex['peso_kg']} kg</div>
  {ult_txt}
</div>""", unsafe_allow_html=True)
                        with c_del:
                            st.write("")
                            if st.button("✕", key=f"del_{ex['id']}", use_container_width=True):
                                st.session_state.del_ex_pending = ex["id"]
                                st.rerun()
                pode_iniciar = True
            else:
                st.caption("SÉRIE " + serie + "  ·  VAZIA")
                pode_iniciar = False

            with st.expander("＋ Adicionar exercício — Série " + serie, expanded=not pode_iniciar):
                with st.form("form_add_" + serie + "_" + str(st.session_state.get("n_adds", 0))):
                    r_nome = st.text_input("Nome do exercício", placeholder="Ex: Supino Reto")
                    c1, c2, c3 = st.columns(3)
                    r_peso   = c1.number_input("Peso (kg)", value=0, min_value=0)
                    r_series = c2.number_input("Séries",    value=3, min_value=1)
                    r_reps   = c3.number_input("Reps",      value=12, min_value=1)
                    if st.form_submit_button("Adicionar exercício", use_container_width=True):
                        if r_nome.strip():
                            dup = supabase.table("exercicios").select("id")\
                                .ilike("nome", r_nome.strip()).eq("serie_tipo", serie)\
                                .eq("user_id", uid()).execute()
                            if dup.data:
                                st.warning("'" + r_nome + "' já existe na Série " + serie)
                            else:
                                try:
                                    supabase.table("exercicios").insert({
                                        "user_id":    uid(), "nome": r_nome.strip(),
                                        "serie_tipo": serie, "peso_kg": r_peso,
                                        "series":     r_series, "repeticoes": r_reps,
                                    }).execute()
                                    st.session_state.n_adds = st.session_state.get("n_adds", 0) + 1
                                    st.success("✅ '" + r_nome + "' adicionado!")
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erro ao adicionar: " + str(e))
                        else:
                            st.warning("Digite o nome do exercício.")



            # 4. Clonar (por último)
            with st.expander("📋 Clonar esta série em outra"):
                outras = [s for s in ["A","B","C","D"] if s != serie]
                dest = st.selectbox("Clonar Série " + serie + " para →", outras, key="clone_dest")
                if st.button("Clonar", key="btn_clone"):
                    if exs.data:
                        for ex in exs.data:
                            dup = supabase.table("exercicios").select("id")\
                                .ilike("nome", ex["nome"]).eq("serie_tipo", dest)\
                                .eq("user_id", uid()).execute()
                            if not dup.data:
                                supabase.table("exercicios").insert({
                                    "user_id":    uid(), "nome": ex["nome"],
                                    "serie_tipo": dest,  "peso_kg": ex["peso_kg"],
                                    "series":     ex["series"], "repeticoes": ex["repeticoes"],
                                }).execute()
                        st.success(f"✅ Série {serie} clonada para Série {dest}!")
                        st.rerun()
                    else:
                        st.warning("Série vazia, nada a clonar.")

        else:
            # Busca todos e reordena conforme ordem_exercicios (permite pular)
            _res_todos = supabase.table("exercicios").select("*").eq("serie_tipo", st.session_state.serie_atual).eq("user_id", uid()).order("id").execute()

            if not _res_todos.data:
                st.warning("Nenhum exercício nesta série.")
                if st.button("Voltar"):
                    st.session_state.treino_ativo = False; st.rerun()
            else:
                _ex_map  = {e["id"]: e for e in _res_todos.data}
                ordem    = st.session_state.get("ordem_exercicios") or [e["id"] for e in _res_todos.data]
                res_data = [_ex_map[i] for i in ordem if i in _ex_map]

                total = len(res_data)
                idx   = st.session_state.indice_ex

                if idx >= total:
                    try:
                        hist_all = supabase.table("historico_treinos").select("data_execucao")\
                            .eq("user_id", uid()).execute()
                        df_all = pd.json_normalize(hist_all.data) if hist_all.data else pd.DataFrame()
                        if not df_all.empty:
                            df_all["data_execucao"] = pd.to_datetime(df_all["data_execucao"])
                        verificar_conquistas_treino(
                            supabase, uid(), fuso,
                            len(df_all), calcular_streak(df_all, hoje_agora.date())
                        )
                    except Exception:
                        pass
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.success("🎉 Treino concluído! Você arrasou hoje!")
                    st.info("💜 " + random.choice(FRASES))
                    st.rerun()

                ex  = res_data[idx]
                pct = int((idx / total) * 100)
                elapsed = int(time.time() - st.session_state.inicio_timer)
                m_e, sg = divmod(elapsed, 60)

                # Inicializa valores editáveis no session_state
                pk = f"val_p_{idx}"; sk = f"val_s_{idx}"; rk = f"val_r_{idx}"
                if pk not in st.session_state: st.session_state[pk] = int(ex["peso_kg"])
                if sk not in st.session_state: st.session_state[sk] = int(ex["series"])
                if rk not in st.session_state: st.session_state[rk] = int(ex["repeticoes"])
                p = st.session_state[pk]
                s = st.session_state[sk]
                r = st.session_state[rk]

                ult_det, ult_data = _ultima_carga(ex["id"])

                # ── Card + controles em HTML puro ─────────────────────────
                ult_txt = f"📌 {ult_data}: {ult_det}" if ult_det else ""

                # Lê ações de query params (vindas dos botões HTML)
                qp = st.query_params
                acao = qp.get("acao", "")
                if acao == "mp": st.session_state[pk] = max(0, p-1); st.query_params.clear(); st.rerun()
                if acao == "pp": st.session_state[pk] = p+1;         st.query_params.clear(); st.rerun()
                if acao == "ms": st.session_state[sk] = max(1, s-1); st.query_params.clear(); st.rerun()
                if acao == "ps": st.session_state[sk] = s+1;         st.query_params.clear(); st.rerun()
                if acao == "mr": st.session_state[rk] = max(1, r-1); st.query_params.clear(); st.rerun()
                if acao == "pr": st.session_state[rk] = r+1;         st.query_params.clear(); st.rerun()
                if acao == "r30": st.session_state.timer_descanso=30;  st.session_state.timer_descanso_inicio=time.time(); st.session_state.timer_descanso_ativo=True;  st.query_params.clear(); st.rerun()
                if acao == "r60": st.session_state.timer_descanso=60;  st.session_state.timer_descanso_inicio=time.time(); st.session_state.timer_descanso_ativo=True;  st.query_params.clear(); st.rerun()
                if acao == "pular":
                    nova_ordem = [eid for eid in ordem if eid != ex["id"]] + [ex["id"]]
                    st.session_state.ordem_exercicios = nova_ordem; st.query_params.clear(); st.rerun()
                if acao == "proximo":
                    st.query_params.clear()
                    is_pr = _verificar_pr(ex["id"], p)
                    det   = str(p) + "kg | " + str(s) + "x" + str(r) + " | " + str(elapsed//60) + "min"
                    _nota_qp = st.session_state.get("nota_" + str(idx), "")
                    if _nota_qp: det += " | " + _nota_qp
                    if is_pr:
                        det += " | 🏆 PR"; _desbloquear("pr_primeiro")
                        st.success("🏆 NOVO RECORDE PESSOAL!")
                    _registrar(ex["id"], det)
                    supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex["id"]).execute()
                    st.session_state.indice_ex += 1
                    st.session_state.timer_descanso_ativo = False
                    st.rerun()

                btn = (
                    "display:inline-flex;align-items:center;justify-content:center;"
                    "width:52px;height:52px;border-radius:10px;background:#2a2a3e;"
                    "color:#fff;font-size:1.6rem;font-weight:bold;text-decoration:none;"
                    "border:1px solid #444;cursor:pointer"
                )
                val_box = (
                    "flex:1;text-align:center;padding:4px 0"
                )
                row = "display:flex;align-items:center;gap:10px;margin:6px 0"

                st.markdown(f"""
<div style="background:#1a1a2e;border-radius:14px;padding:14px;margin-bottom:6px">
  <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#b0b8c8;margin-bottom:6px">
    <span>SÉRIE {st.session_state.serie_atual} · {idx+1}/{total}</span>
    <span>⏱ {m_e:02d}:{sg:02d}</span>
  </div>
  <div style="height:4px;background:#333;border-radius:2px;margin-bottom:10px">
    <div style="height:4px;background:#7c3aed;border-radius:2px;width:{pct}%"></div>
  </div>
  <div style="font-size:1.1rem;font-weight:700;margin-bottom:2px">💪 {ex["nome"]}</div>
  <div style="font-size:0.82rem;color:#c8cdd5;margin-bottom:12px">{ult_txt}</div>

  <div style="{row}">
    <a href="?acao=mp" style="{btn}">−</a>
    <div style="{val_box}">
      <div style="font-size:0.72rem;color:#b0b8c8;letter-spacing:1px">PESO kg</div>
      <div style="font-size:2rem;font-weight:900;line-height:2rem">{p}</div>
    </div>
    <a href="?acao=pp" style="{btn}">+</a>
  </div>

  <div style="{row}">
    <a href="?acao=ms" style="{btn}">−</a>
    <div style="{val_box}">
      <div style="font-size:0.72rem;color:#b0b8c8;letter-spacing:1px">SÉRIES</div>
      <div style="font-size:2rem;font-weight:900;line-height:2rem">{s}</div>
    </div>
    <a href="?acao=ps" style="{btn}">+</a>
  </div>

  <div style="{row}">
    <a href="?acao=mr" style="{btn}">−</a>
    <div style="{val_box}">
      <div style="font-size:0.72rem;color:#b0b8c8;letter-spacing:1px">REPS</div>
      <div style="font-size:2rem;font-weight:900;line-height:2rem">{r}</div>
    </div>
    <a href="?acao=pr" style="{btn}">+</a>
  </div>
</div>""", unsafe_allow_html=True)

                nota_ex = st.text_input("📝 Nota", placeholder="Observação...", key="nota_" + str(idx), label_visibility="collapsed")

                # ── Timer + Pular (HTML puro) ─────────────────────────────────
                if st.session_state.timer_descanso_ativo:
                    decorrido = int(time.time() - st.session_state.timer_descanso_inicio)
                    restante  = st.session_state.timer_descanso - decorrido
                    if restante <= 0:
                        st.session_state.timer_descanso_ativo = False
                        restante = 0
                    mr2, sr2 = divmod(max(restante,0), 60)
                    pct_rest  = 1 - restante / st.session_state.timer_descanso if st.session_state.timer_descanso > 0 else 1
                    timer_txt = f"⏳ {mr2:02d}:{sr2:02d}" if restante > 0 else "✅ Bora!"
                    timer_color = "#a78bfa" if restante > 0 else "#4ade80"
                    timer_bar = f'''<div style="height:4px;background:#333;border-radius:2px;margin:6px 0">
                      <div style="height:4px;background:{timer_color};border-radius:2px;width:{int(pct_rest*100)}%"></div></div>
                      <div style="text-align:center;font-size:1.5rem;font-weight:bold;color:{timer_color};margin-bottom:6px">{timer_txt}</div>'''
                else:
                    timer_bar = ""

                circle = (
                    "display:inline-flex;align-items:center;justify-content:center;"
                    "width:56px;height:56px;border-radius:50%;background:#2a2a3e;"
                    "color:#fff;font-size:0.8rem;font-weight:bold;text-decoration:none;"
                    "border:2px solid #7c3aed;cursor:pointer;margin:0 4px"
                )
                btn_pular = (
                    "display:inline-flex;align-items:center;justify-content:center;"
                    "height:42px;padding:0 16px;border-radius:10px;background:#2a2a3e;"
                    "color:#c8cdd5;font-size:0.92rem;text-decoration:none;"
                    "border:1px solid #444;cursor:pointer"
                )
                btn_prox = (
                    "display:inline-flex;align-items:center;justify-content:center;"
                    "flex:1;height:52px;border-radius:12px;background:#7c3aed;"
                    "color:#fff;font-size:1rem;font-weight:bold;text-decoration:none;"
                    "border:none;cursor:pointer;margin-left:8px"
                )

                st.markdown(f"""
<div style="margin-top:8px">
  {timer_bar}
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
    <span style="font-size:0.75rem;color:#b0b8c8;letter-spacing:1px">DESCANSO</span>
    <div>
      <a href="?acao=r30" style="{circle}">30s</a>
      <a href="?acao=r60" style="{circle}">60s</a>
    </div>
  </div>
  <div style="display:flex;align-items:center">
    <a href="?acao=pular" style="{btn_pular}">⏭ Pular</a>
    <a href="?acao=proximo" style="{btn_prox}">✅ Próximo →</a>
  </div>
</div>""", unsafe_allow_html=True)

                # Cancela via botão Streamlit pequeno
                if st.button("✕ Cancelar treino", key=f"cancel_{idx}"):
                    st.session_state.treino_ativo = False; st.rerun()



    rodape()

# ═══════════════════════════════
# ABA 2 — CARDIO
# ═══════════════════════════════

if aba2.ativa:
    if not st.session_state.cardio_ativo:
        st.info("🏃 " + _frase("cardio"))

        try:
            ini_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0)
            res_sem = supabase.table("historico_treinos").select("detalhes")\
                .eq("user_id", uid()).gte("data_execucao", ini_sem.isoformat()).execute()
            df_sem_c = pd.json_normalize(res_sem.data) if res_sem.data else pd.DataFrame()
            km_sem, _, _ = extrair_stats(df_sem_c)
        except Exception:
            km_sem = 0.0

        with st.expander("🎯 Meta semanal de distância"):
            meta_km  = st.number_input("Meta em km por semana", value=20.0, step=1.0, min_value=1.0, key="meta_cardio")
            pct_meta = min(int((km_sem / meta_km) * 100), 100)
            st.progress(pct_meta)
            st.caption(f"{round(km_sem,1)} km de {meta_km} km esta semana ({pct_meta}%)")
            if pct_meta >= 100:
                st.success("🎉 Meta semanal batida! Incrível!")

        st.caption("CONFIGURAR ESTEIRA")
        modo = st.radio("Modo", ["Distância (km)", "Número de ciclos"], horizontal=True, label_visibility="collapsed")

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Min. Andando",         value=5.0, step=1.0)
        v_anda  = c1.number_input("Vel. Andando (km/h)",  value=5.0, step=0.5)
        t_corre = c2.number_input("Min. Correndo",         value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo (km/h)", value=9.0, step=0.5)

        dist_ciclo_val = distancia_ciclo(t_anda, v_anda, t_corre, v_corre)
        if dist_ciclo_val <= 0:
            st.warning("Verifique velocidades e tempos.")
            st.stop()

        if modo == "Distância (km)":
            dist_alvo = st.number_input("Meta em km", value=5.0, step=0.5, min_value=0.1)
            n_ciclos  = max(1, round(dist_alvo / dist_ciclo_val))
        else:
            n_ciclos  = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo_val * n_ciclos

        km_est  = dist_ciclo_val * n_ciclos
        min_est = int(n_ciclos * (t_anda + t_corre))
        st.caption(f"📊 {n_ciclos} ciclos · ~{round(km_est, 2)} km · ~{fmt_tempo(min_est)}")
        if st.button("🏃  Iniciar cardio", use_container_width=True):
            etapas = gerar_etapas(n_ciclos, t_anda, v_anda, t_corre, v_corre)
            st.session_state.update({
                "cardio_ativo":  True,
                "cardio_salvo":  False,
                "dist_real":     0.0,
                "t_cardio_start": time.time(),
                "params_cardio": {
                    "etapas":    etapas,
                    "dist_alvo": dist_alvo,
                    "etapa_idx": 0,
                    "etapa_start": time.time(),
                },
            })
            st.rerun()

    else:
        p  = st.session_state.params_cardio
        da = p["dist_alvo"]

        # Flag via callback — garante que o clique é capturado mesmo durante sleep
        def _cb_encerrar():
            st.session_state._encerrar_cardio = True

        st.button("⏹  Encerrar e salvar", use_container_width=True,
                  on_click=_cb_encerrar, key="btn_encerrar_cardio")

        if st.session_state.get("_encerrar_cardio"):
            st.session_state._encerrar_cardio = False
            if not st.session_state.cardio_salvo:
                tf     = int((time.time() - st.session_state.t_cardio_start) / 60)
                dist_r = round(st.session_state.dist_real, 2)
                _registrar(None, f"Interrompido: {dist_r}km | {tf}min", tipo="cardio")
                st.session_state.cardio_salvo = True
                if dist_r >= 5:  _desbloquear("cardio_5km")
                if dist_r >= 10: _desbloquear("cardio_10km")
            st.session_state.cardio_ativo = False
            st.rerun()

        # ── Timer baseado em tempo real ────────────────────────────────────────
        estado = calcular_estado_cardio(p)
        st.session_state.params_cardio = estado["params"]
        st.session_state.dist_real     = estado["dist_real"]

        if estado["concluido"]:
            if not st.session_state.cardio_salvo:
                tf     = int((time.time() - st.session_state.t_cardio_start) / 60)
                dist_r = round(estado["dist_real"], 2)
                _registrar(None, f"Concluído: {dist_r}km | {tf}min", tipo="cardio")
                st.session_state.cardio_salvo = True
                if dist_r >= 5:  _desbloquear("cardio_5km")
                if dist_r >= 10: _desbloquear("cardio_10km")
            st.session_state.cardio_ativo = False
            st.balloons()
            st.success("🎉 Cardio concluído! Você foi incrível!")
            st.info("💜 " + random.choice(FRASES))
            st.rerun()

        pct = int((estado["dist_real"] / da) * 100) if da > 0 else 0

        st.subheader("🏃 " + estado["nome_etapa"])
        st.progress(min(pct, 100))
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("⏱ Restante",  fmt_mm_ss(estado["seg_restantes"]))
        c2.metric("📍 Distância", f"{round(estado['dist_real'], 2)} / {round(da, 2)} km")
        st.divider()

        time.sleep(1)
        st.rerun()

    rodape()

# ═══════════════════════════════
# ABA 3 — PAINEL
# ═══════════════════════════════

if aba3.ativa:
    st.info("📊 " + _frase("painel"))
    try:
        res_h = buscar_historico_completo(supabase, uid())

        if not res_h.data:
            st.info("📭 Nenhum treino registrado ainda. Bora começar!")
        else:
            df = pd.json_normalize(res_h.data)
            df["data_execucao"] = pd.to_datetime(df["data_execucao"]).dt.tz_convert("America/Sao_Paulo")

            ini_sem_atual = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0)
            ini_sem_ant = ini_sem_atual - timedelta(weeks=1)

            df_sem_atual = df[df["data_execucao"] >= ini_sem_atual]
            df_sem_ant   = df[(df["data_execucao"] >= ini_sem_ant) & (df["data_execucao"] < ini_sem_atual)]

            km_a,  min_a,  kg_a   = extrair_stats(df_sem_atual)
            km_ant, min_ant, kg_ant = extrair_stats(df_sem_ant)

            meses_n = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
                       7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}

            data_min = df["data_execucao"].dt.date.min()
            data_max = df["data_execucao"].dt.date.max()

            so_hoje = st.checkbox("📅 Ver apenas hoje", value=False)

            if not so_hoje:
                modo_filtro = st.radio("Filtrar por", ["Mês", "Por período"],
                                       horizontal=True, label_visibility="collapsed")
            else:
                modo_filtro = None

            if so_hoje:
                ini_sel = fim_sel = hoje_agora.date()
                fim_dt  = datetime.combine(fim_sel, datetime.max.time()).replace(tzinfo=fuso)
                ini_dt  = datetime.combine(ini_sel, datetime.min.time()).replace(tzinfo=fuso)
                df_f    = df[(df["data_execucao"] >= ini_dt) & (df["data_execucao"] <= fim_dt)]
                titulo_resumo = "RESUMO — HOJE, " + hoje_agora.strftime("%d/%m/%Y")

            elif modo_filtro == "Mês":
                anos    = sorted(df["data_execucao"].dt.year.unique(), reverse=True)
                c1, c2  = st.columns(2)
                ano_sel = c1.selectbox("Ano", anos)
                meses_d = sorted(df[df["data_execucao"].dt.year==ano_sel]["data_execucao"].dt.month.unique(), reverse=True)
                mes_sel = c2.selectbox("Mês", meses_d, format_func=lambda x: meses_n[x])
                df_f    = df[(df["data_execucao"].dt.month==mes_sel) & (df["data_execucao"].dt.year==ano_sel)]
                titulo_resumo = "RESUMO — " + meses_n[mes_sel].upper()

            else:
                c1, c2      = st.columns(2)
                ini_default = max(data_min, data_max - timedelta(days=6))
                ini_sel     = c1.date_input("De",   value=ini_default, min_value=data_min, max_value=data_max, key="dt_ini")
                fim_sel     = c2.date_input("Até",  value=data_max,    min_value=data_min, max_value=data_max, key="dt_fim")
                if ini_sel > fim_sel:
                    st.warning("A data inicial deve ser anterior à final.")
                    ini_sel = fim_sel
                fim_dt = datetime.combine(fim_sel, datetime.max.time()).replace(tzinfo=fuso)
                ini_dt = datetime.combine(ini_sel, datetime.min.time()).replace(tzinfo=fuso)
                df_f   = df[(df["data_execucao"] >= ini_dt) & (df["data_execucao"] <= fim_dt)]
                titulo_resumo = "RESUMO — " + (ini_sel.strftime("%d/%m/%Y") if ini_sel == fim_sel
                                               else ini_sel.strftime("%d/%m") + " a " + fim_sel.strftime("%d/%m/%Y"))

            km_f, min_f, kg_f = extrair_stats(df_f)

            st.caption(titulo_resumo)
            st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0">
  <div style="background:#1a1a2e;border-radius:10px;padding:10px;text-align:center">
    <div style="font-size:0.75rem;color:#b0b8c8">🏋️ ATIVIDADES</div>
    <div style="font-size:1.4rem;font-weight:bold">{len(df_f)}</div>
  </div>
  <div style="background:#1a1a2e;border-radius:10px;padding:10px;text-align:center">
    <div style="font-size:0.75rem;color:#b0b8c8">💪 VOLUME</div>
    <div style="font-size:1.4rem;font-weight:bold">{kg_f:,.0f} kg</div>
  </div>
  <div style="background:#1a1a2e;border-radius:10px;padding:10px;text-align:center">
    <div style="font-size:0.75rem;color:#b0b8c8">⏱ TEMPO</div>
    <div style="font-size:1.4rem;font-weight:bold">{fmt_tempo(min_f)}</div>
  </div>
  <div style="background:#1a1a2e;border-radius:10px;padding:10px;text-align:center">
    <div style="font-size:0.75rem;color:#b0b8c8">🛣️ DISTÂNCIA</div>
    <div style="font-size:1.4rem;font-weight:bold">{round(km_f,1)} km</div>
  </div>
</div>""", unsafe_allow_html=True)

            if kg_ant == 0 and km_ant == 0 and min_ant == 0:
                st.info("📅 Sem dados da semana passada para comparar ainda. Bora criar um histórico! 💪")
            else:
                partes = []
                if kg_ant > 0:
                    diff_kg = kg_ant - kg_a
                    if diff_kg > 0:    partes.append(f"**{diff_kg:,.0f} kg** de volume de treino")
                    elif diff_kg < 0:  partes.append(f"~~peso~~ já superou em **{abs(diff_kg):,.0f} kg** 🔥")
                if min_ant > 0:
                    diff_min = min_ant - min_a
                    if diff_min > 0:   partes.append(f"**{fmt_tempo(diff_min)}** de tempo ativo")
                    elif diff_min < 0: partes.append(f"~~tempo~~ já superou em **{fmt_tempo(abs(diff_min))}** 🔥")
                if km_ant > 0:
                    diff_km = round(km_ant - km_a, 1)
                    if diff_km > 0:    partes.append(f"**{diff_km} km** de distância")
                    elif diff_km < 0:  partes.append(f"~~distância~~ já superou em **{abs(diff_km)} km** 🔥")

                faltam  = [p for p in partes if not p.startswith("~~")]
                superou = [p for p in partes if p.startswith("~~")]
                if not faltam and not superou:
                    st.success("🏆 Semana igualada! Agora é superar!")
                elif not faltam:
                    st.success("🏆 Você superou a semana passada em tudo! Incrível!")
                else:
                    msg = "💡 Ainda falta " + ", ".join(faltam) + " pra se equiparar à semana passada."
                    if superou:
                        msg += " Mas " + ", ".join(s.replace("~~", "") for s in superou) + "!"
                    st.warning(msg)

            st.caption("ATIVIDADES — " + titulo_resumo.replace("RESUMO — ", ""))
            if df_f.empty:
                st.info("Nenhum registro neste período.")
            else:
                df_show = df_f.copy()
                if "exercicios.nome" not in df_show.columns:
                    df_show["exercicios.nome"] = "Cardio"
                df_show["exercicios.nome"] = df_show["exercicios.nome"].fillna("Cardio")
                df_show["Data"] = df_show["data_execucao"].dt.strftime("%d/%m %H:%M")
                st.dataframe(df_show[["Data","exercicios.nome","detalhes"]].rename(
                    columns={"exercicios.nome":"Exercício","detalhes":"Detalhes"}),
                    use_container_width=True, hide_index=True)

                csv = df_show[["Data","exercicios.nome","detalhes"]].rename(
                    columns={"exercicios.nome":"Exercício","detalhes":"Detalhes"}
                ).to_csv(index=False).encode("utf-8")
                st.download_button("📥 Exportar CSV", csv,
                    file_name="pytrain_historico.csv", mime="text/csv", use_container_width=True)

            st.write("")
            if st.button("🗑️  Apagar histórico completo", use_container_width=True):
                st.session_state["confirmar_historico"] = True
            if st.session_state.get("confirmar_historico"):
                st.error("⚠️ Esta ação apaga todo o histórico permanentemente.")
                c1, c2 = st.columns(2)
                if c1.button("Sim, apagar tudo"):
                    supabase.table("historico_treinos").delete().eq("user_id", uid()).execute()
                    st.session_state["confirmar_historico"] = False
                    st.success("Histórico apagado."); st.rerun()
                if c2.button("Cancelar"):
                    st.session_state["confirmar_historico"] = False; st.rerun()

    except Exception as e:
        st.error("Erro: " + str(e))

    rodape()

# ═══════════════════════════════
# ABA 4 — EVOLUÇÃO
# ═══════════════════════════════

if aba4.ativa:
    st.info("📈 " + _frase("evolucao"))

    sub1, sub2, sub3 = st.tabs(["🏋️ Progressão por exercício", "⚖️ Peso corporal", "📏 Medidas"])

    with sub1:
        try:
            exs_todos = supabase.table("exercicios").select("id,nome,serie_tipo")\
                .eq("user_id", uid()).order("nome").execute()
            if not exs_todos.data:
                st.info("Nenhum exercício cadastrado ainda.")
            else:
                nomes_ex   = [f"{e['nome']} (Série {e['serie_tipo']})" for e in exs_todos.data]
                sel        = st.selectbox("Escolha o exercício", nomes_ex)
                ex_id_sel  = exs_todos.data[nomes_ex.index(sel)]["id"]

                hist_ex = supabase.table("historico_treinos").select("data_execucao,detalhes")\
                    .eq("user_id", uid()).eq("exercicio_id", ex_id_sel)\
                    .order("data_execucao").execute()

                if not hist_ex.data:
                    st.info("Nenhum registro para este exercício ainda.")
                else:
                    rows = []
                    for h in hist_ex.data:
                        m_kg = _re.search(r"([\d.]+)kg", str(h.get("detalhes", "")))
                        if m_kg:
                            rows.append({
                                "Data":     pd.to_datetime(h["data_execucao"]).astimezone(fuso).strftime("%d/%m/%y"),
                                "Peso (kg)": float(m_kg.group(1)),
                                "PR":        "🏆" if "PR" in str(h.get("detalhes","")) else "",
                            })
                    if rows:
                        df_ex  = pd.DataFrame(rows)
                        st.line_chart(df_ex.set_index("Data")["Peso (kg)"], use_container_width=True)
                        pr_max = df_ex["Peso (kg)"].max()
                        st.caption(f"🏆 Recorde pessoal: **{pr_max} kg**  ·  {len(df_ex)} registros")
                        st.dataframe(df_ex, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error("Erro: " + str(e))

    with sub2:
        try:
            with st.form("form_peso"):
                c1, c2    = st.columns(2)
                peso_val  = c1.number_input("Peso (kg)", value=60.0, step=0.1, min_value=20.0, max_value=300.0)
                peso_data = c2.date_input("Data", value=hoje_agora.date())
                peso_obs  = st.text_input("Observação (opcional)", placeholder="Em jejum, após treino...")
                if st.form_submit_button("Registrar peso", use_container_width=True):
                    supabase.table("peso_corporal").insert({
                        "user_id":     uid(), "peso_kg": peso_val,
                        "data":        peso_data.isoformat(),
                        "observacao":  peso_obs.strip() or None,
                    }).execute()
                    _desbloquear("peso_registrado")
                    st.success("✅ Peso registrado!"); st.rerun()

            res_peso = supabase.table("peso_corporal").select("*")\
                .eq("user_id", uid()).order("data").execute()

            if res_peso.data:
                df_peso      = pd.DataFrame(res_peso.data)
                df_peso["data"] = pd.to_datetime(df_peso["data"])
                df_peso_plot = df_peso.copy()
                df_peso_plot.index = df_peso_plot["data"].dt.strftime("%d/%m/%y")
                st.line_chart(df_peso_plot["peso_kg"], use_container_width=True)

                primeiro = df_peso["peso_kg"].iloc[0]
                ultimo   = df_peso["peso_kg"].iloc[-1]
                diff_p   = round(ultimo - primeiro, 1)
                sinal    = "+" if diff_p > 0 else ""
                c1, c2, c3 = st.columns(3)
                c1.metric("⚖️ Atual",    f"{ultimo} kg")
                c2.metric("📉 Mínimo",   f"{df_peso['peso_kg'].min()} kg")
                c3.metric("📈 Variação", f"{sinal}{diff_p} kg")

                st.caption("Registros")
                for _, row in df_peso.iloc[::-1].iterrows():
                    c_data, c_peso, c_obs, c_del = st.columns([2, 1.5, 3, 0.7])
                    c_data.write(row["data"].strftime("%d/%m/%Y"))
                    c_peso.write(f"{row['peso_kg']} kg")
                    c_obs.write(row["observacao"] or "—")
                    if c_del.button("✕", key=f"del_peso_{row['id']}", help="Apagar registro"):
                        supabase.table("peso_corporal").delete().eq("id", row["id"]).execute()
                        st.rerun()
            else:
                st.info("Nenhum registro de peso ainda.")
        except Exception as e:
            st.error("Erro: " + str(e))

    with sub3:
        MEDIDAS = [
            ("cintura_cm",     "Cintura (cm)"),
            ("quadril_cm",     "Quadril (cm)"),
            ("busto_cm",       "Busto (cm)"),
            ("braco_d_cm",     "Braço D (cm)"),
            ("braco_e_cm",     "Braço E (cm)"),
            ("coxa_d_cm",      "Coxa D (cm)"),
            ("coxa_e_cm",      "Coxa E (cm)"),
            ("panturrilha_cm", "Panturrilha (cm)"),
            ("pescoco_cm",     "Pescoço (cm)"),
        ]
        try:
            with st.form("form_medidas"):
                st.caption("Preencha apenas as medidas que deseja registrar.")
                data_med  = st.date_input("Data da medição", value=hoje_agora.date())
                cols_med  = st.columns(3)
                vals_med  = {}
                for i, (campo, label) in enumerate(MEDIDAS):
                    vals_med[campo] = cols_med[i % 3].number_input(label, value=0.0, step=0.5, min_value=0.0)
                obs_med = st.text_input("Observação (opcional)")
                if st.form_submit_button("Registrar medidas", use_container_width=True):
                    payload = {"user_id": uid(), "data": data_med.isoformat(),
                               "observacao": obs_med.strip() or None}
                    payload.update({k: v if v > 0 else None for k, v in vals_med.items()})
                    supabase.table("medidas_corporais").insert(payload).execute()
                    _desbloquear("medidas_registradas")
                    st.success("✅ Medidas registradas!"); st.rerun()

            res_med = supabase.table("medidas_corporais").select("*")\
                .eq("user_id", uid()).order("data").execute()

            if res_med.data:
                df_med = pd.DataFrame(res_med.data)
                df_med["data"] = pd.to_datetime(df_med["data"])

                campos_disp = [c for c, _ in MEDIDAS if c in df_med.columns and df_med[c].notna().any()]
                labels_disp = [l for c, l in MEDIDAS if c in campos_disp]
                if campos_disp:
                    campo_sel = st.selectbox("Ver evolução de", labels_disp, key="sel_medida")
                    campo_key = campos_disp[labels_disp.index(campo_sel)]
                    df_plot_m = df_med[df_med[campo_key].notna()].copy()
                    df_plot_m.index = df_plot_m["data"].dt.strftime("%d/%m/%y")
                    st.line_chart(df_plot_m[campo_key], use_container_width=True)

                colunas_show = ["data"] + [c for c, _ in MEDIDAS if c in df_med.columns]
                df_tab_m     = df_med[colunas_show].copy()
                df_tab_m["data"] = df_med["data"].dt.strftime("%d/%m/%Y")
                rename_m = {"data": "Data"}
                rename_m.update({c: l for c, l in MEDIDAS})
                st.dataframe(df_tab_m.rename(columns=rename_m).iloc[::-1],
                             use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma medida registrada ainda.")
        except Exception as e:
            st.error("Erro: " + str(e))

    rodape()

# ═══════════════════════════════
# ABA 5 — CONQUISTAS
# ═══════════════════════════════

if aba5.ativa:
    st.info("🏆 " + _frase("conquistas"))

    try:
        res_conq = supabase.table("conquistas").select("conquista_id,desbloqueada_em")\
            .eq("user_id", uid()).execute()
        desbloqueadas = {r["conquista_id"]: r["desbloqueada_em"] for r in (res_conq.data or [])}

        res_all_h = supabase.table("historico_treinos").select("data_execucao")\
            .eq("user_id", uid()).execute()
        df_all_h = pd.json_normalize(res_all_h.data) if res_all_h.data else pd.DataFrame()
        if not df_all_h.empty:
            df_all_h["data_execucao"] = pd.to_datetime(df_all_h["data_execucao"])

        streak_atual  = calcular_streak(df_all_h, hoje_agora.date())
        total_treinos = len(df_all_h)

        st.caption(f"🔥 Streak atual: **{streak_atual} dia(s)**  ·  🏋️ Total de treinos: **{total_treinos}**")
        st.divider()

        n_desbloqueadas = len(desbloqueadas)
        st.caption(f"CONQUISTAS — {n_desbloqueadas}/{len(CONQUISTAS_DEF)} desbloqueadas")

        cols_c = st.columns(3)
        for i, c in enumerate(CONQUISTAS_DEF):
            desbloq = c["id"] in desbloqueadas
            with cols_c[i % 3]:
                if desbloq:
                    data_d = pd.to_datetime(desbloqueadas[c["id"]]).astimezone(fuso).strftime("%d/%m/%Y")
                    st.success(f"{c['emoji']} **{c['nome']}**\n\n{c['desc']}\n\n_Em {data_d}_")
                else:
                    st.markdown(f"""
                    <div style="background:#13131f;border:1px solid #2d2d45;border-radius:8px;
                    padding:12px;margin-bottom:8px;opacity:0.45;filter:grayscale(1)">
                    <span style="font-size:1.4rem">🔒</span>
                    <div style="font-weight:600;color:#b0b8c8;margin-top:4px">{c['nome']}</div>
                    <div style="color:#9ca3b0;font-size:0.88rem">{c['desc']}</div>
                    </div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("🎯 Metas do mês")

        try:
            res_metas = supabase.table("metas_mensais").select("*")\
                .eq("user_id", uid())\
                .eq("mes", hoje_agora.month).eq("ano", hoje_agora.year).execute()
            meta_atual = res_metas.data[0] if res_metas.data else {}
        except Exception:
            meta_atual = {}

        with st.expander("✏️ Definir metas deste mês"):
            with st.form("form_metas"):
                c1, c2, c3 = st.columns(3)
                m_treinos = c1.number_input("Treinos",           value=int(meta_atual.get("treinos", 12)),          min_value=1)
                m_km      = c2.number_input("Distância (km)",    value=float(meta_atual.get("distancia_km", 30.0)), step=1.0)
                m_min     = c3.number_input("Tempo ativo (min)", value=int(meta_atual.get("tempo_min", 300)),        min_value=1)
                if st.form_submit_button("Salvar metas", use_container_width=True):
                    supabase.table("metas_mensais").upsert({
                        "user_id": uid(), "mes": hoje_agora.month, "ano": hoje_agora.year,
                        "treinos": m_treinos, "distancia_km": m_km, "tempo_min": m_min,
                    }).execute()
                    st.success("✅ Metas salvas!"); st.rerun()

        if meta_atual:
            ini_mes = hoje_agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            try:
                res_mes = supabase.table("historico_treinos").select("detalhes")\
                    .eq("user_id", uid()).gte("data_execucao", ini_mes.isoformat()).execute()
                df_mes = pd.json_normalize(res_mes.data) if res_mes.data else pd.DataFrame()
                km_mes, min_mes, _ = extrair_stats(df_mes)
                tr_mes = len(df_mes)
            except Exception:
                km_mes = 0.0; min_mes = 0; tr_mes = 0

            c1, c2, c3 = st.columns(3)
            pct_tr = min(int(tr_mes  / max(meta_atual.get("treinos", 1), 1) * 100), 100)
            pct_km = min(int(km_mes  / max(float(meta_atual.get("distancia_km", 1)), 0.01) * 100), 100)
            pct_mn = min(int(min_mes / max(meta_atual.get("tempo_min", 1), 1) * 100), 100)

            with c1:
                st.caption("🏋️ Treinos")
                st.progress(pct_tr)
                st.caption(f"{tr_mes} / {meta_atual.get('treinos','?')} ({pct_tr}%)")
            with c2:
                st.caption("🛣️ Distância")
                st.progress(pct_km)
                st.caption(f"{round(km_mes,1)} / {meta_atual.get('distancia_km','?')} km ({pct_km}%)")
            with c3:
                st.caption("⏱ Tempo")
                st.progress(pct_mn)
                st.caption(f"{fmt_tempo(min_mes)} / {fmt_tempo(int(meta_atual.get('tempo_min',0)))} ({pct_mn}%)")
        else:
            st.info("Defina suas metas acima para acompanhar o progresso!")

    except Exception as e:
        st.error("Erro: " + str(e))

    rodape()

# ═══════════════════════════════
# ABA 6 — PERFIL
# ═══════════════════════════════

if aba6.ativa:
    st.info("⚙️ " + _frase("perfil"))

    email_atual = st.session_state.usuario["email"]
    nome_atual  = st.session_state.usuario["nome"]

    try:
        rp = supabase.table("perfis").select("nome,telefone,cidade,estado").eq("user_id", uid()).execute()
        dp = rp.data[0] if rp.data else {}
    except Exception:
        dp = {}

    st.subheader("⚙️ Meu Perfil")
    st.markdown("""
    <style>
    .perfil-card { background:#13131f;border:1px solid #2d2d45;border-radius:10px;
        padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:10px;font-size:0.92rem; }
    .perfil-label { color:#b0b8c8;font-size:0.82rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px; }
    .perfil-valor { color:#e2e8f0;font-size:0.95rem;font-weight:500; }
    .perfil-icon  { font-size:1.2rem;flex-shrink:0; }
    </style>""", unsafe_allow_html=True)

    def card_perfil(icon, label, valor):
        st.markdown(f"""
        <div class="perfil-card">
            <span class="perfil-icon">{icon}</span>
            <div><div class="perfil-label">{label}</div>
            <div class="perfil-valor">{valor}</div></div>
        </div>""", unsafe_allow_html=True)

    card_perfil("👤", "Nome",     dp.get("nome", nome_atual))
    card_perfil("📧", "Email",    email_atual)
    card_perfil("📱", "Telefone", dp.get("telefone", "—"))
    card_perfil("📍", "Cidade",   dp.get("cidade","—") + " — " + dp.get("estado","—"))

    st.divider()

    with st.expander("✏️ Editar dados pessoais"):
        with st.form("form_dados"):
            ed_nome   = st.text_input("Nome",     value=dp.get("nome", nome_atual))
            ed_tel    = st.text_input("Telefone", value=dp.get("telefone",""), placeholder="(28) 99999-9999")
            ed_cidade = st.text_input("Cidade",   value=dp.get("cidade",""))
            ests      = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                         "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
            idx_e     = ests.index(dp.get("estado","ES")) if dp.get("estado","ES") in ests else 7
            ed_estado = st.selectbox("Estado", ests, index=idx_e)
            if st.form_submit_button("Salvar alterações", use_container_width=True):
                if ed_nome.strip() and ed_tel.strip() and ed_cidade.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": ed_nome.strip()}})
                        supabase.table("perfis").upsert({
                            "user_id":  uid(), "nome":   ed_nome.strip(),
                            "telefone": ed_tel.strip(), "cidade": ed_cidade.strip(), "estado": ed_estado,
                        }).execute()
                        st.session_state.usuario["nome"] = ed_nome.strip()
                        st.success("✅ Dados atualizados!"); st.rerun()
                    except Exception as e:
                        st.error("Erro: " + str(e))
                else:
                    st.warning("Preencha todos os campos.")

    with st.expander("📧 Alterar email"):
        st.caption("Você receberá um link de confirmação em ambos os emails.")
        with st.form("form_email"):
            novo_email  = st.text_input("Novo email", placeholder="novo@email.com")
            senha_email = st.text_input("Senha atual", type="password")
            if st.form_submit_button("Enviar confirmações", use_container_width=True):
                if not novo_email.strip() or "@" not in novo_email:
                    st.warning("Email inválido.")
                elif not senha_email:
                    st.warning("Digite sua senha.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_email})
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success("✅ Confirmações enviadas! Verifique os dois emails.")
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    with st.expander("🔒 Alterar senha"):
        with st.form("form_senha"):
            s_antiga = st.text_input("Senha atual",       type="password")
            s_nova   = st.text_input("Nova senha",         type="password", placeholder="mínimo 8 caracteres")
            s_conf   = st.text_input("Confirmar nova senha", type="password")
            if st.form_submit_button("Salvar nova senha", use_container_width=True):
                if not s_antiga:           st.warning("Digite a senha atual.")
                elif len(s_nova) < 8:      st.warning("Mínimo 8 caracteres.")
                elif s_nova != s_conf:     st.error("Senhas não coincidem.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": s_antiga})
                        supabase.auth.update_user({"password": s_nova})
                        st.success("✅ Senha alterada com sucesso!")
                    except Exception:
                        st.error("Senha atual incorreta.")

    st.divider()

    with st.expander("⚠️ Apagar minha conta"):
        st.warning("Ação irreversível. Todos os dados serão removidos permanentemente.")
        with st.form("form_del_conta"):
            conf_txt   = st.text_input("Digite APAGAR para confirmar", placeholder="APAGAR")
            senha_conf = st.text_input("Sua senha", type="password")
            if st.form_submit_button("Apagar conta permanentemente", use_container_width=True):
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
                            SUPABASE_URL + "/functions/v1/delete-account", data=b"{}",
                            headers={"Authorization": "Bearer " + token, "apikey": SUPABASE_KEY,
                                     "Content-Type": "application/json"}, method="POST",
                        )
                        with _ur.urlopen(req, context=_ssl.create_default_context(), timeout=15) as rr:
                            body = _js.loads(rr.read())
                        if body.get("success"):
                            st.success("Conta apagada. Até logo! 👋")
                            time.sleep(1)
                            fazer_logout(supabase, cookies, DEFAULTS)
                        else:
                            st.error("Erro: " + str(body.get("error", body)))
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    rodape()
