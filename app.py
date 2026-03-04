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
    v_anda = col1.number_input("Velocidade Andando", value=5.0, step=0.5)

    t_corre = col2.number_input("Minutos Correndo", value=0, step=1)
    v_corre = col2.number_input("Velocidade Correndo", value=9.0, step=0.5)

    # Botão de início e interrupção usando Session State
    if "cardio_ativo" not in st.session_state:
        st.session_state.cardio_ativo = False

    c_start, c_stop = st.columns(2)
    if c_start.button("🚀 INICIAR", use_container_width=True):
        st.session_state.cardio_ativo = True

    if c_stop.button("🛑 ENCERRAR", use_container_width=True):
        st.session_state.cardio_ativo = False
        st.rerun()

    if st.session_state.cardio_ativo:
        ph = st.empty()
        # Etapas baseadas no que você configurou
        etapas = []
        if t_anda > 0: etapas.append(("🚶 Caminhada", t_anda * 60, v_anda))
        if t_corre > 0: etapas.append(("⚡ Corrida", t_corre * 60, v_corre))
        if t_anda > 0: etapas.append(("❄️ Desaceleração", t_anda * 60, v_anda))

        for nome, tempo_seg, vel in etapas:
            if not st.session_state.cardio_ativo: break

            while tempo_seg > 0 and st.session_state.cardio_ativo:
                m, s = divmod(tempo_seg, 60)
                ph.markdown(f"""
                    <div style="text-align: center; border: 3px solid #e066ff; padding: 20px; border-radius: 15px;">
                        <h2 style="color: #e066ff;">{nome}</h2>
                        <h1 style="font-size: 80px;">{m:02d}:{s:02d}</h1>
                        <h3>Velocidade: {vel} km/h</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                tempo_seg -= 1

        if st.session_state.cardio_ativo:
            st.success("Treino Finalizado!")
            st.session_state.cardio_ativo = False

# --- ABA 3: DASHBOARD DE PERFORMANCE ---
with aba3:
    st.header("📊 Desempenho Mensal")
    res_m = supabase.table("historico_treinos").select("*").execute()
    if res_m.data:
        df = pd.DataFrame(res_m.data)
        df['data_execucao'] = pd.to_datetime(df['data_execucao'])
        df_mes = df[df['data_execucao'].dt.month == hoje.month]

        # Cálculos
        freq = len(df_mes['data_execucao'].dt.date.unique())
        # Extração de KM usando Regex
        df_cardio = df_mes[df_mes['tipo'] == 'cardio']
        km_total = df_cardio['detalhes'].str.extract(r'(\d+\.\d+)km').astype(float).sum()[
            0] if not df_cardio.empty else 0.0
        tempo_total = len(df_mes) * 45  # Estimativa de 45min por sessão

        c1, c2, c3 = st.columns(3)
        c1.metric("Frequência", f"{freq} dias")
        c2.metric("Distância Total", f"{km_total:.1f} km")
        c3.metric("Tempo Est.", f"{tempo_total // 60}h {tempo_total % 60}m")

        st.divider()
        st.subheader("📜 Histórico Recente")
        st.dataframe(df.sort_values('data_execucao', ascending=False).head(15), use_container_width=True)

# --- ABA 4: MENU --- (Manteve igual à sua versão anterior)

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