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

# Fuso horário de Brasília
fuso = pytz.timezone('America/Sao_Paulo')
hoje = datetime.now(fuso)

# Estética CSS para Mobile
st.markdown("""
    <style>
    [data-testid="column"] { min-width: 14% !important; }
    div.stButton > button { height: 3.5em; width: 100%; font-size: 18px !important; font-weight: bold; }
    .stCheckbox { display: flex; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# --- FUNÇÕES DE APOIO ---
def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    agora = datetime.now(fuso).isoformat()
    supabase.table("historico_treinos").insert({
        "exercicio_id": ex_id,
        "data_execucao": agora,
        "detalhes": detalhes,
        "tipo": tipo
    }).execute()


# --- INTERFACE PRINCIPAL ---
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📜 Histórico", "⚙️ Menu"])

# --- ABA 1: TREINO (ORDEM CORRIGIDA) ---
with aba1:
    st.subheader("🗓️ Checklist Semanal")
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    cols = st.columns(7)
    for i, dia in enumerate(dias):
        st.session_state[f"manual_{dia}"] = cols[i].checkbox(dia, key=f"c_{dia}")

    st.divider()

    # IMPORTANTE: Definimos 'serie' ANTES de usar no botão de iniciar
    serie = st.radio("Série de hoje:", ["A", "B", "C", "D"], horizontal=True)  #

    if st.button(f"🚀 INICIAR SÉRIE {serie}"):
        st.session_state.treino_ativo = True
        st.session_state.indice_ex = 0
        st.session_state.inicio_timer = time.time()
        st.rerun()

    if st.session_state.get("treino_ativo"):
        res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]
            st.markdown(f"### Exercício {st.session_state.indice_ex + 1} de {len(res.data)}")
            st.info(f"🏋️ **{ex_atual['nome']}**")

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Carga (kg)", value=int(ex_atual['peso_kg']), step=1,
                                key=f"p_{st.session_state.indice_ex}")
            s = c2.number_input("Séries", value=int(ex_atual['series']), step=1, key=f"s_{st.session_state.indice_ex}")
            r = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1,
                                key=f"r_{st.session_state.indice_ex}")

            # Cronômetro Visual
            timer_place = st.empty()
            tempo_decorrido_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_decorrido_seg, 60)
            timer_place.markdown(f"⏱️ Tempo: **{m:02d}:{seg:02d}**")

            if st.button("PRÓXIMO EXERCÍCIO ➡️", use_container_width=True):
                tempo_final_min = max(1, tempo_decorrido_seg // 60)
                registrar_historico(ex_atual['id'], f"{p}kg | {s}x{r} | {tempo_final_min}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual['id']).execute()

                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                    st.session_state.inicio_timer = time.time()
                    st.rerun()
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.success("Série concluída!")
                    st.rerun()

            time.sleep(1)
            st.rerun()  # Atualiza o relógio