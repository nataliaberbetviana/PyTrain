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
    st.header("🏃 Controle de Esteira")

    # Seletor de Modo de Planejamento
    modo_planejamento = st.radio(
        "Como deseja planejar seu treino?",
        ["Por Distância Alvo (km)", "Por Número de Ciclos"],
        horizontal=True
    )

    st.divider()

    # Configurações do Ciclo Base
    c1, c2 = st.columns(2)
    t_anda = c1.number_input("Minutos Andando", value=5.0, step=1.0, key="t_anda_base")
    v_anda = c1.number_input("Vel. Andando (km/h)", value=5.0, step=0.5, key="v_anda_base")

    t_corre = c2.number_input("Minutos Correndo", value=2.0, step=1.0, key="t_corre_base")
    v_corre = c2.number_input("Vel. Correndo (km/h)", value=9.0, step=0.5, key="v_corre_base")

    # Distância de um único ciclo (Data Science mode)
    dist_por_ciclo = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60)))

    # Lógica Condicional de Entrada
    if modo_planejamento == "Por Distância Alvo (km)":
        distancia_alvo = st.number_input("Qual a distância total desejada (km)?", value=5.0, step=0.5)
        if dist_por_ciclo > 0:
            n_ciclos = int(distancia_alvo / dist_por_ciclo)
            if (distancia_alvo % dist_por_ciclo) > 0.05:  # Pequena margem para arredondar
                n_ciclos += 1
        else:
            n_ciclos = 0
    else:
        n_ciclos = st.number_input("Quantas repetições do ciclo?", value=1, min_value=1, step=1)
        distancia_alvo = dist_por_ciclo * n_ciclos

    # Métricas calculadas para visualização antes do Play
    tempo_total_estimado = (t_anda + t_corre) * n_ciclos

    st.info(f"📋 Resumo: **{n_ciclos} ciclos** de treino.")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("⏱️ Tempo Total", f"{int(tempo_total_estimado)} min")
    col_m2.metric("📍 Distância Final", f"{distancia_alvo:.2f} km")

    # --- LÓGICA DE EXECUÇÃO ---
    if "cardio_ativo" not in st.session_state: st.session_state.cardio_ativo = False
    if "dist_real" not in st.session_state: st.session_state.dist_real = 0.0

    st.divider()
    btn_start, btn_stop = st.columns(2)

    if btn_start.button("🚀 INICIAR CARDIO", use_container_width=True):
        st.session_state.cardio_ativo = True
        st.session_state.dist_real = 0.0

    if btn_stop.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
        if st.session_state.cardio_ativo:
            registrar_historico(None, f"Cardio Interrompido: {st.session_state.dist_real:.2f}km", tipo="cardio")
        st.session_state.cardio_ativo = False
        st.rerun()

    if st.session_state.cardio_ativo:
        ph = st.empty()
        etapas = []
        # Montagem da lista de tarefas do treino
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
                        <h3 style="color:#66ffe0;">Progresso: {st.session_state.dist_real:.2f} / {distancia_alvo:.2f} km</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                segs -= 1

        if st.session_state.cardio_ativo:
            registrar_historico(None, f"Cardio Finalizado: {st.session_state.dist_real:.2f}km", tipo="cardio")
            st.success("🎉 Treino concluído!")
            st.session_state.cardio_ativo = False

# --- ABA 3: HISTÓRICO CORRIGIDO ---
with aba3:
    st.header("📊 Painel de Rendimento")

    try:
        # Busca os dados no Supabase
        res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                        desc=True).execute()

        if res_h.data:
            df = pd.json_normalize(res_h.data)
            df['data_execucao'] = pd.to_datetime(df['data_execucao']).dt.tz_convert('America/Sao_Paulo')

            # --- CÁLCULOS DE PERÍODO ---
            hoje_dt = datetime.now(fuso)
            inicio_semana = (hoje_dt - timedelta(days=hoje_dt.weekday())).replace(hour=0, minute=0, second=0)

            # Filtros
            df_hoje = df[df['data_execucao'].dt.date == hoje_dt.date()]
            df_semana = df[df['data_execucao'] >= inicio_semana]
            df_mes = df[df['data_execucao'].dt.month == hoje_dt.month]


            # Função para extrair KM dos detalhes
            def extrair_km(dataframe):
                if 'detalhes' in dataframe.columns:
                    kms = dataframe[dataframe['tipo'] == 'cardio']['detalhes'].str.extract(r'(\d+\.\d+)km').astype(
                        float)
                    return kms.sum()[0] if not kms.empty else 0.0
                return 0.0


            # --- MÉTRICAS EM DESTAQUE ---
            m1, m2, m3 = st.columns(3)

            # Treinos (Musculação + Cardio)
            m1.metric("Hoje", f"{len(df_hoje)} registros", help="Total de ações registradas hoje")
            m2.metric("Na Semana", f"{len(df_semana)}x", help="Sessões iniciadas desde segunda-feira")
            m3.metric("No Mês", f"{len(df_mes)}x")

            # --- PERFORMANCE DE CARDIO (DISTÂNCIA) ---
            st.divider()
            st.subheader("🏃 Evolução de Distância (km)")
            k1, k2, k3 = st.columns(3)
            k1.metric("Hoje", f"{extrair_km(df_hoje):.2f} km")
            k2.metric("Semana", f"{extrair_km(df_semana):.2f} km")
            k3.metric("Total Mês", f"{extrair_km(df_mes):.2f} km")

            # --- LISTAGEM DETALHADA ---
            st.divider()
            st.subheader("📜 O que você fez hoje")
            if not df_hoje.empty:
                # Tratamento de nomes para exibição
                if 'exercicios.nome' not in df_hoje.columns:
                    df_hoje['exercicios.nome'] = "🏃 Cardio"
                df_hoje['exercicios.nome'] = df_hoje['exercicios.nome'].fillna("🏃 Cardio")

                st.dataframe(
                    df_hoje[['data_execucao', 'exercicios.nome', 'detalhes']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum exercício registrado hoje ainda. Que tal começar agora?")

            if st.checkbox("Ver histórico completo"):
                st.dataframe(df.head(50), use_container_width=True)

        else:
            st.warning("Nenhum dado encontrado no seu histórico.")

    except Exception as e:
        st.error(f"Erro ao processar indicadores: {e}")

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