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
    st.header("🏃 Lógica de Esteira")

    col_t1, col_t2 = st.columns(2)
    # Forçamos o step=1 para aumentar/diminuir de 1 em 1 minuto
    t_base = col_t1.number_input("Tempo Principal (min)", value=20, step=1)
    t_extra = col_t2.number_input("Aquecimento/Desaceleração (min)", value=2, step=1)

    col_v1, col_v2 = st.columns(2)
    # Mantemos 0.5 de step para velocidade, fica mais prático que 0.1
    v_anda = col_v1.number_input("Velocidade Andando (km/h)", value=5.5, step=0.5)
    v_corre = col_v2.number_input("Velocidade Correndo (km/h)", value=9.0, step=0.5)

    t_total = t_base + (t_extra * 2)
    st.info(f"⏱️ Tempo Total do Treino: {t_total} minutos")

    if st.button("🚀 INICIAR CRONÔMETRO"):
        placeholder = st.empty()  # Espaço que será atualizado pelo cronômetro

        # Etapas do treino: (Nome, Tempo em segundos, Velocidade)
        etapas = [
            ("🔥 Aquecimento", t_extra * 60, v_anda),
            ("⚡ Corrida Principal", t_base * 60, v_corre),
            ("❄️ Desaceleração", t_extra * 60, v_anda)
        ]

        for nome_etapa, tempo_seg, vel in etapas:
            while tempo_seg > 0:
                mins, secs = divmod(tempo_seg, 60)
                # Atualiza a interface em tempo real
                placeholder.markdown(f"""
                    <div style="text-align: center; border: 2px solid #e066ff; padding: 20px; border-radius: 10px;">
                        <h2 style="color: #e066ff;">{nome_etapa}</h2>
                        <h1 style="font-size: 80px;">{mins:02d}:{secs:02d}</h1>
                        <h3>Velocidade: <span style="color: #66ffe0;">{vel} km/h</span></h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                tempo_seg -= 1

        placeholder.success("🎉 Treino de Cardio Concluído!")
        registrar_historico(None, f"Cardio: {t_total}min | Pico: {v_corre}km/h", tipo="cardio")

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