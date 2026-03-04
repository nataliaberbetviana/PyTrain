import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime
import pytz  # Para corrigir o fuso horário
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Fuso horário de Brasília
fuso = pytz.timezone('America/Sao_Paulo')

# CSS para garantir a horizontalidade no mobile e botões grandes
st.markdown("""
    <style>
    [data-testid="column"] { min-width: 14% !important; }
    .stCheckbox { display: flex; justify-content: center; }
    div.stButton > button { height: 3.5em; width: 100%; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)


# --- FUNÇÕES ---
def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    agora = datetime.now(fuso).isoformat()
    supabase.table("historico_treinos").insert({
        "exercicio_id": ex_id, "data_execucao": agora,
        "detalhes": detalhes, "tipo": tipo
    }).execute()


# --- ABA 1: TREINO DINÂMICO ---
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📜 Histórico", "⚙️ Menu"])

with aba1:
    # 1. Checklist Semanal Manual
    st.subheader("🗓️ Checklist Semanal")
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    # Colunas forçadas a serem pequenas para caberem lado a lado
    cols = st.columns(7)
    for i, dia in enumerate(dias):
        st.session_state[f"manual_{dia}"] = cols[i].checkbox(dia, key=f"c_{dia}")

    st.divider()

    # 2. Seleção de Série
    serie = st.radio("Selecione a Série", ["A", "B", "C", "D"], horizontal=True)

    # Lógica de Fluxo de Exercícios (Um por um)
    if st.button(f"INICIAR SÉRIE {serie}"):
        st.session_state.treino_ativo = True
        st.session_state.indice_ex = 0
        st.session_state.inicio_timer = time.time()

    if st.session_state.get("treino_ativo"):
        res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]

            # Card do Exercício Atual
            st.markdown(f"### Exercício {st.session_state.indice_ex + 1} de {len(res.data)}")
            st.info(f"🏋️ **{ex_atual['nome']}**")

            c1, c2, c3 = st.columns(3)
            peso = c1.number_input("Carga (kg)", value=int(ex_atual['peso_kg']), step=1)
            sets = c2.number_input("Séries", value=int(ex_atual['series']), step=1)
            reps = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1)

            # Timer do exercício
            tempo_decorrido = int(time.time() - st.session_state.inicio_timer)
            st.write(f"⏱️ Tempo neste exercício: {tempo_decorrido // 60:02d}:{tempo_decorrido % 60:02d}")

            if st.button("PRÓXIMO EXERCÍCIO ➡️"):
                registrar_historico(ex_atual['id'], f"{peso}kg | {sets}x{reps}")
                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                    st.session_state.inicio_timer = time.time()
                    st.rerun()
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.success("Série concluída!")

# --- ABA 2: CARDIO (CONTROLE TOTAL) ---
with aba2:
    st.header("🏃 Controle de Esteira")

    col1, col2 = st.columns(2)
    t_anda = col1.number_input("Minutos Andando", value=5, step=1)
    v_anda = col1.number_input("Velocidade Andando", value=5.0, step=0.5)  # Mínimo 5.0

    t_corre = col2.number_input("Minutos Correndo", value=0, step=1)  # Pode zerar
    v_corre = col2.number_input("Velocidade Correndo", value=9.0, step=0.5)

    if st.button("🚀 INICIAR"):
        st.session_state.cardio_rodando = True
        ph = st.empty()

        # Etapas (Se tempo > 0)
        etapas = []
        if t_anda > 0: etapas.append(("🚶 Caminhada", t_anda * 60, v_anda))
        if t_corre > 0: etapas.append(("⚡ Corrida", t_corre * 60, v_corre))

        for nome, t, v in etapas:
            while t > 0:
                if st.button("🛑 ENCERRAR AGORA", key="stop_cardio"):
                    st.session_state.cardio_rodando = False
                    st.warning("Cardio interrompido.")
                    st.stop()

                m, s = divmod(t, 60)
                ph.header(f"{nome} | {m:02d}:{s:02d} | {v} km/h")
                time.sleep(1)
                t -= 1
        st.success("Finalizado!")