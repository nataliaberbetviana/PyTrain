import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

# Fuso horário Brasília
fuso = pytz.timezone('America/Sao_Paulo')
hoje_agora = datetime.now(fuso)

# --- CSS AVANÇADO ---
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
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
# Certifique-se de que as chaves existam no .env ou Secrets do Streamlit
try:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erro na conexão com Supabase. Verifique suas credenciais.")


def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    agora = datetime.now(fuso).isoformat()
    dados = {
        "data_execucao": agora,
        "detalhes": detalhes,
        "tipo": tipo
    }
    if ex_id: dados["exercicio_id"] = ex_id
    supabase.table("historico_treinos").insert(dados).execute()


# --- INTERFACE ---
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])

# --- ABA 1: TREINO ---
with aba1:
    if not st.session_state.get("treino_ativo"):
        st.subheader("Escolha sua Série")
        serie = st.radio("Selecione:", ["A", "B", "C", "D"], horizontal=True)

        if st.button(f"🚀 INICIAR TREINO - SÉRIE {serie}"):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual = serie
            st.session_state.indice_ex = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()
    else:
        res = supabase.table("exercicios").select("*").eq("serie_tipo", st.session_state.serie_atual).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]

            st.markdown(f"""
                <div class="foco-container">
                    <h4 style="color:gray; margin:0;">Série {st.session_state.serie_atual} | {st.session_state.indice_ex + 1} de {len(res.data)}</h4>
                    <h1 style="color:#e066ff; margin:10px 0; font-size: 28px;">{ex_atual['nome']}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg", value=int(ex_atual['peso_kg']), step=1, key=f"p_{ex_atual['id']}")
            s = c2.number_input("Sets", value=int(ex_atual['series']), step=1, key=f"s_{ex_atual['id']}")
            r = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1, key=f"r_{ex_atual['id']}")

            tempo_total_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_total_seg, 60)
            st.metric("TEMPO TOTAL", f"{m:02d}:{seg:02d}")

            if st.button("PRÓXIMO EXERCÍCIO ➡️"):
                registrar_historico(ex_atual['id'], f"{p}kg | {s}x{r} | {tempo_total_seg // 60}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual['id']).execute()

                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                st.rerun()

            if st.button("🛑 CANCELAR"):
                st.session_state.treino_ativo = False
                st.rerun()

# --- ABA 2: CARDIO ---
with aba2:
    if not st.session_state.get("cardio_ativo"):
        st.subheader("Configurar Esteira")
        c1, c2 = st.columns(2)
        t_anda = c1.number_input("Min. Andando", 5.0, step=1.0)
        v_anda = c1.number_input("Vel. Andando", 5.5, step=0.5)
        t_corre = c2.number_input("Min. Correndo", 2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo", 9.5, step=0.5)
        n_ciclos = st.number_input("Ciclos", 1, 20, 5)

        if st.button("🚀 INICIAR CARDIO"):
            st.session_state.cardio_ativo = True
            st.session_state.params_cardio = (n_ciclos, t_anda, v_anda, t_corre, v_corre)
            st.session_state.t_cardio_start = time.time()
            st.rerun()
    else:
        # Lógica simplificada de exibição (Cardio em execução)
        st.warning("Cardio em andamento... (O timer no Streamlit exige refresh contínuo)")
        if st.button("🛑 ENCERRAR CARDIO"):
            min_f = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Cardio: {min_f}min", tipo="cardio")
            st.session_state.cardio_ativo = False
            st.rerun()

# --- ABA 3: PAINEL ---
with aba3:
    st.header("📊 Performance")
    res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                    desc=True).execute()

    if res_h.data:
        df = pd.json_normalize(res_h.data)
        df['data_execucao'] = pd.to_datetime(df['data_execucao']).dt.tz_convert('America/Sao_Paulo')

        # Garantir que a coluna de nome existe
        nome_col = 'exercicios.nome' if 'exercicios.nome' in df.columns else 'nome_fallback'
        if 'nome_fallback' not in df.columns: df['nome_fallback'] = "🏃 Cardio"
        df[nome_col] = df[nome_col].fillna("🏃 Cardio")

        # Filtros
        anos = sorted(df['data_execucao'].dt.year.unique(), reverse=True)
        ano_sel = st.selectbox("Ano", anos)
        df_filtrado = df[df['data_execucao'].dt.year == ano_sel]

        st.dataframe(df_filtrado[['data_execucao', nome_col, 'detalhes']], use_container_width=True)

# --- ABA 4: CONFIG ---
with aba4:
    with st.expander("✨ Cadastrar Novo Exercício"):
        with st.form("add_ex"):
            n = st.text_input("Nome")
            s = st.selectbox("Série", ["A", "B", "C", "D"])
            if st.form_submit_button("Salvar"):
                supabase.table("exercicios").insert(
                    {"nome": n, "serie_tipo": s, "peso_kg": 0, "series": 3, "repeticoes": 12}).execute()
                st.rerun()

    if st.button("🗑️ Limpar Histórico"):
        # Filtro seguro para deletar tudo
        supabase.table("historico_treinos").delete().gt("id", -1).execute()
        st.success("Limpo!")
        st.rerun()