import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

# Estética CSS para botões maiores no celular
st.markdown("""
    <style>
    div.stButton > button:first-child { height: 3em; width: 100%; font-size: 18px; font-weight: bold; }
    .stNumberInput div div input { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")


@st.cache_resource
def init_connection():
    return create_client(URL, KEY)


supabase = init_connection()


# --- FUNÇÕES DE APOIO ---
def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    dados = {
        "exercicio_id": ex_id,
        "data_execucao": datetime.now().isoformat(),
        "detalhes": detalhes, "tipo": tipo
    }
    supabase.table("historico_treinos").insert(dados).execute()


# --- INTERFACE PRINCIPAL ---
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📜 Histórico", "⚙️ Menu"])

# --- ABA 1: TREINO DE MUSCULAÇÃO ---
with aba1:
    serie = st.radio("Qual série hoje?", ["A", "B", "C"], horizontal=True)
    res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()

    if not res.data:
        st.warning(f"Nenhum exercício na Série {serie}")
    else:
        with st.form(f"form_treino_{serie}"):
            for ex in res.data:
                st.subheader(f"▶ {ex['nome']}")
                c1, c2, c3 = st.columns(3)
                p = c1.number_input("Kg", value=int(ex['peso_kg']), key=f"p_{ex['id']}")
                s = c2.number_input("Séries", value=int(ex['series']), key=f"s_{ex['id']}")
                r = c3.number_input("Reps", value=int(ex['repeticoes']), key=f"r_{ex['id']}")
                st.divider()

            if st.form_submit_button("CONCLUIR TREINO"):
                for ex in res.data:
                    p_val = st.session_state[f"p_{ex['id']}"]
                    s_val = st.session_state[f"s_{ex['id']}"]
                    r_val = st.session_state[f"r_{ex['id']}"]

                    # Atualiza peso no catálogo e salva histórico
                    supabase.table("exercicios").update({"peso_kg": p_val}).eq("id", ex['id']).execute()
                    registrar_historico(ex['id'], f"{p_val}kg | {s_val}x{r_val}")
                st.success("✅ Treino salvo! Bom descanso, Natália!")

# --- ABA 2: CARDIO (ESTEIRA) ---
with aba2:
    st.header("🏃 Esteira Intervalada (HIIT)")

    # 1. Configuração dos Tempos e Velocidades
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚶 Andando")
        t_anda = st.number_input("Minutos Andando", value=2, step=1, key="t_anda")
        v_anda = st.number_input("Velocidade Andando", value=5.5, step=0.5, key="v_anda")

    with col2:
        st.subheader("⚡ Correndo")
        t_corre = st.number_input("Minutos Correndo", value=1, step=1, key="t_corre")
        v_corre = st.number_input("Velocidade Correndo", value=9.0, step=0.5, key="v_corre")

    st.divider()

    # 2. Configuração do Ciclo
    col3, col4 = st.columns(2)
    n_ciclos = col3.number_input("Quantos Ciclos (Repetições)?", value=5, step=1)

    t_total = (t_anda + t_corre) * n_ciclos
    st.info(f"⏱️ Tempo Total Estimado: **{t_total} minutos**")

    if st.button("🚀 INICIAR HIIT"):
        placeholder = st.empty()
        progresso = st.progress(0)

        for i in range(n_ciclos):
            # Fase 1: Andando
            tempo_seg = t_anda * 60
            while tempo_seg > 0:
                mins, secs = divmod(tempo_seg, 60)
                placeholder.markdown(f"""
                    <div style="text-align: center; border: 3px solid #66ffe0; padding: 20px; border-radius: 15px; background-color: #1e1e1e;">
                        <h4 style="color: #66ffe0;">Ciclo {i + 1} de {n_ciclos}</h4>
                        <h2 style="color: white;">🚶 ANDANDO</h2>
                        <h1 style="font-size: 80px; color: #66ffe0;">{mins:02d}:{secs:02d}</h1>
                        <h3 style="color: white;">Velocidade: {v_anda} km/h</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                tempo_seg -= 1

            # Fase 2: Correndo
            tempo_seg = t_corre * 60
            while tempo_seg > 0:
                mins, secs = divmod(tempo_seg, 60)
                placeholder.markdown(f"""
                    <div style="text-align: center; border: 3px solid #e066ff; padding: 20px; border-radius: 15px; background-color: #1e1e1e;">
                        <h4 style="color: #e066ff;">Ciclo {i + 1} de {n_ciclos}</h4>
                        <h2 style="color: white;">⚡ CORRENDO</h2>
                        <h1 style="font-size: 80px; color: #e066ff;">{mins:02d}:{secs:02d}</h1>
                        <h3 style="color: white;">Velocidade: {v_corre} km/h</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                tempo_seg -= 1

            # Atualiza barra de progresso geral
            progresso.progress((i + 1) / n_ciclos)

        placeholder.success("🔥 HIIT Concluído! Você é fera!")
        registrar_historico(None, f"HIIT: {n_ciclos} ciclos de {t_anda}min/{t_corre}min", tipo="cardio")

# --- ABA 3: HISTÓRICO ---
with aba3:
    st.header("📊 Evolução Recente")
    res_h = supabase.table("historico_treinos").select("data_execucao, detalhes, exercicios(nome)").order(
        "data_execucao", desc=True).limit(15).execute()
    if res_h.data:
        # Organizando dados para tabela
        dados_limpos = []
        for r in res_h.data:
            nome = r['exercicios']['nome'] if r['exercicios'] else "🏃 Cardio"
            data = datetime.fromisoformat(r['data_execucao']).strftime("%d/%m %H:%M")
            dados_limpos.append({"Data": data, "Exercício": nome, "Detalhes": r['detalhes']})
        st.table(pd.DataFrame(dados_limpos))

# --- ABA 4: CONFIGURAÇÕES ---
with aba4:
    st.header("⚙️ Gerenciamento do Sistema")

    # 1. Adicionar Novo Exercício (Com suporte a Série D)
    with st.expander("✨ Cadastrar Novo Exercício"):
        with st.form("form_cadastro"):
            n_nome = st.text_input("Nome do Exercício")
            # Adicionei "D" nas opções abaixo
            n_serie = st.selectbox("Série", ["A", "B", "C", "D"])
            n_peso = st.number_input("Peso Inicial (kg)", value=0)
            if st.form_submit_button("Salvar no Catálogo"):
                if n_nome:
                    supabase.table("exercicios").insert({
                        "nome": n_nome,
                        "serie_tipo": n_serie,
                        "peso_kg": n_peso,
                        "series": 3,
                        "repeticoes": 12
                    }).execute()
                    st.success(f"✅ {n_nome} adicionado à Série {n_serie}!")
                    st.rerun()  # Atualiza a tela para mostrar a nova série

    # 2. Editar/Excluir Exercícios do Catálogo
    with st.expander("📝 Editar ou Remover Exercícios"):
        res_cat = supabase.table("exercicios").select("*").order("serie_tipo").execute()
        if res_cat.data:
            for ex_cat in res_cat.data:
                col_n, col_d = st.columns([3, 1])
                col_n.write(f"**{ex_cat['nome']}** (Série {ex_cat['serie_tipo']})")
                if col_d.button("🗑️", key=f"del_{ex_cat['id']}"):
                    supabase.table("exercicios").delete().eq("id", ex_cat['id']).execute()
                    st.error(f"Excluído: {ex_cat['nome']}")
                    st.rerun()

    st.divider()

    # 3. Zona de Perigo (Limpar Dados)
    st.subheader("🚨 Zona de Perigo")

    col_h, col_p = st.columns(2)

    if col_h.button("🗑️ Apagar Todo Histórico"):
        # Deleta tudo onde o ID não é zero (ou seja, tudo)
        supabase.table("historico_treinos").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        st.success("Histórico limpo com sucesso!")
        st.rerun()

    if col_p.button("🔄 Resetar Todos os Pesos"):
        supabase.table("exercicios").update({"peso_kg": 0}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
        st.success("Pesos resetados para 0kg!")
        st.rerun()