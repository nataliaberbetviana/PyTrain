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

FRASES = [
    "O único treino ruim é aquele que não aconteceu. 💜",
    "Cada rep te aproxima da melhor versão de você. 🔥",
    "Consistência bate perfeição sempre. 🏆",
    "Seu corpo consegue. É sua mente que precisa ser convencida. 💪",
    "Pequenos progressos ainda são progressos. ⚡",
    "Você não vai se arrepender de ter treinado. Promessa. 🌟",
    "A dor de hoje é a força de amanhã. 🚀",
    "Foco. Disciplina. Resultado. 🎯",
    "Mais um dia, mais um treino, mais uma conquista. ✨",
    "Você é mais forte do que imagina. Sempre. 💫",
    "Não espere motivação. Crie o hábito. 🔑",
    "Cada gota de suor é um investimento em você mesma. 💧",
    "O corpo alcança o que a mente acredita. 🧠",
    "Descanso é parte do treino. Volta amanhã mais forte. 😴",
    "Ninguém se arrepende de ter se exercitado. Nunca. 🙌",
    "Sua única competição é quem você era ontem. 📈",
    "Vai com tudo. Você merece sentir essa sensação no fim. 🎉",
    "Treinar é um presente que você dá pro seu futuro. 🎁",
    "Um passo de cada vez. O caminho se faz caminhando. 👣",
    "Força não é o que você tem. É o que você descobre quando não aguenta mais. 💎",
    "Hoje pode ser difícil. Amanhã vai valer a pena. ☀️",
    "Seu esforço não some. Ele se acumula. 📊",
    "Seja orgulhosa de cada treino. Você apareceu. Isso já é tudo. 🌸",
    "A versão mais forte de você está sendo construída agora. 🏗️",
    "Não precisa ser perfeito. Precisa ser constante. 🔄",
    "Você já fez isso antes. Você faz de novo. 💥",
    "Cada série é uma escolha por você mesma. ❤️",
    "O cansaço passa. O orgulho fica. 🥇",
    "Mais forte do que qualquer desculpa. 🚫",
    "Você não treina pra impressionar ninguém. Treina pra se sentir incrível. 🌟",
]

CONQUISTAS_DEF = [
    {"id": "primeiro_treino",   "emoji": "🌱", "nome": "Primeiro passo",      "desc": "Completou o primeiro treino"},
    {"id": "treinos_5",         "emoji": "🔥", "nome": "Pegando fogo",         "desc": "5 treinos concluídos"},
    {"id": "treinos_10",        "emoji": "💪", "nome": "Dez e contando",       "desc": "10 treinos concluídos"},
    {"id": "treinos_25",        "emoji": "⚡", "nome": "Máquina",              "desc": "25 treinos concluídos"},
    {"id": "treinos_50",        "emoji": "🚀", "nome": "Imparável",            "desc": "50 treinos concluídos"},
    {"id": "treinos_100",       "emoji": "🏆", "nome": "Lendária",             "desc": "100 treinos concluídos"},
    {"id": "streak_3",          "emoji": "📅", "nome": "3 dias seguidos",      "desc": "Treinou 3 dias consecutivos"},
    {"id": "streak_7",          "emoji": "🗓️", "nome": "Semana cheia",         "desc": "Treinou 7 dias consecutivos"},
    {"id": "streak_30",         "emoji": "🌙", "nome": "Mês invicta",          "desc": "Treinou 30 dias consecutivos"},
    {"id": "pr_primeiro",       "emoji": "🎯", "nome": "Novo recorde!",        "desc": "Bateu o primeiro PR"},
    {"id": "cardio_5km",        "emoji": "🏃", "nome": "5 km!",               "desc": "Correu 5 km em uma sessão"},
    {"id": "cardio_10km",       "emoji": "🛣️", "nome": "10 km!",              "desc": "Correu 10 km em uma sessão"},
    {"id": "peso_registrado",   "emoji": "⚖️", "nome": "Me pesando",           "desc": "Registrou o peso corporal"},
    {"id": "medidas_registradas","emoji": "📏","nome": "Me medindo",           "desc": "Registrou as medidas corporais"},
]

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Variáveis de ambiente não encontradas.")
    st.stop()

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
supabase = get_supabase()

defaults = {
    "usuario": None, "access_token": None, "refresh_token": None,
    "treino_ativo": False, "serie_atual": "A", "indice_ex": 0, "inicio_timer": 0.0,
    "timer_descanso": 0, "timer_descanso_inicio": 0.0, "timer_descanso_ativo": False,
    "cardio_ativo": False, "params_cardio": None, "dist_real": 0.0,
    "t_cardio_start": 0.0, "cardio_salvo": False,
    "confirmar_historico": False, "perfil_completo": None,
    "sessao_restaurada": False,
    "frase_idx": 0, "aba_anterior": None,
    "treino_livre_exs": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── helpers ────────────────────────────────────────────────────────────────────

def frase_aba(nome_aba: str) -> str:
    if st.session_state.aba_anterior != nome_aba:
        st.session_state.frase_idx = (st.session_state.frase_idx + 1) % len(FRASES)
        st.session_state.aba_anterior = nome_aba
    return FRASES[st.session_state.frase_idx]

def fmt_tempo(minutos: int) -> str:
    if minutos >= 60:
        h, m = divmod(minutos, 60)
        return f"{h}h {m}min" if m else f"{h}h"
    return f"{minutos}min"

import re as _re

def extrair_stats(df):
    if df.empty or "detalhes" not in df.columns:
        return 0.0, 0, 0.0
    km_total = 0.0; min_total = 0; kg_total = 0.0
    for det in df["detalhes"].dropna():
        det = str(det)
        m = _re.search(r"([\d.]+)km", det)
        if m: km_total += float(m.group(1))
        for mm in _re.findall(r"(\d+)min", det):
            min_total += int(mm)
        m_kg = _re.search(r"([\d.]+)kg", det)
        m_sets = _re.search(r"(\d+)x(\d+)", det)
        if m_kg and m_sets:
            kg_total += float(m_kg.group(1)) * int(m_sets.group(1)) * int(m_sets.group(2))
    return km_total, min_total, kg_total

def extrair_peso_total(df):
    _, _, kg = extrair_stats(df)
    return kg

def rodape():
    st.divider()
    st.caption("Dúvidas: nabevia@gmail.com")

def _cookie_get(key):
    try:
        val = cookies[key]; return val if val else ""
    except Exception: return ""

def _cookie_set(key, val):
    try: cookies[key] = val; cookies.save()
    except Exception: pass

# ── auth ───────────────────────────────────────────────────────────────────────

def fazer_login(email, senha):
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
        st.error("Email ou senha incorretos.")
        return False

def restaurar_sessao():
    if st.session_state.sessao_restaurada: return False
    st.session_state.sessao_restaurada = True
    rt = _cookie_get("rt")
    if not rt: return False
    try:
        res = supabase.auth.refresh_session(rt)
        if not res or not res.session or not res.user:
            _cookie_set("rt", ""); return False
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id": res.user.id, "email": res.user.email,
            "nome": res.user.user_metadata.get("nome", res.user.email.split("@")[0]),
        }
        _cookie_set("rt", res.session.refresh_token)
        return True
    except Exception:
        _cookie_set("rt", ""); return False

def fazer_logout():
    _cookie_set("rt", "")
    try: supabase.auth.sign_out()
    except Exception: pass
    for k in list(defaults.keys()):
        st.session_state[k] = defaults[k]
    st.rerun()

def user_id():
    return st.session_state.usuario["id"]

def verificar_perfil():
    try:
        res = supabase.table("perfis").select("telefone,cidade").eq("user_id", user_id()).execute()
        return bool(res.data and res.data[0].get("telefone") and res.data[0].get("cidade"))
    except Exception: return False

def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    supabase.table("historico_treinos").insert({
        "user_id": user_id(), "exercicio_id": ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes": detalhes, "tipo": tipo,
    }).execute()

# ── conquistas ─────────────────────────────────────────────────────────────────

def desbloquear_conquista(conquista_id: str):
    try:
        ex = supabase.table("conquistas").select("id").eq("user_id", user_id()).eq("conquista_id", conquista_id).execute()
        if not ex.data:
            supabase.table("conquistas").insert({
                "user_id": user_id(), "conquista_id": conquista_id,
                "desbloqueada_em": datetime.now(fuso).isoformat(),
            }).execute()
    except Exception: pass

def verificar_conquistas_treino(total_treinos: int, streak: int):
    if total_treinos >= 1:   desbloquear_conquista("primeiro_treino")
    if total_treinos >= 5:   desbloquear_conquista("treinos_5")
    if total_treinos >= 10:  desbloquear_conquista("treinos_10")
    if total_treinos >= 25:  desbloquear_conquista("treinos_25")
    if total_treinos >= 50:  desbloquear_conquista("treinos_50")
    if total_treinos >= 100: desbloquear_conquista("treinos_100")
    if streak >= 3:  desbloquear_conquista("streak_3")
    if streak >= 7:  desbloquear_conquista("streak_7")
    if streak >= 30: desbloquear_conquista("streak_30")

def calcular_streak(df_hist):
    if df_hist.empty: return 0
    datas = sorted(df_hist["data_execucao"].dt.date.unique(), reverse=True)
    streak = 0
    ref = hoje_agora.date()
    for d in datas:
        if d == ref or d == ref - timedelta(days=1):
            streak += 1
            ref = d
        else:
            break
    return streak

# ── PR ─────────────────────────────────────────────────────────────────────────

def verificar_pr(ex_id, peso_atual):
    try:
        res = supabase.table("historico_treinos").select("detalhes")\
            .eq("user_id", user_id()).eq("exercicio_id", ex_id).execute()
        if not res.data: return False
        max_peso = 0.0
        for row in res.data:
            m = _re.search(r"([\d.]+)kg", str(row.get("detalhes","")))
            if m: max_peso = max(max_peso, float(m.group(1)))
        return peso_atual > max_peso
    except Exception: return False

def ultima_carga(ex_id):
    try:
        res = supabase.table("historico_treinos").select("detalhes,data_execucao")\
            .eq("user_id", user_id()).eq("exercicio_id", ex_id)\
            .order("data_execucao", desc=True).limit(1).execute()
        if res.data:
            det  = res.data[0]["detalhes"]
            data = pd.to_datetime(res.data[0]["data_execucao"]).astimezone(fuso).strftime("%d/%m")
            return det, data
    except Exception: pass
    return None, None

# ═══════════════════════════════
# TELAS PRE-LOGIN
# ═══════════════════════════════

def tela_login():
    st.title("🏋️ PyTrain PRO")
    st.caption("Seu treino, sua evolução.")
    st.divider()
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_reset = st.tabs(["Entrar", "Recuperar senha"])
        with tab_login:
            with st.form("form_login"):
                email  = st.text_input("Email", placeholder="seu@email.com")
                senha  = st.text_input("Senha", type="password", placeholder="••••••••")
                entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                if email and senha:
                    with st.spinner(""):
                        if fazer_login(email, senha): st.rerun()
                else: st.warning("Preencha email e senha.")
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
                    except Exception as e: st.error("Erro: " + str(e))
                else: st.warning("Digite um email válido.")

def tela_definir_senha(access_token, refresh_token):
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.title("🏋️ Ativar conta")
        st.caption("Crie sua senha para começar.")
        with st.form("form_definir_senha"):
            nova = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            conf = st.text_input("Confirmar senha", type="password")
            ok   = st.form_submit_button("Ativar conta", use_container_width=True)
        if ok:
            if not nova or len(nova) < 8: st.warning("Mínimo 8 caracteres."); return
            if nova != conf: st.error("Senhas não coincidem."); return
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
            except Exception as e: st.error("Erro: " + str(e))

def tela_completar_perfil():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
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
                        "user_id": user_id(), "nome": nome_p.strip(),
                        "telefone": telefone.strip(), "cidade": cidade.strip(), "estado": estado,
                    }).execute()
                    st.session_state.perfil_completo = True
                    st.rerun()
                except Exception as e: st.error("Erro: " + str(e))

# ═══════════════════════════════
# FLUXO PRINCIPAL
# ═══════════════════════════════

qp = st.query_params
url_at = qp.get("access_token")
url_rt = qp.get("refresh_token")

if url_at and url_rt and not st.session_state.usuario:
    tela_definir_senha(url_at, url_rt)
    st.stop()

if not st.session_state.usuario and not st.session_state.sessao_restaurada:
    if restaurar_sessao(): st.rerun()

if not st.session_state.usuario:
    tela_login(); st.stop()

if st.session_state.perfil_completo is None:
    st.session_state.perfil_completo = verificar_perfil()

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
    r = supabase.table("historico_treinos").select("data_execucao").eq("user_id", user_id())\
        .gte("data_execucao", hoje_agora.replace(day=1,hour=0,minute=0,second=0).isoformat()).execute()
    treinos_mes = len(r.data) if r.data else 0
except Exception:
    treinos_mes = 0

if treinos_mes == 0:   msg_treinos = "Nenhum treino este mês ainda — bora começar! 💪"
elif treinos_mes < 5:  msg_treinos = str(treinos_mes) + " treino(s) este mês. Continue assim! 🔥"
elif treinos_mes < 10: msg_treinos = str(treinos_mes) + " treinos este mês. Você está em chamas! 🚀"
else:                  msg_treinos = str(treinos_mes) + " treinos este mês. Lendária! 🏆"

col_titulo, col_sair = st.columns([5, 1])
with col_titulo:
    st.subheader(emoji_hora + " " + saudacao + ", " + nome_usuario + "!")
    st.caption(msg_treinos)
with col_sair:
    if st.button("Sair", key="btn_sair", use_container_width=True):
        fazer_logout()

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "🚀 Treino", "🏃 Cardio", "📊 Painel", "📈 Evolução", "🏆 Conquistas", "⚙️ Perfil"
])

# ═══════════════════════════════
# ABA 1 — TREINO
# ═══════════════════════════════

with aba1:
    st.info("✨ " + frase_aba("treino"))

    modo_treino = st.radio("Modo", ["Série", "Treino Livre"], horizontal=True, label_visibility="collapsed")

    # ── TREINO LIVRE ──────────────────────────────────────────────────────────
    if modo_treino == "Treino Livre":
        st.caption("TREINO LIVRE — adicione exercícios na hora")

        with st.form("form_livre"):
            c1, c2, c3, c4 = st.columns([3,1,1,1])
            tl_nome   = c1.text_input("Exercício", placeholder="Ex: Agachamento")
            tl_peso   = c2.number_input("Kg", value=0, min_value=0)
            tl_series = c3.number_input("Séries", value=3, min_value=1)
            tl_reps   = c4.number_input("Reps", value=12, min_value=1)
            tl_nota   = st.text_input("Nota (opcional)", placeholder="Como se sentiu, observações...")
            if st.form_submit_button("➕ Adicionar", use_container_width=True):
                if tl_nome.strip():
                    st.session_state.treino_livre_exs.append({
                        "nome": tl_nome.strip(), "peso": tl_peso,
                        "series": tl_series, "reps": tl_reps, "nota": tl_nota.strip(),
                    })
                    st.rerun()

        if st.session_state.treino_livre_exs:
            st.caption(str(len(st.session_state.treino_livre_exs)) + " exercício(s) adicionado(s)")
            for i, ex in enumerate(st.session_state.treino_livre_exs):
                c1, c2 = st.columns([9,1])
                txt = f"**{i+1}. {ex['nome']}** · {ex['series']}×{ex['reps']} · {ex['peso']}kg"
                if ex.get("nota"): txt += f" · _{ex['nota']}_"
                c1.info(txt)
                if c2.button("✕", key=f"del_livre_{i}"):
                    st.session_state.treino_livre_exs.pop(i); st.rerun()

            st.write("")
            if st.button("✅ Salvar treino livre", use_container_width=True):
                for ex in st.session_state.treino_livre_exs:
                    det = f"{ex['peso']}kg | {ex['series']}x{ex['reps']}"
                    if ex.get("nota"): det += f" | {ex['nota']}"
                    registrar_historico(None, det, tipo="musculacao")
                st.session_state.treino_livre_exs = []
                st.success("✅ Treino salvo!")
                st.balloons()
        else:
            st.caption("Nenhum exercício adicionado ainda.")

    # ── TREINO POR SÉRIE ──────────────────────────────────────────────────────
    else:
        if not st.session_state.treino_ativo:
            serie = st.radio("Série", ["A", "B", "C", "D"], horizontal=True, label_visibility="collapsed")

            exs = supabase.table("exercicios").select("id,nome,series,repeticoes,peso_kg")\
                .eq("serie_tipo", serie).eq("user_id", user_id()).execute()

            with st.expander("📋 Clonar esta série em outra"):
                outras = [s for s in ["A","B","C","D"] if s != serie]
                dest = st.selectbox("Clonar Série " + serie + " para →", outras, key="clone_dest")
                if st.button("Clonar", key="btn_clone"):
                    if exs.data:
                        for ex in exs.data:
                            dup = supabase.table("exercicios").select("id")\
                                .ilike("nome", ex["nome"]).eq("serie_tipo", dest)\
                                .eq("user_id", user_id()).execute()
                            if not dup.data:
                                supabase.table("exercicios").insert({
                                    "user_id": user_id(), "nome": ex["nome"],
                                    "serie_tipo": dest, "peso_kg": ex["peso_kg"],
                                    "series": ex["series"], "repeticoes": ex["repeticoes"],
                                }).execute()
                        st.success(f"✅ Série {serie} clonada para Série {dest}!")
                        st.rerun()
                    else:
                        st.warning("Série vazia, nada a clonar.")

            if exs.data:
                st.caption("SÉRIE " + serie + "  ·  " + str(len(exs.data)) + " exercícios")
                for i, ex in enumerate(exs.data, 1):
                    ult_det, ult_data = ultima_carga(ex["id"])
                    c1, c2 = st.columns([8, 1])
                    with c1:
                        txt = f"**{i}. {ex['nome']}** · {ex['series']}×{ex['repeticoes']} · {ex['peso_kg']} kg"
                        if ult_det:
                            txt += f"\n\n_Última vez ({ult_data}): {ult_det}_"
                        st.info(txt)
                    with c2:
                        st.write("")
                        if st.button("✕", key="del_" + str(ex["id"]), help="Remover"):
                            supabase.table("exercicios").delete().eq("id", ex["id"]).execute()
                            st.rerun()
                pode_iniciar = True
            else:
                st.caption("SÉRIE " + serie + "  ·  VAZIA")
                pode_iniciar = False

            with st.expander("＋ Adicionar exercício — Série " + serie, expanded=not pode_iniciar):
                with st.form("form_add_" + serie):
                    r_nome = st.text_input("Nome do exercício", placeholder="Ex: Supino Reto")
                    c1, c2, c3 = st.columns(3)
                    r_peso   = c1.number_input("Peso (kg)", value=0, min_value=0)
                    r_series = c2.number_input("Séries",    value=3, min_value=1)
                    r_reps   = c3.number_input("Reps",      value=12, min_value=1)
                    if st.form_submit_button("Adicionar exercício", use_container_width=True):
                        if r_nome.strip():
                            dup = supabase.table("exercicios").select("id")\
                                .ilike("nome", r_nome.strip()).eq("serie_tipo", serie)\
                                .eq("user_id", user_id()).execute()
                            if dup.data:
                                st.warning("'" + r_nome + "' já existe na Série " + serie)
                            else:
                                try:
                                    supabase.table("exercicios").insert({
                                        "user_id": user_id(), "nome": r_nome.strip(),
                                        "serie_tipo": serie, "peso_kg": r_peso,
                                        "series": r_series, "repeticoes": r_reps,
                                    }).execute()
                                    st.success("✅ '" + r_nome + "' adicionado!")
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erro ao adicionar: " + str(e))
                        else:
                            st.warning("Digite o nome do exercício.")

            st.write("")
            if st.button("🚀  Iniciar Série " + serie, use_container_width=True, disabled=not pode_iniciar):
                st.session_state.treino_ativo = True
                st.session_state.serie_atual  = serie
                st.session_state.indice_ex    = 0
                st.session_state.inicio_timer = time.time()
                st.session_state.timer_descanso_ativo = False
                st.rerun()

        else:
            res = supabase.table("exercicios").select("*")\
                .eq("serie_tipo", st.session_state.serie_atual).eq("user_id", user_id()).execute()

            if not res.data:
                st.warning("Nenhum exercício nesta série.")
                if st.button("Voltar"): st.session_state.treino_ativo = False; st.rerun()
            else:
                total = len(res.data)
                idx   = st.session_state.indice_ex

                if idx >= total:
                    try:
                        hist_all = supabase.table("historico_treinos").select("data_execucao")\
                            .eq("user_id", user_id()).execute()
                        df_all = pd.json_normalize(hist_all.data) if hist_all.data else pd.DataFrame()
                        if not df_all.empty:
                            df_all["data_execucao"] = pd.to_datetime(df_all["data_execucao"])
                        verificar_conquistas_treino(len(df_all), calcular_streak(df_all))
                    except Exception: pass
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.success("🎉 Treino concluído! Você arrasou hoje!")
                    st.info("💜 " + random.choice(FRASES))
                    st.rerun()

                ex  = res.data[idx]
                pct = int((idx / total) * 100)

                st.caption("SÉRIE " + st.session_state.serie_atual + "  ·  " + str(idx+1) + " de " + str(total))
                st.progress(pct)
                st.subheader("💪 " + ex["nome"])

                ult_det, ult_data = ultima_carga(ex["id"])
                if ult_det:
                    st.caption(f"📌 Última vez ({ult_data}): {ult_det}")

                c1, c2, c3 = st.columns(3)
                p = c1.number_input("Peso (kg)", value=int(ex["peso_kg"]),    step=1, key="p" + str(idx))
                s = c2.number_input("Séries",    value=int(ex["series"]),     step=1, key="s" + str(idx))
                r = c3.number_input("Reps",      value=int(ex["repeticoes"]), step=1, key="r" + str(idx))

                nota_ex = st.text_input("📝 Nota (opcional)",
                    placeholder="Como se sentiu, dor, observação...", key="nota_" + str(idx))

                elapsed = int(time.time() - st.session_state.inicio_timer)
                m_e, sg = divmod(elapsed, 60)

                st.divider()
                c_t1, c_t2, c_t3 = st.columns(3)
                c_t1.metric("⏱ Tempo", str(m_e).zfill(2) + ":" + str(sg).zfill(2))
                c_t2.metric("🔢 Exercício", str(idx+1) + "/" + str(total))
                c_t3.metric("📋 Série", st.session_state.serie_atual)

                # ── Timer de descanso ──────────────────────────────────────────
                st.divider()
                st.caption("⏳ TIMER DE DESCANSO")
                tc1, tc2, tc3, tc4 = st.columns(4)
                botoes_rest = [(tc1, 30, "30s"), (tc2, 60, "1min"), (tc3, 90, "1:30"), (tc4, 120, "2min")]
                for col, seg, label in botoes_rest:
                    if col.button(label, key=f"rest_{seg}_{idx}"):
                        st.session_state.timer_descanso        = seg
                        st.session_state.timer_descanso_inicio = time.time()
                        st.session_state.timer_descanso_ativo  = True
                        st.rerun()

                if st.session_state.timer_descanso_ativo:
                    decorrido = int(time.time() - st.session_state.timer_descanso_inicio)
                    restante  = st.session_state.timer_descanso - decorrido
                    if restante > 0:
                        mr, sr = divmod(restante, 60)
                        st.progress(1 - restante / st.session_state.timer_descanso)
                        st.info(f"Descansando... ⏳ {mr:02d}:{sr:02d}")
                    else:
                        st.session_state.timer_descanso_ativo = False
                        st.success("✅ Descanso concluído! Hora de mais uma série!")

                if idx > 0:
                    st.caption("💬 " + FRASES[(hoje_agora.day + idx) % len(FRASES)])

                st.write("")
                c_prox, c_cancel = st.columns(2)
                if c_prox.button("✅  Próximo →", use_container_width=True):
                    is_pr = verificar_pr(ex["id"], p)
                    det   = str(p) + "kg | " + str(s) + "x" + str(r) + " | " + str(elapsed//60) + "min"
                    if nota_ex: det += " | " + nota_ex
                    if is_pr:
                        det += " | 🏆 PR"
                        desbloquear_conquista("pr_primeiro")
                        st.success("🏆 NOVO RECORDE PESSOAL!")
                    registrar_historico(ex["id"], det)
                    supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex["id"]).execute()
                    st.session_state.indice_ex += 1
                    st.session_state.timer_descanso_ativo = False
                    st.rerun()
                if c_cancel.button("Cancelar treino", use_container_width=True):
                    st.session_state.treino_ativo = False; st.rerun()

                time.sleep(1)
                st.rerun()

    rodape()

# ═══════════════════════════════
# ABA 2 — CARDIO
# ═══════════════════════════════

with aba2:
    if not st.session_state.cardio_ativo:
        st.info("🏃 " + frase_aba("cardio"))

        try:
            ini_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0)
            res_sem = supabase.table("historico_treinos").select("detalhes")\
                .eq("user_id", user_id()).gte("data_execucao", ini_sem.isoformat()).execute()
            df_sem_c = pd.json_normalize(res_sem.data) if res_sem.data else pd.DataFrame()
            km_sem, _, _ = extrair_stats(df_sem_c)
        except Exception:
            km_sem = 0.0

        with st.expander("🎯 Meta semanal de distância"):
            meta_km = st.number_input("Meta em km por semana", value=20.0, step=1.0, min_value=1.0, key="meta_cardio")
            pct_meta = min(int((km_sem / meta_km) * 100), 100)
            st.progress(pct_meta)
            st.caption(f"{round(km_sem,1)} km de {meta_km} km esta semana ({pct_meta}%)")
            if pct_meta >= 100:
                st.success("🎉 Meta semanal batida! Incrível!")

        st.caption("CONFIGURAR ESTEIRA")
        modo = st.radio("Modo", ["Distância (km)", "Número de ciclos"], horizontal=True, label_visibility="collapsed")

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Min. Andando",        value=5.0, step=1.0)
        v_anda  = c1.number_input("Vel. Andando (km/h)",  value=5.0, step=0.5)
        t_corre = c2.number_input("Min. Correndo",        value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo (km/h)", value=9.0, step=0.5)

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
        st.info("📊  " + str(n_ciclos) + " ciclos  ·  ~" + str(round(km_est,2)) + " km  ·  ~" + fmt_tempo(min_est))

        st.write("")
        if st.button("🏃  Iniciar cardio", use_container_width=True):
            etapas = []
            for i in range(int(n_ciclos)):
                etapas += [
                    ("Caminhada " + str(i+1) + "/" + str(int(n_ciclos)), int(t_anda*60), v_anda),
                    ("Corrida "   + str(i+1) + "/" + str(int(n_ciclos)), int(t_corre*60), v_corre),
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

        if st.button("⏹  Encerrar e salvar", use_container_width=True):
            if not st.session_state.cardio_salvo:
                tf = int((time.time()-st.session_state.t_cardio_start)/60)
                dist_r = round(st.session_state.dist_real, 2)
                registrar_historico(None, "Interrompido: " + str(dist_r) + "km | " + str(tf) + "min", tipo="cardio")
                st.session_state.cardio_salvo = True
                if dist_r >= 5:  desbloquear_conquista("cardio_5km")
                if dist_r >= 10: desbloquear_conquista("cardio_10km")
            st.session_state.cardio_ativo = False; st.rerun()

        if idx >= len(et):
            if not st.session_state.cardio_salvo:
                tf = int((time.time()-st.session_state.t_cardio_start)/60)
                dist_r = round(st.session_state.dist_real, 2)
                registrar_historico(None, "Concluído: " + str(dist_r) + "km | " + str(tf) + "min", tipo="cardio")
                st.session_state.cardio_salvo = True
                if dist_r >= 5:  desbloquear_conquista("cardio_5km")
                if dist_r >= 10: desbloquear_conquista("cardio_10km")
            st.session_state.cardio_ativo = False
            st.balloons()
            st.success("🎉 Cardio concluído! Você foi incrível!")
            st.info("💜 " + random.choice(FRASES))
            st.rerun()

        nome_et, _, vel_et = et[idx]
        seg = p["seg_restantes"]; m, s = divmod(seg, 60)
        pct = int((st.session_state.dist_real / da) * 100) if da > 0 else 0

        st.subheader("🏃 " + nome_et)
        st.progress(min(pct, 100))
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("⏱ Restante", str(m).zfill(2) + ":" + str(s).zfill(2))
        c2.metric("📍 Distância", str(round(st.session_state.dist_real, 2)) + " / " + str(round(da, 2)) + " km")
        st.divider()

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

# ═══════════════════════════════
# ABA 3 — PAINEL
# ═══════════════════════════════

with aba3:
    st.info("📊 " + frase_aba("painel"))
    try:
        res_h = supabase.table("historico_treinos").select("*,exercicios(nome)")\
            .eq("user_id", user_id()).order("data_execucao", desc=True).execute()

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

            def delta_str(atual, anterior, fmt="{:.0f}"):
                if anterior == 0: return None
                diff = atual - anterior
                return ("+" if diff >= 0 else "") + fmt.format(diff)

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
                fim_dt = datetime.combine(fim_sel, datetime.max.time()).replace(tzinfo=fuso)
                ini_dt = datetime.combine(ini_sel, datetime.min.time()).replace(tzinfo=fuso)
                df_f = df[(df["data_execucao"] >= ini_dt) & (df["data_execucao"] <= fim_dt)]
                titulo_resumo = "RESUMO — HOJE, " + hoje_agora.strftime("%d/%m/%Y")

            elif modo_filtro == "Mês":
                anos = sorted(df["data_execucao"].dt.year.unique(), reverse=True)
                c1, c2 = st.columns(2)
                ano_sel = c1.selectbox("Ano", anos)
                meses_d = sorted(df[df["data_execucao"].dt.year==ano_sel]["data_execucao"].dt.month.unique(), reverse=True)
                mes_sel = c2.selectbox("Mês", meses_d, format_func=lambda x: meses_n[x])
                df_f = df[(df["data_execucao"].dt.month==mes_sel)&(df["data_execucao"].dt.year==ano_sel)]
                titulo_resumo = "RESUMO — " + meses_n[mes_sel].upper()

            else:
                c1, c2 = st.columns(2)
                ini_default = max(data_min, data_max - timedelta(days=6))
                ini_sel = c1.date_input("De", value=ini_default, min_value=data_min, max_value=data_max, key="dt_ini")
                fim_sel = c2.date_input("Até", value=data_max,   min_value=data_min, max_value=data_max, key="dt_fim")
                if ini_sel > fim_sel:
                    st.warning("A data inicial deve ser anterior à final.")
                    ini_sel = fim_sel
                fim_dt = datetime.combine(fim_sel, datetime.max.time()).replace(tzinfo=fuso)
                ini_dt = datetime.combine(ini_sel, datetime.min.time()).replace(tzinfo=fuso)
                df_f = df[(df["data_execucao"] >= ini_dt) & (df["data_execucao"] <= fim_dt)]
                titulo_resumo = "RESUMO — " + (ini_sel.strftime("%d/%m/%Y") if ini_sel == fim_sel
                                               else ini_sel.strftime("%d/%m") + " a " + fim_sel.strftime("%d/%m/%Y"))

            km_f, min_f, kg_f = extrair_stats(df_f)

            st.caption(titulo_resumo)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🏋️ Atividades", len(df_f))
            c2.metric("🏋️ Vol. Total",  f"{kg_f:,.0f} kg")
            c3.metric("⏱ Tempo",       fmt_tempo(min_f))
            c4.metric("🛣️ Distância",  str(round(km_f,1)) + " km")

            # Comparativo semanal
            if kg_ant == 0 and km_ant == 0 and min_ant == 0:
                st.info("📅 Sem dados da semana passada para comparar ainda. Bora criar um histórico! 💪")
            else:
                partes = []
                if kg_ant > 0:
                    diff_kg = kg_ant - kg_a
                    if diff_kg > 0:   partes.append(f"**{diff_kg:,.0f} kg** de volume de treino")
                    elif diff_kg < 0: partes.append(f"~~peso~~ já superou em **{abs(diff_kg):,.0f} kg** 🔥")
                if min_ant > 0:
                    diff_min = min_ant - min_a
                    if diff_min > 0:   partes.append(f"**{fmt_tempo(diff_min)}** de tempo ativo")
                    elif diff_min < 0: partes.append(f"~~tempo~~ já superou em **{fmt_tempo(abs(diff_min))}** 🔥")
                if km_ant > 0:
                    diff_km = round(km_ant - km_a, 1)
                    if diff_km > 0:   partes.append(f"**{diff_km} km** de distância")
                    elif diff_km < 0: partes.append(f"~~distância~~ já superou em **{abs(diff_km)} km** 🔥")

                faltam  = [p for p in partes if not p.startswith("~~")]
                superou = [p for p in partes if p.startswith("~~")]
                if not faltam and not superou:
                    st.success("🏆 Semana igualada! Agora é superar!")
                elif not faltam:
                    st.success("🏆 Você superou a semana passada em tudo! Incrível!")
                else:
                    msg = "💡 Ainda falta " + ", ".join(faltam) + " pra se equiparar à semana passada."
                    if superou:
                        msg += " Mas " + ", ".join(s.replace("~~","") for s in superou) + "!"
                    st.warning(msg)

            st.caption("ATIVIDADES — " + titulo_resumo.replace("RESUMO — ", ""))
            if df_f.empty:
                st.info("Nenhum registro neste período.")
            else:
                df_show = df_f.copy()
                if "exercicios.nome" not in df_show.columns: df_show["exercicios.nome"] = "Cardio"
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
                    supabase.table("historico_treinos").delete().eq("user_id", user_id()).execute()
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

with aba4:
    st.info("📈 " + frase_aba("evolucao"))

    sub1, sub2, sub3 = st.tabs(["🏋️ Progressão por exercício", "⚖️ Peso corporal", "📏 Medidas"])

    with sub1:
        try:
            exs_todos = supabase.table("exercicios").select("id,nome,serie_tipo")\
                .eq("user_id", user_id()).order("nome").execute()
            if not exs_todos.data:
                st.info("Nenhum exercício cadastrado ainda.")
            else:
                nomes_ex = [f"{e['nome']} (Série {e['serie_tipo']})" for e in exs_todos.data]
                sel      = st.selectbox("Escolha o exercício", nomes_ex)
                ex_id_sel = exs_todos.data[nomes_ex.index(sel)]["id"]

                hist_ex = supabase.table("historico_treinos").select("data_execucao,detalhes")\
                    .eq("user_id", user_id()).eq("exercicio_id", ex_id_sel)\
                    .order("data_execucao").execute()

                if not hist_ex.data:
                    st.info("Nenhum registro para este exercício ainda.")
                else:
                    rows = []
                    for h in hist_ex.data:
                        m_kg = _re.search(r"([\d.]+)kg", str(h.get("detalhes","")))
                        if m_kg:
                            rows.append({
                                "Data": pd.to_datetime(h["data_execucao"]).astimezone(fuso).strftime("%d/%m/%y"),
                                "Peso (kg)": float(m_kg.group(1)),
                                "PR": "🏆" if "PR" in str(h.get("detalhes","")) else "",
                            })
                    if rows:
                        df_ex = pd.DataFrame(rows)
                        st.line_chart(df_ex.set_index("Data")["Peso (kg)"], use_container_width=True)
                        pr_max = df_ex["Peso (kg)"].max()
                        st.caption(f"🏆 Recorde pessoal: **{pr_max} kg**  ·  {len(df_ex)} registros")
                        st.dataframe(df_ex, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error("Erro: " + str(e))

    with sub2:
        try:
            with st.form("form_peso"):
                c1, c2 = st.columns(2)
                peso_val  = c1.number_input("Peso (kg)", value=60.0, step=0.1, min_value=20.0, max_value=300.0)
                peso_data = c2.date_input("Data", value=hoje_agora.date())
                peso_obs  = st.text_input("Observação (opcional)", placeholder="Em jejum, após treino...")
                if st.form_submit_button("Registrar peso", use_container_width=True):
                    supabase.table("peso_corporal").insert({
                        "user_id": user_id(), "peso_kg": peso_val,
                        "data": peso_data.isoformat(), "observacao": peso_obs.strip() or None,
                    }).execute()
                    desbloquear_conquista("peso_registrado")
                    st.success("✅ Peso registrado!"); st.rerun()

            res_peso = supabase.table("peso_corporal").select("*")\
                .eq("user_id", user_id()).order("data").execute()

            if res_peso.data:
                df_peso = pd.DataFrame(res_peso.data)
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

                df_tab_p = df_peso[["data","peso_kg","observacao"]].copy()
                df_tab_p["data"] = df_tab_p["data"].dt.strftime("%d/%m/%Y")
                st.dataframe(df_tab_p.rename(
                    columns={"data":"Data","peso_kg":"Peso (kg)","observacao":"Obs"}
                ).iloc[::-1], use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro de peso ainda.")
        except Exception as e:
            st.error("Erro: " + str(e))

    with sub3:
        MEDIDAS = [
            ("cintura_cm",    "Cintura (cm)"),
            ("quadril_cm",    "Quadril (cm)"),
            ("busto_cm",      "Busto (cm)"),
            ("braco_d_cm",    "Braço D (cm)"),
            ("braco_e_cm",    "Braço E (cm)"),
            ("coxa_d_cm",     "Coxa D (cm)"),
            ("coxa_e_cm",     "Coxa E (cm)"),
            ("panturrilha_cm","Panturrilha (cm)"),
            ("pescoco_cm",    "Pescoço (cm)"),
        ]
        try:
            with st.form("form_medidas"):
                st.caption("Preencha apenas as medidas que deseja registrar.")
                data_med = st.date_input("Data da medição", value=hoje_agora.date())
                cols_med = st.columns(3)
                vals_med = {}
                for i, (campo, label) in enumerate(MEDIDAS):
                    vals_med[campo] = cols_med[i % 3].number_input(label, value=0.0, step=0.5, min_value=0.0)
                obs_med = st.text_input("Observação (opcional)")
                if st.form_submit_button("Registrar medidas", use_container_width=True):
                    payload = {"user_id": user_id(), "data": data_med.isoformat(),
                               "observacao": obs_med.strip() or None}
                    payload.update({k: v if v > 0 else None for k, v in vals_med.items()})
                    supabase.table("medidas_corporais").insert(payload).execute()
                    desbloquear_conquista("medidas_registradas")
                    st.success("✅ Medidas registradas!"); st.rerun()

            res_med = supabase.table("medidas_corporais").select("*")\
                .eq("user_id", user_id()).order("data").execute()

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
                df_tab_m = df_med[colunas_show].copy()
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

with aba5:
    st.info("🏆 " + frase_aba("conquistas"))

    try:
        res_conq = supabase.table("conquistas").select("conquista_id,desbloqueada_em")\
            .eq("user_id", user_id()).execute()
        desbloqueadas = {r["conquista_id"]: r["desbloqueada_em"] for r in (res_conq.data or [])}

        res_all_h = supabase.table("historico_treinos").select("data_execucao")\
            .eq("user_id", user_id()).execute()
        df_all_h = pd.json_normalize(res_all_h.data) if res_all_h.data else pd.DataFrame()
        if not df_all_h.empty:
            df_all_h["data_execucao"] = pd.to_datetime(df_all_h["data_execucao"])
        streak_atual  = calcular_streak(df_all_h)
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
                    <div style="font-weight:600;color:#888;margin-top:4px">{c['nome']}</div>
                    <div style="color:#666;font-size:0.8rem">{c['desc']}</div>
                    </div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("🎯 Metas do mês")

        try:
            res_metas = supabase.table("metas_mensais").select("*")\
                .eq("user_id", user_id())\
                .eq("mes", hoje_agora.month).eq("ano", hoje_agora.year).execute()
            meta_atual = res_metas.data[0] if res_metas.data else {}
        except Exception:
            meta_atual = {}

        with st.expander("✏️ Definir metas deste mês"):
            with st.form("form_metas"):
                c1, c2, c3 = st.columns(3)
                m_treinos = c1.number_input("Treinos",           value=int(meta_atual.get("treinos",12)),         min_value=1)
                m_km      = c2.number_input("Distância (km)",    value=float(meta_atual.get("distancia_km",30.0)), step=1.0)
                m_min     = c3.number_input("Tempo ativo (min)", value=int(meta_atual.get("tempo_min",300)),       min_value=1)
                if st.form_submit_button("Salvar metas", use_container_width=True):
                    supabase.table("metas_mensais").upsert({
                        "user_id": user_id(), "mes": hoje_agora.month, "ano": hoje_agora.year,
                        "treinos": m_treinos, "distancia_km": m_km, "tempo_min": m_min,
                    }).execute()
                    st.success("✅ Metas salvas!"); st.rerun()

        if meta_atual:
            ini_mes = hoje_agora.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
            try:
                res_mes = supabase.table("historico_treinos").select("detalhes")\
                    .eq("user_id", user_id()).gte("data_execucao", ini_mes.isoformat()).execute()
                df_mes = pd.json_normalize(res_mes.data) if res_mes.data else pd.DataFrame()
                km_mes, min_mes, _ = extrair_stats(df_mes)
                tr_mes = len(df_mes)
            except Exception:
                km_mes = 0.0; min_mes = 0; tr_mes = 0

            c1, c2, c3 = st.columns(3)
            pct_tr = min(int(tr_mes / max(meta_atual.get("treinos",1),1) * 100), 100)
            pct_km = min(int(km_mes / max(float(meta_atual.get("distancia_km",1)),0.01) * 100), 100)
            pct_mn = min(int(min_mes / max(meta_atual.get("tempo_min",1),1) * 100), 100)

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

with aba6:
    st.info("⚙️ " + frase_aba("perfil"))

    email_atual = st.session_state.usuario["email"]
    nome_atual  = st.session_state.usuario["nome"]

    try:
        rp = supabase.table("perfis").select("nome,telefone,cidade,estado").eq("user_id", user_id()).execute()
        dp = rp.data[0] if rp.data else {}
    except Exception:
        dp = {}

    st.subheader("⚙️ Meu Perfil")

    st.markdown("""
    <style>
    .perfil-card {
        background: #13131f; border: 1px solid #2d2d45; border-radius: 10px;
        padding: 12px 16px; margin-bottom: 8px; display: flex;
        align-items: center; gap: 10px; font-size: 0.92rem;
    }
    .perfil-label { color: #888; font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 0.05em; margin-bottom: 2px; }
    .perfil-valor { color: #e2e8f0; font-size: 0.95rem; font-weight: 500; }
    .perfil-icon  { font-size: 1.2rem; flex-shrink: 0; }
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
            ed_nome   = st.text_input("Nome", value=dp.get("nome", nome_atual))
            ed_tel    = st.text_input("Telefone", value=dp.get("telefone",""), placeholder="(28) 99999-9999")
            ed_cidade = st.text_input("Cidade", value=dp.get("cidade",""))
            ests      = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                         "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
            idx_e     = ests.index(dp.get("estado","ES")) if dp.get("estado","ES") in ests else 7
            ed_estado = st.selectbox("Estado", ests, index=idx_e)
            if st.form_submit_button("Salvar alterações", use_container_width=True):
                if ed_nome.strip() and ed_tel.strip() and ed_cidade.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": ed_nome.strip()}})
                        supabase.table("perfis").upsert({
                            "user_id": user_id(), "nome": ed_nome.strip(),
                            "telefone": ed_tel.strip(), "cidade": ed_cidade.strip(), "estado": ed_estado,
                        }).execute()
                        st.session_state.usuario["nome"] = ed_nome.strip()
                        st.success("✅ Dados atualizados!"); st.rerun()
                    except Exception as e: st.error("Erro: " + str(e))
                else: st.warning("Preencha todos os campos.")

    with st.expander("📧 Alterar email"):
        st.caption("Você receberá um link de confirmação em ambos os emails.")
        with st.form("form_email"):
            novo_email  = st.text_input("Novo email", placeholder="novo@email.com")
            senha_email = st.text_input("Senha atual", type="password")
            if st.form_submit_button("Enviar confirmações", use_container_width=True):
                if not novo_email.strip() or "@" not in novo_email: st.warning("Email inválido.")
                elif not senha_email: st.warning("Digite sua senha.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_email})
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success("✅ Confirmações enviadas! Verifique os dois emails.")
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    with st.expander("🔒 Alterar senha"):
        with st.form("form_senha"):
            s_antiga = st.text_input("Senha atual", type="password")
            s_nova   = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            s_conf   = st.text_input("Confirmar nova senha", type="password")
            if st.form_submit_button("Salvar nova senha", use_container_width=True):
                if not s_antiga: st.warning("Digite a senha atual.")
                elif len(s_nova) < 8: st.warning("Mínimo 8 caracteres.")
                elif s_nova != s_conf: st.error("Senhas não coincidem.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": s_antiga})
                        supabase.auth.update_user({"password": s_nova})
                        st.success("✅ Senha alterada com sucesso!")
                    except Exception: st.error("Senha atual incorreta.")

    st.divider()

    with st.expander("⚠️ Apagar minha conta"):
        st.warning("Ação irreversível. Todos os dados serão removidos permanentemente.")
        with st.form("form_del_conta"):
            conf_txt   = st.text_input("Digite APAGAR para confirmar", placeholder="APAGAR")
            senha_conf = st.text_input("Sua senha", type="password")
            if st.form_submit_button("Apagar conta permanentemente", use_container_width=True):
                if conf_txt.strip().upper() != "APAGAR": st.error("Digite APAGAR em maiúsculas.")
                elif not senha_conf: st.warning("Digite sua senha.")
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
                            st.success("Conta apagada. Até logo! 👋"); time.sleep(1); fazer_logout()
                        else:
                            st.error("Erro: " + str(body.get("error", body)))
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    rodape()