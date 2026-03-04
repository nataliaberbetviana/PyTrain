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
# FIX: load_dotenv() deve ser chamado ANTES de os.getenv()
# ─────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas no .env")
    st.stop()

# FIX: usar st.cache_resource para não recriar o cliente a cada rerun
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def registrar_historico(ex_id, detalhes: str, tipo: str = "musculacao") -> None:
    """Insere um registo no histórico de treinos."""
    supabase.table("historico_treinos").insert({
        "exercicio_id": ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes": detalhes,
        "tipo": tipo,
    }).execute()


def extrair_stats(dataframe: pd.DataFrame) -> tuple[float, int]:
    """Extrai km e minutos totais de um DataFrame de histórico."""
    if dataframe.empty or "detalhes" not in dataframe.columns:
        return 0.0, 0
    kms = dataframe["detalhes"].str.extract(r"([\d.]+)km").astype(float).sum()[0]
    mins = dataframe["detalhes"].str.extract(r"(\d+)min").astype(float).sum()[0]
    return (float(kms) if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)


# ─────────────────────────────────────────────
# INICIALIZAÇÃO DO SESSION STATE
# FIX: centralizar inicialização evita KeyError em qualquer aba
# ─────────────────────────────────────────────
defaults = {
    "treino_ativo": False,
    "serie_atual": "A",
    "indice_ex": 0,
    "inicio_timer": 0.0,
    "cardio_ativo": False,
    "params_cardio": None,
    "dist_real": 0.0,
    "t_cardio_start": 0.0,
    # FIX: flag para evitar double-save no cardio
    "cardio_salvo": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])


# ═══════════════════════════════════════════
# ABA 1 — TREINO
# ═══════════════════════════════════════════
with aba1:
    if not st.session_state.treino_ativo:
        st.subheader("Escolha sua Série")
        serie = st.radio("Selecione:", ["A", "B", "C", "D"], horizontal=True)

        if st.button(f"🚀 INICIAR TREINO — SÉRIE {serie}", use_container_width=True):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual = serie
            st.session_state.indice_ex = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()

    else:
        res = supabase.table("exercicios").select("*").eq("serie_tipo", st.session_state.serie_atual).execute()

        if not res.data:
            st.warning("Nenhum exercício cadastrado para esta série.")
            if st.button("Voltar"):
                st.session_state.treino_ativo = False
                st.rerun()
        else:
            total_ex = len(res.data)
            indice = st.session_state.indice_ex

            # FIX: guardar na hora certa — se já passou de todos, encerra
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
            p = c1.number_input("Kg",   value=int(ex_atual["peso_kg"]),    step=1, key=f"p_{indice}")
            s = c2.number_input("Sets", value=int(ex_atual["series"]),      step=1, key=f"s_{indice}")
            r = c3.number_input("Reps", value=int(ex_atual["repeticoes"]),  step=1, key=f"r_{indice}")

            # Cronómetro da sessão
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
                registrar_historico(
                    ex_atual["id"],
                    f"{p}kg | {s}x{r} | {tempo_total_seg // 60}min"
                )
                # Actualiza peso no catálogo
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual["id"]).execute()
                st.session_state.indice_ex += 1
                st.rerun()

            if col_cancel.button("🛑 CANCELAR", type="secondary", use_container_width=True):
                st.session_state.treino_ativo = False
                st.rerun()

            # FIX: time.sleep + rerun apenas para refrescar o cronómetro;
            #      colocado no FINAL da aba para não bloquear os botões acima.
            time.sleep(1)
            st.rerun()


# ═══════════════════════════════════════════
# ABA 2 — CARDIO
# FIX: loop bloqueante substituído por máquina de estados
#      para que o botão "Encerrar" funcione de verdade
# ═══════════════════════════════════════════
with aba2:
    if not st.session_state.cardio_ativo:
        st.subheader("Configurar Esteira")
        modo = st.radio("Objetivo:", ["Distância Alvo (km)", "Número de Ciclos"], horizontal=True)

        c1, c2 = st.columns(2)
        t_anda  = c1.number_input("Minutos Andando",  value=5.0,  step=1.0)
        v_anda  = c1.number_input("Vel. Andando",     value=5.0,  step=0.5)
        t_corre = c2.number_input("Minutos Correndo", value=2.0,  step=1.0)
        v_corre = c2.number_input("Vel. Correndo",    value=9.0,  step=0.5)

        dist_ciclo = (v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60))
        if dist_ciclo <= 0:
            st.warning("Verifique as velocidades e tempos configurados.")
            st.stop()

        if modo == "Distância Alvo (km)":
            dist_alvo = st.number_input("Meta (km)", value=5.0, step=0.5, min_value=0.1)
            n_ciclos  = max(1, round(dist_alvo / dist_ciclo))
        else:
            n_ciclos  = st.number_input("Ciclos", value=1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos

        st.info(f"Estimativa: **{n_ciclos} ciclos** → ~{dist_ciclo * n_ciclos:.2f} km")

        if st.button("🚀 INICIAR CARDIO", use_container_width=True):
            # Constrói lista de etapas: (nome, duração_seg, velocidade)
            etapas = []
            for i in range(int(n_ciclos)):
                etapas.append((f"🚶 Caminhada ({i+1}/{int(n_ciclos)})", int(t_anda * 60),  v_anda))
                etapas.append((f"⚡ Corrida   ({i+1}/{int(n_ciclos)})", int(t_corre * 60), v_corre))

            st.session_state.cardio_ativo    = True
            st.session_state.cardio_salvo    = False
            st.session_state.dist_real       = 0.0
            st.session_state.t_cardio_start  = time.time()
            st.session_state.params_cardio   = {
                "etapas":     etapas,
                "dist_alvo":  dist_alvo,
                "etapa_idx":  0,          # índice da etapa actual
                "seg_restantes": etapas[0][1] if etapas else 0,
            }
            st.rerun()

    else:
        params    = st.session_state.params_cardio
        etapas    = params["etapas"]
        dist_alvo = params["dist_alvo"]
        idx       = params["etapa_idx"]

        # ── Botão de encerramento antecipado ──────────────────────────
        if st.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(
                    None,
                    f"Interrompido: {st.session_state.dist_real:.2f}km | {t_final}min",
                    tipo="cardio"
                )
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.rerun()

        # ── Cardio concluído ──────────────────────────────────────────
        if idx >= len(etapas):
            if not st.session_state.cardio_salvo:
                t_final = int((time.time() - st.session_state.t_cardio_start) / 60)
                registrar_historico(
                    None,
                    f"Concluído: {st.session_state.dist_real:.2f}km | {t_final}min",
                    tipo="cardio"
                )
                st.session_state.cardio_salvo = True
            st.session_state.cardio_ativo = False
            st.success("🎉 Objetivo concluído!")
            st.balloons()
            st.rerun()

        # ── Display da etapa actual ───────────────────────────────────
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

        # ── Avança 1 segundo por rerun ────────────────────────────────
        time.sleep(1)
        st.session_state.dist_real += vel_etapa / 3600  # km por segundo

        if seg <= 1:
            # Passa para a próxima etapa
            params["etapa_idx"] += 1
            next_idx = params["etapa_idx"]
            if next_idx < len(etapas):
                params["seg_restantes"] = etapas[next_idx][1]
            else:
                params["seg_restantes"] = 0
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
        res_h = (
            supabase.table("historico_treinos")
            .select("*, exercicios(nome)")
            .order("data_execucao", desc=True)
            .execute()
        )

        if not res_h.data:
            st.info("Nenhum treino registado ainda.")
        else:
            df = pd.json_normalize(res_h.data)
            df["data_execucao"] = pd.to_datetime(df["data_execucao"]).dt.tz_convert("America/Sao_Paulo")

            # ── Filtro de período ─────────────────────────────────────
            st.subheader("📅 Filtrar Período")
            col_f1, col_f2 = st.columns(2)

            anos = sorted(df["data_execucao"].dt.year.unique(), reverse=True)
            ano_sel = col_f1.selectbox("Ano", anos)

            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março",    4: "Abril",
                5: "Maio",    6: "Junho",     7: "Julho",    8: "Agosto",
                9: "Setembro",10: "Outubro",  11: "Novembro",12: "Dezembro",
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

            # ── Resumo do mês ─────────────────────────────────────────
            st.markdown(f"#### 📈 Resumo de {meses_nomes[mes_sel]}/{ano_sel}")
            c1, c2, c3 = st.columns(3)
            km_f, min_f = extrair_stats(df_filtrado)
            c1.metric("Treinos",       len(df_filtrado))
            c2.metric("Distância",     f"{km_f:.2f} km")
            c3.metric("Tempo Total",   f"{min_f} min")

            # ── Hoje e esta semana ────────────────────────────────────
            df_hoje   = df[df["data_execucao"].dt.date == hoje_agora.date()]
            inicio_sem = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            df_semana = df[df["data_execucao"] >= inicio_sem]

            with st.expander("📌 Ver Hoje e Esta Semana"):
                km_h, min_h = extrair_stats(df_hoje)
                km_s, min_s = extrair_stats(df_semana)
                st.markdown(f"""
**Hoje:** {len(df_hoje)} atividades | {km_h:.2f} km | {min_h} min  
**Esta Semana:** {len(df_semana)} atividades | {km_s:.2f} km | {min_s} min
                """)

            # ── Lista completa do mês ─────────────────────────────────
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

                st.dataframe(
                    df_show[["Data", "exercicios.nome", "detalhes"]],
                    use_container_width=True,
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")


# ═══════════════════════════════════════════
# ABA 4 — CONFIGURAÇÕES
# ═══════════════════════════════════════════
with aba4:
    st.header("⚙️ Gerenciamento do Sistema")

    # ── Cadastrar exercício ───────────────────────────────────────────
    with st.expander("✨ Cadastrar Novo Exercício"):
        with st.form("form_cadastro"):
            n_nome  = st.text_input("Nome do Exercício")
            n_serie = st.selectbox("Série", ["A", "B", "C", "D"])
            n_peso  = st.number_input("Peso Inicial (kg)", value=0, min_value=0)
            n_series = st.number_input("Séries padrão", value=3, min_value=1)
            n_reps   = st.number_input("Repetições padrão", value=12, min_value=1)

            if st.form_submit_button("Salvar no Catálogo"):
                if n_nome.strip():
                    # FIX: verificar duplicidade antes de inserir
                    existe = (
                        supabase.table("exercicios")
                        .select("id")
                        .ilike("nome", n_nome.strip())
                        .execute()
                    )
                    if existe.data:
                        st.warning(f"Exercício '{n_nome}' já existe no catálogo.")
                    else:
                        supabase.table("exercicios").insert({
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

    # ── Editar / Remover exercícios ───────────────────────────────────
    with st.expander("📝 Editar ou Remover Exercícios"):
        res_cat = supabase.table("exercicios").select("*").order("serie_tipo").execute()
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

    # ── Zona de perigo ────────────────────────────────────────────────
    st.subheader("🚨 Zona de Perigo")
    st.warning("Estas acções são irreversíveis.")

    col_h, col_p = st.columns(2)

    # FIX: confirmação antes de apagar para evitar cliques acidentais
    if col_h.button("🗑️ Apagar Todo Histórico"):
        st.session_state["confirmar_historico"] = True

    if st.session_state.get("confirmar_historico"):
        st.error("Tens a certeza? Esta acção apaga **todo** o histórico.")
        c_sim, c_nao = st.columns(2)
        if c_sim.button("✅ Sim, apagar"):
            supabase.table("historico_treinos").delete().neq(
                "id", "00000000-0000-0000-0000-000000000000"
            ).execute()
            st.session_state["confirmar_historico"] = False
            st.success("Histórico limpo.")
            st.rerun()
        if c_nao.button("❌ Cancelar"):
            st.session_state["confirmar_historico"] = False
            st.rerun()

    if col_p.button("🔄 Resetar Todos os Pesos"):
        supabase.table("exercicios").update({"peso_kg": 0}).neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()
        st.success("Pesos resetados para 0 kg!")
        st.rerun()