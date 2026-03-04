import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PyTrain PRO", page_icon="🏋️", layout="wide")

# Estética CSS
st.markdown("""
    <style>
    div.stButton > button:first-child { height: 3em; width: 100%; font-size: 18px; font-weight: bold; }
    .stNumberInput div div input { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# --- FUNÇÕES DE APOIO ---
def registrar_historico(ex_id, detalhes, tipo="musculacao"):
    dados = {
        "exercicio_id": ex_id,
        "data_execucao": datetime.now().isoformat(),
        "detalhes": detalhes,
        "tipo": tipo
    }
    supabase.table("historico_treinos").insert(dados).execute()


# --- INTERFACE ---
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📜 Histórico", "⚙️ Menu"])

# --- ABA 1: TREINO (COM CHECKLIST SEMANAL REAL) ---
with aba1:
    st.subheader("🗓️ Checklist Semanal")

    # Lógica de Data Science: Buscar treinos da semana atual
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    res_semana = supabase.table("historico_treinos").select("data_execucao").filter("data_execucao", "gte",
                                                                                    inicio_semana.isoformat()).execute()

    dias_treinados = [datetime.fromisoformat(r['data_execucao']).weekday() for r in res_semana.data]
    dias_nome = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    cols = st.columns(7)
    for i, dia in enumerate(dias_nome):
        # Checkbox marcado automaticamente se houver registro no banco para aquele dia
        cols[i].checkbox(dia, value=(i in dias_treinados), key=f"check_{dia}", disabled=True)

    st.divider()

    serie = st.radio("Qual série hoje?", ["A", "B", "C", "D"], horizontal=True)
    res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()

    if not res.data:
        st.warning(f"Nenhum exercício na Série {serie}")
    else:
        with st.form(f"form_treino_{serie}"):
            for ex in res.data:
                st.subheader(f"▶ {ex['nome']}")
                c1, c2, c3 = st.columns(3)
                p = c1.number_input("Kg", value=int(ex['peso_kg']), key=f"p_{ex['id']}", step=1)
                s = c2.number_input("Séries", value=int(ex['series']), key=f"s_{ex['id']}", step=1)
                r = c3.number_input("Reps", value=int(ex['repeticoes']), key=f"r_{ex['id']}", step=1)

            if st.form_submit_button("🏆 CONCLUIR TREINO"):
                for ex in res.data:
                    p_val, s_val, r_val = st.session_state[f"p_{ex['id']}"], st.session_state[f"s_{ex['id']}"], \
                    st.session_state[f"r_{ex['id']}"]
                    supabase.table("exercicios").update({"peso_kg": p_val}).eq("id", ex['id']).execute()
                    registrar_historico(ex['id'], f"{p_val}kg | {s_val}x{r_val}")
                st.balloons()
                st.success("✅ Treino salvo!")
                st.rerun()

# --- ABA 2: CARDIO (COM CÁLCULO DE KM) ---
with aba2:
    st.header("🏃 HIIT Intervalado")
    c1, c2 = st.columns(2)
    t_anda = c1.number_input("Minutos Andando", 2, step=1)
    v_anda = c1.number_input("Vel. Andando", 5.5, step=0.5)
    t_corre = c2.number_input("Minutos Correndo", 1, step=1)
    v_corre = c2.number_input("Vel. Correndo", 9.0, step=0.5)
    n_ciclos = st.number_input("Repetições do Ciclo", 5, step=1)

    tempo_total = (t_anda + t_corre) * n_ciclos
    distancia = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60))) * n_ciclos

    st.info(f"⏱️ {tempo_total} min | 📍 {distancia:.2f} km")

    if st.button("🚀 INICIAR"):
        ph = st.empty()
        bar = st.progress(0)
        for c in range(n_ciclos):
            for fase, t, v, cor in [("🚶 ANDANDO", t_anda, v_anda, "#66ffe0"),
                                    ("⚡ CORRENDO", t_corre, v_corre, "#e066ff")]:
                segundos = t * 60
                while segundos > 0:
                    m, s = divmod(segundos, 60)
                    ph.markdown(
                        f'<div style="text-align:center;border:3px solid {cor};padding:20px;border-radius:15px;background:#1e1e1e;"><h2 style="color:{cor}">{fase}</h2><h1 style="font-size:80px;color:white;">{m:02d}:{s:02d}</h1><h3>{v} km/h</h3></div>',
                        unsafe_allow_html=True)
                    time.sleep(1)
                    segundos -= 1
            bar.progress((c + 1) / n_ciclos)
        registrar_historico(None, f"Cardio: {distancia:.2f}km | {tempo_total}min", tipo="cardio")
        st.success("HIIT Concluído!")

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