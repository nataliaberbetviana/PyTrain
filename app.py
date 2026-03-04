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
# --- ABA 2: CARDIO (CORREÇÃO DE TEMPO TOTAL E CICLOS) ---
with aba2:
    st.header("🏃 Controle de Esteira")
    modo = st.radio("Configurar por:", ["KM Total", "Número de Ciclos"], horizontal=True)

    col1, col2 = st.columns(2)
    t_anda = col1.number_input("Minutos Andando", value=5.0, step=1.0, key="t_anda_cardio")
    v_anda = col1.number_input("Vel. Andando (km/h)", value=5.0, step=0.5, key="v_anda_cardio")
    t_corre = col2.number_input("Minutos Correndo", value=2.0, step=1.0, key="t_corre_cardio")
    v_corre = col2.number_input("Vel. Correndo (km/h)", value=9.0, step=0.5, key="v_corre_cardio")

    # Distância de um ciclo base: (Velocidade * Tempo / 60)
    dist_ciclo = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60)))

    if modo == "KM Total":
        dist_alvo = st.number_input("Meta de Percurso (km)", value=5.0, step=0.5)
        # Cálculo de ciclos necessários para atingir os KM desejados
        if dist_ciclo > 0:
            n_ciclos = int(dist_alvo / dist_ciclo) + (1 if dist_alvo % dist_ciclo > 0.05 else 0)
        else:
            n_ciclos = 0
    else:
        # Se você escolher por ciclos, definimos o N e calculamos a distância
        n_ciclos = st.number_input("Quantos Ciclos?", value=1, min_value=1, step=1)
        dist_alvo = dist_ciclo * n_ciclos

    # CÁLCULO DO TEMPO TOTAL REAL (Minutos de um ciclo * quantidade de ciclos)
    tempo_total_real = (t_anda + t_corre) * n_ciclos

    # Exibição em destaque das métricas combinadas
    st.markdown(f"""
        <div style="background:#1e1e2e; padding:20px; border-radius:15px; border-left: 5px solid #7d33ff; margin-bottom:20px;">
            <h3 style="margin:0; color:#a366ff;">📊 Planejamento do Treino</h3>
            <p style="margin:5px 0; font-size:18px;">🔄 <b>{n_ciclos} Ciclos</b> planejados</p>
            <p style="margin:5px 0; font-size:22px; color:#e066ff;">⏱️ Tempo Total: <b>{int(tempo_total_real)} minutos</b></p>
            <p style="margin:5px 0; font-size:18px;">📍 Distância Estimada: <b>{dist_alvo:.2f} km</b></p>
        </div>
    """, unsafe_allow_html=True)

    if "cardio_ativo" not in st.session_state: st.session_state.cardio_ativo = False
    if "dist_real" not in st.session_state: st.session_state.dist_real = 0.0

    c_start, c_stop = st.columns(2)
    if c_start.button("🚀 INICIAR TREINO", use_container_width=True):
        st.session_state.cardio_ativo = True
        st.session_state.dist_real = 0.0
        st.session_state.t_cardio_start = time.time()

    if c_stop.button("🛑 ENCERRAR E SALVAR", use_container_width=True):
        if st.session_state.cardio_ativo:
            t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Cardio Interrompido: {st.session_state.dist_real:.2f}km | {t_final}min",
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
            while segs > 0 and st.session_state.cardio_ativo:
                st.session_state.dist_real += vel / 3600
                m, s = divmod(int(segs), 60)
                ph.markdown(f"""
                    <div style="text-align:center; border:2px solid #7d33ff; padding:20px; border-radius:15px; background:black;">
                        <h2 style="color:#a366ff">{nome}</h2>
                        <h1 style="font-size:70px; color:white;">{m:02d}:{segs % 60:02.0f}</h1>
                        <h3 style="color:#e066ff">Progresso: {st.session_state.dist_real:.2f} / {dist_alvo:.2f} km</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                segs -= 1

        if st.session_state.cardio_ativo:
            t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Cardio Concluído: {st.session_state.dist_real:.2f}km | {t_final}min",
                                tipo="cardio")
            st.session_state.cardio_ativo = False
            st.success("Objetivo de cardio alcançado!")

# --- ABA 3: RENDIMENTO DETALHADO (DIÁRIO/SEMANAL/MENSAL) ---
# --- ABA 3: PAINEL DE RENDIMENTO COM FILTRO ---
with aba3:
    st.header("📊 Performance & Histórico")

    try:
        # Busca TODOS os dados para permitir o filtro por mês
        res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                        desc=True).execute()

        if res_h.data:
            df = pd.json_normalize(res_h.data)
            df['data_execucao'] = pd.to_datetime(df['data_execucao']).dt.tz_convert('America/Sao_Paulo')

            # --- SELETOR DE MÊS/ANO ---
            st.subheader("📅 Filtrar Período")
            col_f1, col_f2 = st.columns(2)

            anos_disponiveis = sorted(df['data_execucao'].dt.year.unique(), reverse=True)
            ano_sel = col_f1.selectbox("Ano", anos_disponiveis, index=0)

            meses_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                           7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            meses_disponiveis = sorted(df[df['data_execucao'].dt.year == ano_sel]['data_execucao'].dt.month.unique(),
                                       reverse=True)
            mes_sel = col_f2.selectbox("Mês", meses_disponiveis, format_func=lambda x: meses_nomes[x])

            # --- FILTRAGEM DOS DADOS ---
            df_filtrado = df[(df['data_execucao'].dt.month == mes_sel) & (df['data_execucao'].dt.year == ano_sel)]

            # Hoje e Semana (fixos para referência rápida)
            df_hoje = df[df['data_execucao'].dt.date == hoje_agora.date()]
            inicio_semana = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0, minute=0)
            df_semana = df[df['data_execucao'] >= inicio_semana]


            def extrair_stats(dataframe):
                if dataframe.empty or 'detalhes' not in dataframe.columns: return 0.0, 0
                kms = dataframe['detalhes'].str.extract(r'(\d+\.\d+)km').astype(float).sum()[0]
                mins = dataframe['detalhes'].str.extract(r'(\d+)min').astype(float).sum()[0]
                return (kms if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)


            # --- EXIBIÇÃO DE MÉTRICAS ---
            st.markdown(f"#### 📈 Resumo de {meses_nomes[mes_sel]}/{ano_sel}")
            c1, c2, c3 = st.columns(3)
            km_f, min_f = extrair_stats(df_filtrado)

            c1.metric("Treinos", len(df_filtrado))
            c2.metric("Distância", f"{km_f:.2f} km")
            c3.metric("Tempo", f"{min_f} min")

            # --- LISTA COMPLETA DO MÊS SELECIONADO ---
            st.divider()
            st.subheader(f"📜 Atividades em {meses_nomes[mes_sel]}")

            if not df_filtrado.empty:
                # Tratamento de nomes para a tabela
                if 'exercicios.nome' not in df_filtrado.columns:
                    df_filtrado['exercicios.nome'] = "🏃 Cardio"
                df_filtrado['exercicios.nome'] = df_filtrado['exercicios.nome'].fillna("🏃 Cardio")

                # Formata a data para leitura humana
                df_filtrado['Data'] = df_filtrado['data_execucao'].dt.strftime('%d/%m/%Y %H:%M')

                st.dataframe(
                    df_filtrado[['Data', 'exercicios.nome', 'detalhes']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum registro para este período.")

            # Referência rápida de hoje/semana no final
            with st.expander("📌 Ver Hoje e Esta Semana"):
                km_h, min_h = extrair_stats(df_hoje)
                km_s, min_s = extrair_stats(df_semana)
                st.write(f"**Hoje:** {len(df_hoje)} atividades | {km_h:.2f}km | {min_h}min")
                st.write(f"**Semana:** {len(df_semana)} atividades | {km_s:.2f}km | {min_s}min")

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

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