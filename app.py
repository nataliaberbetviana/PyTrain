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

# Fuso horário e Data (Brasília)
fuso = pytz.timezone('America/Sao_Paulo')
hoje_agora = datetime.now(fuso)

# Estética CSS: Tema Roxo e Preto Total
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #1e1e2e; border-radius: 8px 8px 0 0; color: white; border: none;
    }
    .stTabs [aria-selected="true"] { background-color: #7d33ff !important; }
    div.stButton > button {
        background-color: #7d33ff; color: white; border-radius: 12px; height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    /* Inputs Roxo Neon */
    .stNumberInput div div input { background-color: #1e1e2e !important; color: #e066ff !important; font-size: 20px !important; }
    /* Checklist Horizontal Mobile */
    [data-testid="column"] { min-width: 14% !important; }
    .stCheckbox { display: flex; justify-content: center; background-color: #1e1e2e; padding: 5px; border-radius: 5px; }
    /* Estilo para Radio Buttons */
    div[data-testid="stWidgetLabel"] p { color: #a366ff !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    agora = datetime.now(fuso).isoformat()
    supabase.table("historico_treinos").insert({
        "exercicio_id": ex_id, "data_execucao": agora,
        "detalhes": detalhes, "tipo": tipo
    }).execute()


# --- INTERFACE ---
st.title("💜 PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])

# --- ABA 1: TREINO DINÂMICO ---
with aba1:
    st.subheader("🗓️ Checklist Semanal")
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    cols = st.columns(7)
    for i, dia in enumerate(dias):
        # Aqui você marca manualmente conforme pediu
        st.session_state[f"manual_{dia}"] = cols[i].checkbox(dia, key=f"c_{dia}")

    st.divider()
    serie = st.radio("Série de hoje:", ["A", "B", "C", "D"], horizontal=True)

    if st.button(f"🚀 INICIAR SÉRIE {serie}"):
        st.session_state.treino_ativo = True
        st.session_state.indice_ex = 0
        st.session_state.inicio_timer = time.time()
        st.rerun()

    if st.session_state.get("treino_ativo"):
        res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]

            st.markdown(f"""
                <div style="background:#1e1e2e; padding:15px; border-radius:10px; border-left: 5px solid #7d33ff; margin-bottom:15px;">
                    <h4 style="color:gray; margin:0;">Exercício {st.session_state.indice_ex + 1} de {len(res.data)}</h4>
                    <h2 style="color:white; margin:0;">{ex_atual['nome']}</h2>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg", value=int(ex_atual['peso_kg']), step=1, key=f"p_{st.session_state.indice_ex}")
            s = c2.number_input("Séries", value=int(ex_atual['series']), step=1, key=f"s_{st.session_state.indice_ex}")
            r = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1,
                                key=f"r_{st.session_state.indice_ex}")

            # Cronômetro Contínuo
            tempo_total_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_total_seg, 60)
            st.markdown(f"""
                <div style="text-align:center; padding:10px; border:1px solid #7d33ff; border-radius:10px; margin-bottom:15px;">
                    <span style="color:#a366ff;">⏱️ Tempo de Sessão:</span><br>
                    <span style="font-size:30px; font-weight:bold;">{m:02d}:{seg:02d}</span>
                </div>
            """, unsafe_allow_html=True)

            if st.button("PRÓXIMO ➡️"):
                tempo_min = max(1, tempo_total_seg // 60)
                registrar_historico(ex_atual['id'], f"{p}kg | {s}x{r} | {tempo_min}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual['id']).execute()

                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                    st.rerun()
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.rerun()

            # Autoupdate do timer
            time.sleep(1)
            st.rerun()

# --- ABA 2: CARDIO (CORREÇÃO DO TYPEERROR) ---
with aba2:
    st.header("🏃 Cardio")
    modo = st.radio("Configurar por:", ["KM Total", "Número de Ciclos"], horizontal=True)

    col1, col2 = st.columns(2)
    t_anda = col1.number_input("Minutos Andando", 5.0, step=1.0)
    v_anda = col1.number_input("Vel. Andando", 5.0, step=0.5)
    t_corre = col2.number_input("Minutos Correndo", 2.0, step=1.0)
    v_corre = col2.number_input("Vel. Correndo", 9.0, step=0.5)

    dist_ciclo = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60)))

    if modo == "KM Total":
        dist_alvo = st.number_input("Meta de Percurso (km)", 5.0, step=0.5)
        # CORREÇÃO: int() garante que n_ciclos não seja float
        n_ciclos = int(dist_alvo / dist_ciclo) + (1 if dist_alvo % dist_ciclo > 0.05 else 0)
    else:
        n_ciclos = st.number_input("Quantos Ciclos?", value=1, min_value=1, step=1)
        dist_alvo = dist_ciclo * n_ciclos

    st.info(f"📋 {n_ciclos} ciclos planejados | Total: {dist_alvo:.2f} km")

    if "cardio_ativo" not in st.session_state: st.session_state.cardio_ativo = False
    if "dist_real" not in st.session_state: st.session_state.dist_real = 0.0

    c_start, c_stop = st.columns(2)
    if c_start.button("🚀 INICIAR"):
        st.session_state.cardio_ativo = True
        st.session_state.dist_real = 0.0
        st.session_state.t_cardio_start = time.time()

    if c_stop.button("🛑 ENCERRAR"):
        if st.session_state.cardio_ativo:
            t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Cardio: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
        st.session_state.cardio_ativo = False
        st.rerun()

    if st.session_state.cardio_ativo:
        ph = st.empty()
        etapas = []
        for i in range(n_ciclos):
            etapas.append((f"🚶 Caminhada ({i + 1})", t_anda * 60, v_anda))
            etapas.append((f"⚡ Corrida ({i + 1})", t_corre * 60, v_corre))

        for nome, segs, vel in etapas:
            while segs > 0 and st.session_state.cardio_ativo:
                st.session_state.dist_real += vel / 3600
                m, s = divmod(int(segs), 60)
                ph.markdown(f"""
                    <div style='text-align:center; border:2px solid #7d33ff; padding:20px; border-radius:15px; background:black;'>
                        <h2 style='color:#a366ff'>{nome}</h2>
                        <h1 style='font-size:70px;'>{m:02d}:{s:02d}</h1>
                        <h3 style='color:#e066ff'>{st.session_state.dist_real:.2f} / {dist_alvo:.2f} km</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                segs -= 1

        if st.session_state.cardio_ativo:
            t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Cardio: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
            st.session_state.cardio_ativo = False
            st.success("Objetivo concluído!")

# --- ABA 3: RENDIMENTO DETALHADO (DIÁRIO/SEMANAL/MENSAL) ---
with aba3:
    st.header("📊 Performance Detalhada")
    try:
        res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                        desc=True).execute()
        if res_h.data:
            df = pd.json_normalize(res_h.data)
            df['data_execucao'] = pd.to_datetime(df['data_execucao']).dt.tz_convert('America/Sao_Paulo')

            # Filtros
            inicio_semana = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0, minute=0)
            df_hoje = df[df['data_execucao'].dt.date == hoje_agora.date()]
            df_semana = df[df['data_execucao'] >= inicio_semana]
            df_mes = df[df['data_execucao'].dt.month == hoje_agora.month]


            def extrair_stats(dataframe):
                if 'detalhes' not in dataframe.columns: return 0.0, 0
                kms = dataframe['detalhes'].str.extract(r'(\d+\.\d+)km').astype(float).sum()[0]
                mins = dataframe['detalhes'].str.extract(r'(\d+)min').astype(float).sum()[0]
                return (kms if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)


            # Exibição
            for titulo, dff in [("Hoje", df_hoje), ("Na Semana", df_semana), ("No Mês", df_mes)]:
                km, tempo = extrair_stats(dff)
                st.markdown(f"#### 📅 {titulo}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Registros", len(dff))
                c2.metric("Distância", f"{km:.2f} km")
                c3.metric("Tempo", f"{tempo} min")
                st.divider()
    except:
        st.error("Erro ao carregar dados do Supabase.")

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