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

# Estética CSS para Mobile (Checklist Horizontal e Botões Grandes)
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

# --- ABA 1: TREINO (EXERCÍCIO POR EXERCÍCIO) ---
with aba1:
    st.subheader("🗓️ Checklist Semanal")
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    cols = st.columns(7)
    for i, dia in enumerate(dias):
        st.session_state[f"manual_{dia}"] = cols[i].checkbox(dia, key=f"c_{dia}")

    st.divider()
    serie = st.radio("Série de hoje:", ["A", "B", "C", "D"], horizontal=True)

    if st.button(f"🚀 INICIAR SÉRIE {serie}"):
        st.session_state.treino_ativo = True
        st.session_state.indice_ex = 0
        st.session_state.inicio_timer = time.time()

    if st.session_state.get("treino_ativo"):
        res = supabase.table("exercicios").select("*").eq("serie_tipo", serie).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]
            st.markdown(f"### Exercício {st.session_state.indice_ex + 1} de {len(res.data)}")
            st.info(f"🏋️ **{ex_atual['nome']}**")

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Carga (kg)", value=int(ex_atual['peso_kg']), step=1)
            s = c2.number_input("Séries", value=int(ex_atual['series']), step=1)
            r = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1)

            tempo_decorrido = int(time.time() - st.session_state.inicio_timer)
            st.write(f"⏱️ Tempo neste exercício: {tempo_decorrido // 60:02d}:{tempo_decorrido % 60:02d}")

            if st.button("PRÓXIMO EXERCÍCIO ➡️"):
                registrar_historico(ex_atual['id'], f"{p}kg | {s}x{r}")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual['id']).execute()
                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                    st.session_state.inicio_timer = time.time()
                    st.rerun()
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                    st.success("Série concluída!")

# --- ABA 2: CARDIO (SALVAMENTO NA INTERRUPÇÃO) ---
with aba2:
    st.header("🏃 Meta de Percurso")

    # Meta Principal
    distancia_alvo = st.number_input("Quanto você quer percorrer no total (km)?", value=5.0, step=0.5)

    st.divider()
    st.subheader("⚙️ Configuração do Ciclo")
    c1, c2 = st.columns(2)

    # Configurações de tempo e velocidade
    t_anda = c1.number_input("Minutos Andando", value=5.0, step=1.0)
    v_anda = c1.number_input("Velocidade Andando (km/h)", value=5.0, step=0.5)

    t_corre = c2.number_input("Minutos Correndo", value=2.0, step=1.0)
    v_corre = c2.number_input("Velocidade Correndo (km/h)", value=9.0, step=0.5)

    # --- LÓGICA DE DATA SCIENCE (Cálculo Automático) ---
    # 1. Calcular distância de UM ciclo: (V * T / 60)
    dist_ciclo = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60)))

    # 2. Calcular quantas repetições são necessárias para atingir a meta
    if dist_ciclo > 0:
        n_ciclos = int(distancia_alvo / dist_ciclo)
        sobra_km = distancia_alvo % dist_ciclo
        # Se sobrar uma distância considerável, arredondamos para cima ou avisamos
        if sobra_km > 0.1:
            n_ciclos += 1
    else:
        n_ciclos = 0

    tempo_total_estimado = (t_anda + t_corre) * n_ciclos

    # Exibição dos resultados calculados pelo App
    st.info(f"💡 Para percorrer **{distancia_alvo}km**, o app calculou que você fará **{n_ciclos} ciclos** completos.")

    m1, m2 = st.columns(2)
    m1.metric("⏱️ Tempo Total Estimado", f"{int(tempo_total_estimado)} min")
    m2.metric("📍 Distância Final", f"{distancia_alvo:.2f} km")

    # --- CONTROLE DE EXECUÇÃO ---
    if "cardio_ativo" not in st.session_state: st.session_state.cardio_ativo = False
    if "dist_real" not in st.session_state: st.session_state.dist_real = 0.0

    st.divider()
    btn_start, btn_stop = st.columns(2)

    if btn_start.button("🚀 INICIAR PERCURSO", use_container_width=True):
        st.session_state.cardio_ativo = True
        st.session_state.dist_real = 0.0

    if btn_stop.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
        if st.session_state.cardio_ativo:
            registrar_historico(None, f"Cardio (Meta {distancia_alvo}k): {st.session_state.dist_real:.2f}km",
                                tipo="cardio")
        st.session_state.cardio_ativo = False
        st.rerun()

    if st.session_state.cardio_ativo:
        ph = st.empty()
        etapas = []
        for i in range(n_ciclos):
            if t_anda > 0: etapas.append((f"🚶 Caminhada ({i + 1}/{n_ciclos})", t_anda * 60, v_anda))
            if t_corre > 0: etapas.append((f"⚡ Corrida ({i + 1}/{n_ciclos})", t_corre * 60, v_corre))

        for nome, segs, vel in etapas:
            if not st.session_state.cardio_ativo: break
            while segs > 0 and st.session_state.cardio_ativo:
                st.session_state.dist_real += vel / 3600
                m, s = divmod(int(segs), 60)
                ph.markdown(f"""
                    <div style="text-align:center;border:3px solid #e066ff;padding:20px;border-radius:15px;background:#1e1e1e;">
                        <h2 style="color:#e066ff">{nome}</h2>
                        <h1 style="font-size:80px;color:white;">{m:02d}:{s:02d}</h1>
                        <h3 style="color:#66ffe0;">Progresso: {st.session_state.dist_real:.2f} / {distancia_alvo} km</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                segs -= 1

        if st.session_state.cardio_ativo:
            registrar_historico(None, f"Meta {distancia_alvo}k Concluída: {st.session_state.dist_real:.2f}km",
                                tipo="cardio")
            st.success("🎉 Percurso concluído com sucesso!")
            st.session_state.cardio_ativo = False

# --- ABA 3: HISTÓRICO CORRIGIDO ---
with aba3:
    st.header("📊 Desempenho Mensal")
    try:
        res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                        desc=True).execute()
        if res_h.data:
            df = pd.json_normalize(res_h.data)
            df['data_execucao'] = pd.to_datetime(df['data_execucao'])
            df_mes = df[df['data_execucao'].dt.month == hoje.month]

            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Frequência", f"{len(df_mes)}x")

            # Cálculo de KM com verificação de coluna
            km_sum = 0.0
            if 'detalhes' in df_mes.columns:
                km_sum = \
                df_mes[df_mes['tipo'] == 'cardio']['detalhes'].str.extract(r'(\d+\.\d+)km').astype(float).sum()[0]
            c2.metric("Distância", f"{km_sum:.1f} km" if not pd.isna(km_sum) else "0.0 km")
            c3.metric("Mês", hoje.strftime("%B"))

            # Exibição da Tabela com verificação de colunas (Evita o KeyError)
            st.subheader("📜 Registros Recentes")
            # Garantir que a coluna de nome exista mesmo que venha vazia
            if 'exercicios.nome' not in df.columns:
                df['exercicios.nome'] = "🏃 Cardio"
            else:
                df['exercicios.nome'] = df['exercicios.nome'].fillna("🏃 Cardio")

            colunas_visiveis = ['data_execucao', 'exercicios.nome', 'detalhes']
            # Filtra apenas as colunas que realmente existem no DF
            existentes = [c for c in colunas_visiveis if c in df.columns]

            st.dataframe(
                df[existentes].head(15),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Ainda não há treinos registrados neste mês! Bora começar?")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

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