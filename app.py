import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

fuso = pytz.timezone("America/Sao_Paulo")
hoje_agora = datetime.now(fuso)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #ffffff; }
.block-container { padding-top: 1rem !important; }
div.stButton > button {
    background-color: #7d33ff;
    color: white;
    border-radius: 12px;
    height: 3.5em;
    width: 100%;
    font-weight: bold;
    border: none;
}
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
    margin: 80px auto;
    background: #1e1e2e;
    border: 2px solid #7d33ff;
    border-radius: 16px;
    padding: 40px 32px;
}
.stNumberInput div div input {
    background-color: #1e1e2e !important;
    color: #e066ff !important;
    font-size: 22px !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 5px; }
.stTabs [data-baseweb="tab"] {
    background-color: #1e1e2e;
    border-radius: 8px 8px 0 0;
    color: white;
}
.stTabs [aria-selected="true"] { background-color: #7d33ff !important; }
</style>
""", unsafe_allow_html=True)

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
    "usuario":        None,   # dict com id, email, nome
    "access_token":   None,
    "refresh_token":  None,
    # Treino
    "treino_ativo":   False,
    "serie_atual":    "A",
    "indice_ex":      0,
    "inicio_timer":   0.0,
    # Cardio
    "cardio_ativo":   False,
    "params_cardio":  None,
    "dist_real":      0.0,
    "t_cardio_start": 0.0,
    "cardio_salvo":   False,
    # UI
    "confirmar_historico": False,
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
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id":    res.user.id,
            "email": res.user.email,
            "nome":  res.user.user_metadata.get("nome", email.split("@")[0]),
        }
        return True
    except Exception as e:
        st.error(f"❌ Email ou senha incorretos.")
        return False

def fazer_logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k in ["usuario", "access_token", "refresh_token",
              "treino_ativo", "cardio_ativo", "params_cardio"]:
        st.session_state[k] = defaults[k]
    st.rerun()

def user_id() -> str:
    """Retorna o UUID do utilizador logado."""
    return st.session_state.usuario["id"]

# ─────────────────────────────────────────────
# HELPERS — DADOS
# Todas as queries incluem user_id para isolamento
# ─────────────────────────────────────────────
def registrar_historico(ex_id, detalhes: str, tipo: str = "musculacao") -> None:
    supabase.table("historico_treinos").insert({
        "user_id":        user_id(),
        "exercicio_id":   ex_id,
        "data_execucao":  datetime.now(fuso).isoformat(),
        "detalhes":       detalhes,
        "tipo":           tipo,
    }).execute()

def extrair_stats(dataframe: pd.DataFrame) -> tuple[float, int]:
    if dataframe.empty or "detalhes" not in dataframe.columns:
        return 0.0, 0
    kms  = dataframe["detalhes"].str.extract(r"([\d.]+)km").astype(float).sum()[0]
    mins = dataframe["detalhes"].str.extract(r"(\d+)min").astype(float).sum()[0]
    return (float(kms) if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)

# ─────────────────────────────────────────────
# TELA DE LOGIN
# ─────────────────────────────────────────────
def tela_login():
    st.markdown("""
        <div class="login-box">
            <h2 style="text-align:center;color:#e066ff;margin-bottom:8px;">🏋️ PyTrain PRO</h2>
            <p style="text-align:center;color:gray;margin-bottom:24px;">Entre com sua conta para continuar</p>
        </div>
    """, unsafe_allow_html=True)

    # Centralizar formulário
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
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
                <p style="color:gray;">Bem-vinda! Define a tua senha para activar a conta.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_definir_senha"):
            nova_senha  = st.text_input("🔒 Nova Senha", type="password", placeholder="mínimo 8 caracteres")
            conf_senha  = st.text_input("🔒 Confirmar Senha", type="password", placeholder="repita a senha")
            salvar      = st.form_submit_button("Activar Conta", use_container_width=True)

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
                st.session_state.access_token  = access_token
                st.session_state.refresh_token = refresh_token
                st.session_state.usuario = {
                    "id":    user.user.id,
                    "email": user.user.email,
                    "nome":  user.user.user_metadata.get("nome", user.user.email.split("@")[0]),
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

# Verifica se chegaram tokens via URL (vindo da página de redirect)
qp            = st.query_params
url_token     = qp.get("access_token")
url_refresh   = qp.get("refresh_token")
url_type      = qp.get("type", "")

if url_token and url_refresh and not st.session_state.usuario:
    # Convite ou recuperação de senha — mostra tela de definir senha
    tela_definir_senha(url_token, url_refresh)
    st.stop()

if not st.session_state.usuario:
    tela_login()
    st.stop()   # Nada abaixo é renderizado sem login

# ─────────────────────────────────────────────
# APP PRINCIPAL (só chega aqui se estiver logado)
# ─────────────────────────────────────────────
nome_usuario = st.session_state.usuario["nome"]
hora_atual   = hoje_agora.hour

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
    msg_motivacao = f"Já tens **{treinos_mes} treinos** este mês. Continue assim! 🔥"
elif treinos_mes < 10:
    msg_motivacao = f"**{treinos_mes} treinos** este mês — você está voando! 🚀"
else:
    msg_motivacao = f"Impressionante! **{treinos_mes} treinos** este mês. Você é uma máquina! 🏆"

# ── Banner de saudação (largura total) ───────────────────────────
st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e1e2e 0%, #2a1a3e 100%);
        border: 2px solid #7d33ff;
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 16px;
    ">
        <div style="font-size:2.4em; line-height:1; flex-shrink:0;">{emoji_hora}</div>
        <div>
            <p style="margin:0; color:#a78bfa; font-size:0.8em; letter-spacing:1px; text-transform:uppercase;">
                🏋️ PyTrain PRO
            </p>
            <h2 style="margin:3px 0 4px; color:#ffffff; font-size:1.35em;">
                {saudacao}, <span style="color:#e066ff;">{nome_usuario}</span>!
            </h2>
            <p style="margin:0; color:#aaa; font-size:0.88em;">{msg_motivacao}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

col_esp, col_sair = st.columns([6, 1])
with col_sair:
    if st.button("🚪 Sair", use_container_width=True):
        fazer_logout()

aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])

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

        if preview.data:
            st.markdown(f"#### 📋 Série {serie} — {len(preview.data)} exercícios")
            for i, ex in enumerate(preview.data, 1):
                st.markdown(
                    f"""<div style="background:#1e1e2e;border-left:3px solid #7d33ff;
                        border-radius:8px;padding:10px 16px;margin:6px 0;
                        display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:white;font-weight:bold;">{i}. {ex['nome']}</span>
                        <span style="color:#a78bfa;font-size:0.85em;">
                            {ex['series']}x{ex['repeticoes']} &nbsp;|&nbsp; {ex['peso_kg']} kg
                        </span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            pode_iniciar = True
        else:
            st.warning(f"Nenhum exercício cadastrado na Série {serie}. Adicione no Menu ⚙️.")
            pode_iniciar = False

        if st.button(f"🚀 INICIAR TREINO — SÉRIE {serie}", use_container_width=True, disabled=not pode_iniciar):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual  = serie
            st.session_state.indice_ex    = 0
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
            indice   = st.session_state.indice_ex

            if indice >= total_ex:
                st.session_state.treino_ativo = False
                st.balloons()
                st.success("🎉 Treino concluído!")
                st.rerun()

            ex_atual = res.data[indice]

            st.markdown(f"""
                <div class="foco-container">
                    <h4 style="color:gray;margin:0;">
                        Série {st.session_state.serie_atual} | {indice + 1} de {total_ex}
                    </h4>
                    <h1 style="color:#e066ff;margin:10px 0;font-size:28px;">{ex_atual['nome']}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg",   value=int(ex_atual["peso_kg"]),   step=1, key=f"p_{indice}")
            s = c2.number_input("Sets", value=int(ex_atual["series"]),     step=1, key=f"s_{indice}")
            r = c3.number_input("Reps", value=int(ex_atual["repeticoes"]), step=1, key=f"r_{indice}")

            tempo_total_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_total_seg, 60)
            st.markdown(f"""
                <div style="text-align:center;padding:15px;border:1px solid #7d33ff;
                            border-radius:12px;margin:15px 0;">
                    <small style="color:gray;">TEMPO TOTAL</small><br>
                    <span style="font-size:35px;font-weight:bold;color:white;">{m:02d}:{seg:02d}</span>
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


# ═══════════════════════════════════════════
# ABA 2 — CARDIO
# ═══════════════════════════════════════════
with aba2:
    if not st.session_state.cardio_ativo:
        st.subheader("Configurar Esteira")
        modo = st.radio("Objetivo:", ["Distância Alvo (km)", "Número de Ciclos"], horizontal=True)

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Minutos Andando",  value=5.0, step=1.0)
        v_anda  = c1.number_input("Vel. Andando",     value=5.0, step=0.5)
        t_corre = c2.number_input("Minutos Correndo", value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo",    value=9.0, step=0.5)

        dist_ciclo = (v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60))
        if dist_ciclo <= 0:
            st.warning("Verifique as velocidades e tempos configurados.")
            st.stop()

        if modo == "Distância Alvo (km)":
            dist_alvo = st.number_input("Meta (km)", value=5.0, step=0.5, min_value=0.1)
            n_ciclos  = max(1, round(dist_alvo / dist_ciclo))
            tempo_total_min = n_ciclos * (t_anda + t_corre)
            st.info(f"Estimativa: **{n_ciclos} ciclos** → ~{dist_ciclo * n_ciclos:.2f} km | ~{int(tempo_total_min)} min")
        else:
            n_ciclos  = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos
            tempo_total_min = n_ciclos * (t_anda + t_corre)
            st.info(f"Estimativa: ~{dist_alvo:.2f} km | ~{int(tempo_total_min)} min")

        if st.button("🚀 INICIAR CARDIO", use_container_width=True):
            etapas = []
            for i in range(int(n_ciclos)):
                etapas.append((f"🚶 Caminhada ({i+1}/{int(n_ciclos)})", int(t_anda * 60),  v_anda))
                etapas.append((f"⚡ Corrida   ({i+1}/{int(n_ciclos)})", int(t_corre * 60), v_corre))

            st.session_state.cardio_ativo   = True
            st.session_state.cardio_salvo   = False
            st.session_state.dist_real      = 0.0
            st.session_state.t_cardio_start = time.time()
            st.session_state.params_cardio  = {
                "etapas":        etapas,
                "dist_alvo":     dist_alvo,
                "etapa_idx":     0,
                "seg_restantes": etapas[0][1] if etapas else 0,
            }
            st.rerun()

    else:
        params    = st.session_state.params_cardio
        etapas    = params["etapas"]
        dist_alvo = params["dist_alvo"]
        idx       = params["etapa_idx"]

        if st.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(None, f"Interrompido: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.rerun()

        if idx >= len(etapas):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(None, f"Concluído: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
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
                <h3 style="color:#66ffe0;">
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
                1: "Janeiro", 2: "Fevereiro", 3: "Março",     4: "Abril",
                5: "Maio",    6: "Junho",     7: "Julho",     8: "Agosto",
                9: "Setembro",10: "Outubro",  11: "Novembro", 12: "Dezembro",
            }
            meses_disp = sorted(
                df[df["data_execucao"].dt.year == ano_sel]["data_execucao"].dt.month.unique(),
                reverse=True,
            )
            mes_sel = col_f2.selectbox("Mês", meses_disp, format_func=lambda x: meses_nomes[x])

            df_filtrado = df[
                (df["data_execucao"].dt.month == mes_sel) &
                (df["data_execucao"].dt.year  == ano_sel)
            ]

            st.markdown(f"#### 📈 Resumo de {meses_nomes[mes_sel]}/{ano_sel}")
            c1, c2, c3 = st.columns(3)
            km_f, min_f = extrair_stats(df_filtrado)
            c1.metric("Treinos",     len(df_filtrado))
            c2.metric("Distância",   f"{km_f:.2f} km")
            c3.metric("Tempo Total", f"{min_f} min")

            df_hoje    = df[df["data_execucao"].dt.date == hoje_agora.date()]
            inicio_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            df_semana  = df[df["data_execucao"] >= inicio_sem]

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
                st.dataframe(df_show[["Data", "exercicios.nome", "detalhes"]], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")


# ═══════════════════════════════════════════
# ABA 4 — CONFIGURAÇÕES
# ═══════════════════════════════════════════
with aba4:
    st.header("⚙️ Gerenciamento do Sistema")

    # ── Perfil do utilizador ──────────────────────────────────────────
    with st.expander("👤 Meu Perfil"):
        email_atual = st.session_state.usuario["email"]
        nome_atual  = st.session_state.usuario["nome"]

        st.markdown(f"**Email atual:** `{email_atual}`")
        st.markdown("---")

        # Alterar nome
        with st.form("form_nome"):
            st.markdown("##### ✏️ Alterar Nome")
            novo_nome = st.text_input("Novo nome", value=nome_atual, placeholder="Seu nome")
            if st.form_submit_button("Salvar Nome", use_container_width=True):
                if novo_nome.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": novo_nome.strip()}})
                        st.session_state.usuario["nome"] = novo_nome.strip()
                        st.success("✅ Nome atualizado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Digite um nome válido.")

        st.markdown("---")

        # Alterar email
        with st.form("form_email"):
            st.markdown("##### 📧 Alterar Email")
            novo_email = st.text_input("Novo email", placeholder="novo@email.com")
            if st.form_submit_button("Salvar Email", use_container_width=True):
                if novo_email.strip() and "@" in novo_email:
                    try:
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success("✅ Confirmação enviada para o novo email. Verifique a caixa de entrada.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Digite um email válido.")

        st.markdown("---")

        # Alterar senha
        with st.form("form_senha"):
            st.markdown("##### 🔒 Alterar Senha")
            nova_senha  = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres")
            conf_senha  = st.text_input("Confirmar senha", type="password", placeholder="repita a senha")
            if st.form_submit_button("Salvar Senha", use_container_width=True):
                if not nova_senha or len(nova_senha) < 8:
                    st.warning("A senha deve ter pelo menos 8 caracteres.")
                elif nova_senha != conf_senha:
                    st.error("As senhas não coincidem.")
                else:
                    try:
                        supabase.auth.update_user({"password": nova_senha})
                        st.success("✅ Senha alterada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.markdown("---")

        # Recuperar senha por email
        st.markdown("##### 🔑 Esqueci a Senha")
        st.caption("Envia um link de recuperação para o teu email de cadastro.")
        if st.button("Enviar link de recuperação", use_container_width=True):
            try:
                supabase.auth.reset_password_email(email_atual)
                st.success(f"✅ Link enviado para **{email_atual}**. Verifique a caixa de entrada.")
            except Exception as e:
                st.error(f"Erro: {e}")

    st.divider()

    with st.expander("✨ Cadastrar Novo Exercício"):
        with st.form("form_cadastro"):
            n_nome   = st.text_input("Nome do Exercício")
            n_serie  = st.selectbox("Série", ["A", "B", "C", "D"])
            n_peso   = st.number_input("Peso Inicial (kg)", value=0, min_value=0)
            n_series = st.number_input("Séries padrão", value=3, min_value=1)
            n_reps   = st.number_input("Repetições padrão", value=12, min_value=1)

            if st.form_submit_button("Salvar no Catálogo"):
                if n_nome.strip():
                    existe = (
                        supabase.table("exercicios")
                        .select("id")
                        .ilike("nome", n_nome.strip())
                        .eq("user_id", user_id())
                        .execute()
                    )
                    if existe.data:
                        st.warning(f"'{n_nome}' já existe no seu catálogo.")
                    else:
                        supabase.table("exercicios").insert({
                            "user_id":    user_id(),
                            "nome":       n_nome.strip(),
                            "serie_tipo": n_serie,
                            "peso_kg":    n_peso,
                            "series":     n_series,
                            "repeticoes": n_reps,
                        }).execute()
                        st.success(f"✅ '{n_nome}' adicionado à Série {n_serie}!")
                        st.rerun()
                else:
                    st.warning("Digite o nome do exercício.")

    with st.expander("📝 Editar ou Remover Exercícios"):
        res_cat = (
            supabase.table("exercicios")
            .select("*")
            .eq("user_id", user_id())
            .order("serie_tipo")
            .execute()
        )
        if res_cat.data:
            for ex_cat in res_cat.data:
                col_n, col_d = st.columns([3, 1])
                col_n.write(f"**{ex_cat['nome']}** — Série {ex_cat['serie_tipo']} | {ex_cat['peso_kg']} kg")
                if col_d.button("🗑️", key=f"del_{ex_cat['id']}"):
                    supabase.table("exercicios").delete().eq("id", ex_cat["id"]).execute()
                    st.warning(f"Removido: {ex_cat['nome']}")
                    st.rerun()
        else:
            st.info("Catálogo vazio.")

    st.divider()
    st.subheader("🚨 Zona de Perigo")
    st.warning("Estas acções são irreversíveis.")

    col_h, col_p = st.columns(2)

    if col_h.button("🗑️ Apagar Todo Histórico"):
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

    if col_p.button("🔄 Resetar Todos os Pesos"):
        supabase.table("exercicios").update({"peso_kg": 0}).eq("user_id", user_id()).execute()
        st.success("Pesos resetados para 0 kg!")
        st.rerun()