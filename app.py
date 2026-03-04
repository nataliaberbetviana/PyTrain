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

fuso       = pytz.timezone("America/Sao_Paulo")
hoje_agora = datetime.now(fuso)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas.")
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

def _cookie_get(key):
    try:
        val = cookies[key]
        return val if val else ""
    except Exception:
        return ""

def _cookie_set(key, val):
    try:
        cookies[key] = val
        cookies.save()
    except Exception:
        pass

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

def user_id():
    return st.session_state.usuario["id"]

def verificar_perfil():
    try:
        res = supabase.table("perfis").select("telefone,cidade").eq("user_id", user_id()).execute()
        return bool(res.data and res.data[0].get("telefone") and res.data[0].get("cidade"))
    except Exception:
        return False

def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    supabase.table("historico_treinos").insert({
        "user_id": user_id(), "exercicio_id": ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes": detalhes, "tipo": tipo,
    }).execute()

def extrair_stats(df):
    if df.empty or "detalhes" not in df.columns:
        return 0.0, 0
    km = df["detalhes"].str.extract(r"([\d.]+)km").astype(float).sum()[0]
    mn = df["detalhes"].str.extract(r"(\d+)min").astype(float).sum()[0]
    return (float(km) if not pd.isna(km) else 0.0), (int(mn) if not pd.isna(mn) else 0)

def rodape():
    st.divider()
    st.caption("Duvidas: nabevia@gmail.com")

# TELAS PRE-LOGIN

def tela_login():
    st.title("PyTrain PRO")
    st.caption("Seu treino, sua evolucao.")
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
                        st.success("Link enviado para " + email_reset)
                    except Exception as e:
                        st.error("Erro: " + str(e))
                else:
                    st.warning("Digite um email valido.")

def tela_definir_senha(access_token, refresh_token):
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.title("Ativar conta")
        st.caption("Crie sua senha para comecar.")
        with st.form("form_definir_senha"):
            nova = st.text_input("Nova senha", type="password", placeholder="minimo 8 caracteres")
            conf = st.text_input("Confirmar senha", type="password")
            ok   = st.form_submit_button("Ativar conta", use_container_width=True)
        if ok:
            if not nova or len(nova) < 8:
                st.warning("Minimo 8 caracteres.")
                return
            if nova != conf:
                st.error("Senhas nao coincidem.")
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
                st.error("Erro: " + str(e))

def tela_completar_perfil():
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.title("Bem-vinda!")
        st.caption("Complete seu perfil para continuar.")
        with st.form("form_perfil"):
            nome_p   = st.text_input("Nome completo", placeholder="Seu nome")
            telefone = st.text_input("Telefone com DDD", placeholder="(28) 99999-9999", max_chars=20)
            cidade   = st.text_input("Cidade", placeholder="Onde voce mora")
            estado   = st.selectbox("Estado", [
                "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"], index=7)
            salvar = st.form_submit_button("Salvar e entrar", use_container_width=True)
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
                    st.error("Erro: " + str(e))

# FLUXO PRINCIPAL

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

# CABECALHO

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

if treinos_mes == 0:
    msg = "Vamos comecar o mes forte! 💪"
elif treinos_mes < 5:
    msg = str(treinos_mes) + " treino(s) este mes — continue! 🔥"
elif treinos_mes < 10:
    msg = str(treinos_mes) + " treinos — voce esta em chamas! 🚀"
else:
    msg = str(treinos_mes) + " treinos este mes. Lendaria! 🏆"

st.subheader(emoji_hora + " " + saudacao + ", " + nome_usuario + "!")
st.caption(msg)

col_sair, _ = st.columns([1, 3])
with col_sair:
    if st.button("Sair", key="btn_sair"):
        fazer_logout()

st.divider()
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Perfil"])

# ABA 1 - TREINO

with aba1:
    if not st.session_state.treino_ativo:
        serie = st.radio("Serie", ["A", "B", "C", "D"], horizontal=True, label_visibility="collapsed")

        exs = supabase.table("exercicios").select("id,nome,series,repeticoes,peso_kg")\
            .eq("serie_tipo", serie).eq("user_id", user_id()).execute()

        if exs.data:
            st.caption("SERIE " + serie + " - " + str(len(exs.data)) + " EXERCICIOS")
            for i, ex in enumerate(exs.data, 1):
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.info("**" + str(i) + ". " + ex["nome"] + "** — " + str(ex["series"]) + "x" + str(ex["repeticoes"]) + " · " + str(ex["peso_kg"]) + "kg")
                with c2:
                    if st.button("X", key="del_" + str(ex["id"]), help="Remover"):
                        supabase.table("exercicios").delete().eq("id", ex["id"]).execute()
                        st.rerun()
            pode_iniciar = True
        else:
            st.caption("SERIE " + serie + " - VAZIA")
            pode_iniciar = False

        with st.expander("+ Adicionar exercicio — Serie " + serie, expanded=not pode_iniciar):
            with st.form("form_add_" + serie):
                r_nome = st.text_input("Nome", placeholder="Ex: Supino Reto")
                c1, c2, c3 = st.columns(3)
                r_peso   = c1.number_input("Peso kg", value=0, min_value=0)
                r_series = c2.number_input("Series",  value=3, min_value=1)
                r_reps   = c3.number_input("Reps",    value=12, min_value=1)
                if st.form_submit_button("Adicionar", use_container_width=True):
                    if r_nome.strip():
                        dup = supabase.table("exercicios").select("id")\
                            .ilike("nome", r_nome.strip()).eq("serie_tipo", serie)\
                            .eq("user_id", user_id()).execute()
                        if dup.data:
                            st.warning("'" + r_nome + "' ja existe na Serie " + serie)
                        else:
                            supabase.table("exercicios").insert({
                                "user_id": user_id(), "nome": r_nome.strip(),
                                "serie_tipo": serie, "peso_kg": r_peso,
                                "series": r_series, "repeticoes": r_reps,
                            }).execute()
                            st.success("'" + r_nome + "' adicionado!")
                            st.rerun()
                    else:
                        st.warning("Digite o nome.")

        if st.button("Iniciar Serie " + serie, use_container_width=True, disabled=not pode_iniciar):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual  = serie
            st.session_state.indice_ex    = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()

    else:
        res = supabase.table("exercicios").select("*")\
            .eq("serie_tipo", st.session_state.serie_atual).eq("user_id", user_id()).execute()

        if not res.data:
            st.warning("Nenhum exercicio nesta serie.")
            if st.button("Voltar"):
                st.session_state.treino_ativo = False
                st.rerun()
        else:
            total = len(res.data)
            idx   = st.session_state.indice_ex

            if idx >= total:
                st.session_state.treino_ativo = False
                st.balloons()
                st.success("Treino concluido!")
                st.rerun()

            ex  = res.data[idx]
            pct = int((idx / total) * 100)

            st.caption("SERIE " + st.session_state.serie_atual + " — " + str(idx+1) + " / " + str(total))
            st.progress(pct)
            st.subheader(ex["nome"])

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg",   value=int(ex["peso_kg"]),   step=1, key="p" + str(idx))
            s = c2.number_input("Sets", value=int(ex["series"]),     step=1, key="s" + str(idx))
            r = c3.number_input("Reps", value=int(ex["repeticoes"]), step=1, key="r" + str(idx))

            elapsed = int(time.time() - st.session_state.inicio_timer)
            m, sg   = divmod(elapsed, 60)
            st.metric("Tempo de treino", str(m).zfill(2) + ":" + str(sg).zfill(2))

            c_prox, c_cancel = st.columns(2)
            if c_prox.button("Proximo", use_container_width=True):
                registrar_historico(ex["id"], str(p) + "kg | " + str(s) + "x" + str(r) + " | " + str(elapsed//60) + "min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex["id"]).execute()
                st.session_state.indice_ex += 1
                st.rerun()
            if c_cancel.button("Cancelar", use_container_width=True):
                st.session_state.treino_ativo = False
                st.rerun()

            time.sleep(1)
            st.rerun()

    rodape()

# ABA 2 - CARDIO

with aba2:
    if not st.session_state.cardio_ativo:
        st.caption("CONFIGURAR ESTEIRA")
        modo = st.radio("Modo", ["Distancia (km)", "Numero de ciclos"], horizontal=True, label_visibility="collapsed")

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Min. Andando",  value=5.0, step=1.0)
        v_anda  = c1.number_input("Vel. Andando",  value=5.0, step=0.5)
        t_corre = c2.number_input("Min. Correndo", value=2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo", value=9.0, step=0.5)

        dist_ciclo = (v_anda*(t_anda/60)) + (v_corre*(t_corre/60))
        if dist_ciclo <= 0:
            st.warning("Verifique velocidades e tempos.")
            st.stop()

        if modo == "Distancia (km)":
            dist_alvo = st.number_input("Meta em km", value=5.0, step=0.5, min_value=0.1)
            n_ciclos  = max(1, round(dist_alvo / dist_ciclo))
        else:
            n_ciclos  = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos

        km_est  = dist_ciclo * n_ciclos
        min_est = int(n_ciclos * (t_anda + t_corre))
        st.info(str(n_ciclos) + " ciclos · ~" + str(round(km_est,2)) + " km · ~" + str(min_est) + " min")

        if st.button("Iniciar cardio", use_container_width=True):
            etapas = []
            for i in range(int(n_ciclos)):
                etapas += [
                    ("Caminhada " + str(i+1) + "/" + str(int(n_ciclos)), int(t_anda*60), v_anda),
                    ("Corrida " + str(i+1) + "/" + str(int(n_ciclos)),   int(t_corre*60), v_corre),
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
                registrar_historico(None, "Interrompido: " + str(round(st.session_state.dist_real,2)) + "km | " + str(tf) + "min", tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.rerun()

        if idx >= len(et):
            if not st.session_state.cardio_salvo:
                tf = int((time.time()-st.session_state.t_cardio_start)/60)
                registrar_historico(None, "Concluido: " + str(round(st.session_state.dist_real,2)) + "km | " + str(tf) + "min", tipo="cardio")
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.balloons()
            st.success("Objetivo concluido!")
            st.rerun()

        nome_et, _, vel_et = et[idx]
        seg = p["seg_restantes"]; m, s = divmod(seg, 60)
        pct = int((st.session_state.dist_real / da) * 100) if da > 0 else 0

        st.subheader(nome_et)
        st.progress(min(pct, 100))
        st.metric("Tempo restante", str(m).zfill(2) + ":" + str(s).zfill(2))
        st.metric("Distancia", str(round(st.session_state.dist_real,2)) + " / " + str(round(da,2)) + " km")

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

# ABA 3 - PAINEL

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
            meses_n = {1:"Janeiro",2:"Fevereiro",3:"Marco",4:"Abril",5:"Maio",6:"Junho",
                       7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
            meses_d = sorted(df[df["data_execucao"].dt.year==ano_sel]["data_execucao"].dt.month.unique(), reverse=True)
            mes_sel = c2.selectbox("Mes", meses_d, format_func=lambda x: meses_n[x])

            df_f = df[(df["data_execucao"].dt.month==mes_sel)&(df["data_execucao"].dt.year==ano_sel)]
            km_f, min_f = extrair_stats(df_f)

            c1, c2, c3 = st.columns(3)
            c1.metric("Treinos", len(df_f))
            c2.metric("Distancia", str(round(km_f,1)) + " km")
            c3.metric("Tempo", str(min_f) + " min")

            df_h = df[df["data_execucao"].dt.date == hoje_agora.date()]
            ini_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
            df_s = df[df["data_execucao"] >= ini_sem]

            with st.expander("Hoje e esta semana"):
                km_h, min_h = extrair_stats(df_h)
                km_s, min_s = extrair_stats(df_s)
                col1, col2 = st.columns(2)
                col1.metric("Hoje", str(len(df_h)) + " ativ · " + str(round(km_h,1)) + "km · " + str(min_h) + "min")
                col2.metric("Esta semana", str(len(df_s)) + " ativ · " + str(round(km_s,1)) + "km · " + str(min_s) + "min")

            st.caption("ATIVIDADES — " + meses_n[mes_sel].upper())
            if df_f.empty:
                st.info("Nenhum registro em " + meses_n[mes_sel])
            else:
                df_show = df_f.copy()
                if "exercicios.nome" not in df_show.columns:
                    df_show["exercicios.nome"] = "Cardio"
                df_show["exercicios.nome"] = df_show["exercicios.nome"].fillna("Cardio")
                df_show["Data"] = df_show["data_execucao"].dt.strftime("%d/%m %H:%M")
                st.dataframe(df_show[["Data","exercicios.nome","detalhes"]].rename(
                    columns={"exercicios.nome":"Exercicio","detalhes":"Detalhes"}),
                    use_container_width=True, hide_index=True)

            if st.button("Apagar historico completo", use_container_width=True):
                st.session_state["confirmar_historico"] = True
            if st.session_state.get("confirmar_historico"):
                st.error("Esta acao apaga todo o seu historico permanentemente.")
                c1, c2 = st.columns(2)
                if c1.button("Sim, apagar"):
                    supabase.table("historico_treinos").delete().eq("user_id", user_id()).execute()
                    st.session_state["confirmar_historico"] = False
                    st.success("Historico apagado.")
                    st.rerun()
                if c2.button("Cancelar"):
                    st.session_state["confirmar_historico"] = False
                    st.rerun()

    except Exception as e:
        st.error("Erro: " + str(e))

    rodape()

# ABA 4 - PERFIL

with aba4:
    email_atual = st.session_state.usuario["email"]
    nome_atual  = st.session_state.usuario["nome"]

    try:
        rp = supabase.table("perfis").select("nome,telefone,cidade,estado").eq("user_id", user_id()).execute()
        dp = rp.data[0] if rp.data else {}
    except Exception:
        dp = {}

    st.subheader("Meu Perfil")
    c1, c2 = st.columns(2)
    c1.metric("Nome", dp.get("nome", nome_atual))
    c2.metric("Telefone", dp.get("telefone", "—"))
    c1.metric("Email", email_atual)
    c2.metric("Cidade / Estado", dp.get("cidade","—") + " · " + dp.get("estado","—"))

    st.divider()

    with st.expander("Editar dados pessoais"):
        with st.form("form_dados"):
            ed_nome   = st.text_input("Nome", value=dp.get("nome", nome_atual))
            ed_tel    = st.text_input("Telefone", value=dp.get("telefone",""), placeholder="(28) 99999-9999")
            ed_cidade = st.text_input("Cidade", value=dp.get("cidade",""))
            ests      = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                         "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
            idx_e     = ests.index(dp.get("estado","ES")) if dp.get("estado","ES") in ests else 7
            ed_estado = st.selectbox("Estado", ests, index=idx_e)
            if st.form_submit_button("Salvar", use_container_width=True):
                if ed_nome.strip() and ed_tel.strip() and ed_cidade.strip():
                    try:
                        supabase.auth.update_user({"data": {"nome": ed_nome.strip()}})
                        supabase.table("perfis").upsert({
                            "user_id": user_id(), "nome": ed_nome.strip(),
                            "telefone": ed_tel.strip(), "cidade": ed_cidade.strip(), "estado": ed_estado,
                        }).execute()
                        st.session_state.usuario["nome"] = ed_nome.strip()
                        st.success("Dados atualizados!")
                        st.rerun()
                    except Exception as e:
                        st.error("Erro: " + str(e))
                else:
                    st.warning("Preencha todos os campos.")

    with st.expander("Alterar email"):
        st.caption("Voce recebera links de confirmacao no email atual e no novo.")
        with st.form("form_email"):
            novo_email  = st.text_input("Novo email", placeholder="novo@email.com")
            senha_email = st.text_input("Sua senha atual", type="password")
            if st.form_submit_button("Enviar confirmacoes", use_container_width=True):
                if not novo_email.strip() or "@" not in novo_email:
                    st.warning("Email invalido.")
                elif not senha_email:
                    st.warning("Digite sua senha.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_email})
                        supabase.auth.update_user({"email": novo_email.strip()})
                        st.success("Confirmacoes enviadas! Verifique ambos os emails.")
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    with st.expander("Alterar senha"):
        with st.form("form_senha"):
            s_antiga = st.text_input("Senha atual", type="password")
            s_nova   = st.text_input("Nova senha", type="password", placeholder="minimo 8 caracteres")
            s_conf   = st.text_input("Confirmar nova senha", type="password")
            if st.form_submit_button("Salvar senha", use_container_width=True):
                if not s_antiga:
                    st.warning("Digite a senha atual.")
                elif len(s_nova) < 8:
                    st.warning("Minimo 8 caracteres.")
                elif s_nova != s_conf:
                    st.error("Senhas nao coincidem.")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email_atual, "password": s_antiga})
                        supabase.auth.update_user({"password": s_nova})
                        st.success("Senha alterada!")
                    except Exception:
                        st.error("Senha atual incorreta.")

    st.divider()

    with st.expander("Apagar minha conta"):
        st.warning("Acao irreversivel. Todos os dados serao removidos permanentemente.")
        with st.form("form_del_conta"):
            conf_txt   = st.text_input("Digite APAGAR para confirmar", placeholder="APAGAR")
            senha_conf = st.text_input("Sua senha", type="password")
            if st.form_submit_button("Apagar conta", use_container_width=True):
                if conf_txt.strip().upper() != "APAGAR":
                    st.error("Digite APAGAR em maiusculas.")
                elif not senha_conf:
                    st.warning("Digite sua senha.")
                else:
                    try:
                        rl    = supabase.auth.sign_in_with_password({"email": email_atual, "password": senha_conf})
                        token = rl.session.access_token
                        import urllib.request as _ur, json as _js, ssl as _ssl
                        req = _ur.Request(
                            SUPABASE_URL + "/functions/v1/delete-account",
                            data=b"{}",
                            headers={"Authorization": "Bearer " + token, "apikey": SUPABASE_KEY, "Content-Type": "application/json"},
                            method="POST",
                        )
                        with _ur.urlopen(req, context=_ssl.create_default_context(), timeout=15) as rr:
                            body = _js.loads(rr.read())
                        if body.get("success"):
                            st.success("Conta apagada. Ate logo!")
                            time.sleep(1)
                            fazer_logout()
                        else:
                            st.error("Erro: " + str(body.get("error", body)))
                    except Exception as e:
                        st.error("Senha incorreta." if "invalid" in str(e).lower() else "Erro: " + str(e))

    rodape()