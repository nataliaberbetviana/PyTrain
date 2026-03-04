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

# Fuso horário Brasília
fuso = pytz.timezone('America/Sao_Paulo')
hoje_agora = datetime.now(fuso)

# --- CSS AVANÇADO PARA MOBILE (TEMA ROXO/PRETO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }

    /* Remove espaços inúteis no topo */
    .block-container { padding-top: 1rem !important; }

    /* Botões Grandes e Roxos */
    div.stButton > button {
        background-color: #7d33ff;
        color: white;
        border-radius: 12px;
        height: 3.5em;
        width: 100%;
        font-weight: bold;
        border: none;
    }

    /* Container de Exercício no Topo */
    .foco-container {
        background-color: #1e1e2e;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #7d33ff;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Inputs Estilizados */
    .stNumberInput div div input {
        background-color: #1e1e2e !important;
        color: #e066ff !important;
        font-size: 22px !important;
    }

    /* Estilização das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e2e;
        border-radius: 8px 8px 0 0;
        color: white;
    }
    .stTabs [aria-selected="true"] { background-color: #7d33ff !important; }
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
st.title("🏋️ PyTrain PRO")
aba1, aba2, aba3, aba4 = st.tabs(["🚀 Treino", "🏃 Cardio", "📊 Painel", "⚙️ Menu"])

# --- ABA 1: TREINO (MODO FOCO TOTAL) ---
with aba1:
    if not st.session_state.get("treino_ativo"):
        st.subheader("Escolha sua Série")
        serie = st.radio("Selecione:", ["A", "B", "C", "D"], horizontal=True)

        if st.button(f"🚀 INICIAR TREINO - SÉRIE {serie}", use_container_width=True):
            st.session_state.treino_ativo = True
            st.session_state.serie_atual = serie
            st.session_state.indice_ex = 0
            st.session_state.inicio_timer = time.time()
            st.rerun()

    else:
        # TUDO O QUE ESTÁ AQUI APARECE NO TOPO QUANDO O TREINO INICIA
        res = supabase.table("exercicios").select("*").eq("serie_tipo", st.session_state.serie_atual).execute()
        if res.data:
            ex_atual = res.data[st.session_state.indice_ex]

            # Cabeçalho de Progresso
            st.markdown(f"""
                <div class="foco-container">
                    <h4 style="color:gray; margin:0;">Série {st.session_state.serie_atual} | {st.session_state.indice_ex + 1} de {len(res.data)}</h4>
                    <h1 style="color:#e066ff; margin:10px 0; font-size: 28px;">{ex_atual['nome']}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Kg", value=int(ex_atual['peso_kg']), step=1, key=f"p_{st.session_state.indice_ex}")
            s = c2.number_input("Sets", value=int(ex_atual['series']), step=1, key=f"s_{st.session_state.indice_ex}")
            r = c3.number_input("Reps", value=int(ex_atual['repeticoes']), step=1,
                                key=f"r_{st.session_state.indice_ex}")

            # Cronômetro da Sessão (Contínuo)
            tempo_total_seg = int(time.time() - st.session_state.inicio_timer)
            m, seg = divmod(tempo_total_seg, 60)
            st.markdown(f"""
                <div style='text-align:center; padding:15px; border:1px solid #7d33ff; border-radius:12px; margin: 15px 0;'>
                    <small style='color:gray;'>TEMPO TOTAL</small><br>
                    <span style='font-size:35px; font-weight:bold; color:white;'>{m:02d}:{seg:02d}</span>
                </div>
            """, unsafe_allow_html=True)

            if st.button("PRÓXIMO EXERCÍCIO ➡️", use_container_width=True):
                registrar_historico(ex_atual['id'], f"{p}kg | {s}x{r} | {tempo_total_seg // 60}min")
                supabase.table("exercicios").update({"peso_kg": p}).eq("id", ex_atual['id']).execute()

                if st.session_state.indice_ex + 1 < len(res.data):
                    st.session_state.indice_ex += 1
                else:
                    st.session_state.treino_ativo = False
                    st.balloons()
                st.rerun()

            if st.button("🛑 CANCELAR TREINO", type="secondary"):
                st.session_state.treino_ativo = False
                st.rerun()

            time.sleep(1)
            st.rerun()

# --- ABA 2: CARDIO (MODO FOCO TOTAL) ---
with aba2:
    if not st.session_state.get("cardio_ativo"):
        st.subheader("Configurar Esteira")
        modo = st.radio("Objetivo:", ["Distância Alvo (km)", "Número de Ciclos"], horizontal=True)

        c1, c2 = st.columns(2)
        t_anda = c1.number_input("Minutos Andando", 5.0, step=1.0)
        v_anda = c1.number_input("Vel. Andando", 5.0, step=0.5)
        t_corre = c2.number_input("Minutos Correndo", 2.0, step=1.0)
        v_corre = c2.number_input("Vel. Correndo", 9.0, step=0.5)

        dist_ciclo = ((v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60)))

        if modo == "Distância Alvo (km)":
            dist_alvo = st.number_input("Meta (km)", 5.0, step=0.5)
            n_ciclos = int(dist_alvo / dist_ciclo) + (1 if dist_alvo % dist_ciclo > 0.05 else 0)
        else:
            n_ciclos = st.number_input("Ciclos", 1, min_value=1, step=1)
            dist_alvo = dist_ciclo * n_ciclos

        if st.button("🚀 INICIAR CARDIO", use_container_width=True):
            st.session_state.cardio_ativo = True
            st.session_state.params_cardio = (n_ciclos, t_anda, v_anda, t_corre, v_corre, dist_alvo)
            st.session_state.dist_real = 0.0
            st.session_state.t_cardio_start = time.time()
            st.rerun()

    else:
        # TUDO O QUE ESTÁ AQUI APARECE NO TOPO QUANDO O CARDIO INICIA
        n_ciclos, t_anda, v_anda, t_corre, v_corre, dist_alvo = st.session_state.params_cardio

        if st.button("🛑 ENCERRAR E SALVAR"):
            t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
            registrar_historico(None, f"Interrompido: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
            st.session_state.cardio_ativo = False
            st.rerun()

        ph = st.empty()
        etapas = []
        for i in range(n_ciclos):
            etapas.append((f"🚶 Caminhada ({i + 1}/{n_ciclos})", t_anda * 60, v_anda))
            etapas.append((f"⚡ Corrida ({i + 1}/{n_ciclos})", t_corre * 60, v_corre))

        for nome, segs, vel in etapas:
            while segs > 0 and st.session_state.cardio_ativo:
                st.session_state.dist_real += vel / 3600
                m, s = divmod(int(segs), 60)
                ph.markdown(f"""
                    <div class="foco-container" style="border-color:#e066ff; background: black;">
                        <h2 style="color:#e066ff; margin:0;">{nome}</h2>
                        <h1 style="font-size:70px; margin:10px 0;">{m:02d}:{s:02d}</h1>
                        <h3 style="color:#66ffe0;">{st.session_state.dist_real:.2f} / {dist_alvo:.2f} km</h3>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                segs -= 1

        # Salvamento automático no fim
        t_final = int((time.time() - st.session_state.t_cardio_start) // 60)
        registrar_historico(None, f"Concluído: {st.session_state.dist_real:.2f}km | {t_final}min", tipo="cardio")
        st.session_state.cardio_ativo = False
        st.success("Objetivo concluído!")
        st.rerun()

# --- ABA 3: PAINEL DE RENDIMENTO COM FILTRO REORGANIZADO ---
with aba3:
    st.header("📊 Performance & Histórico")

    try:
        # Busca TODOS os dados para permitir o filtro por mês
        res_h = supabase.table("historico_treinos").select("*, exercicios(nome)").order("data_execucao",
                                                                                        desc=True).execute()

        if res_h.data:
            df = pd.json_normalize(res_h.data)
            df['data_execucao'] = pd.to_datetime(df['data_execucao']).dt.tz_convert('America/Sao_Paulo')

            # --- 1. SELETOR DE MÊS/ANO ---
            st.subheader("📅 Filtrar Período")
            col_f1, col_f2 = st.columns(2)

            anos_disponiveis = sorted(df['data_execucao'].dt.year.unique(), reverse=True)
            ano_sel = col_f1.selectbox("Ano", anos_disponiveis, index=0)

            meses_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                           7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            meses_disponiveis = sorted(df[df['data_execucao'].dt.year == ano_sel]['data_execucao'].dt.month.unique(),
                                       reverse=True)
            mes_sel = col_f2.selectbox("Mês", meses_disponiveis, format_func=lambda x: meses_nomes[x])

            # --- FILTRAGEM E CÁLCULOS ---
            df_filtrado = df[(df['data_execucao'].dt.month == mes_sel) & (df['data_execucao'].dt.year == ano_sel)]
            df_hoje = df[df['data_execucao'].dt.date == hoje_agora.date()]
            inicio_semana = (hoje_agora - timedelta(days=hoje_agora.weekday())).replace(hour=0, minute=0)
            df_semana = df[df['data_execucao'] >= inicio_semana]


            def extrair_stats(dataframe):
                if dataframe.empty or 'detalhes' not in dataframe.columns: return 0.0, 0
                kms = dataframe['detalhes'].str.extract(r'(\d+\.\d+)km').astype(float).sum()[0]
                mins = dataframe['detalhes'].str.extract(r'(\d+)min').astype(float).sum()[0]
                return (kms if not pd.isna(kms) else 0.0), (int(mins) if not pd.isna(mins) else 0)


            # --- 2. RESUMO DO MÊS SELECIONADO ---
            st.markdown(f"#### 📈 Resumo de {meses_nomes[mes_sel]}/{ano_sel}")
            c1, c2, c3 = st.columns(3)
            km_f, min_f = extrair_stats(df_filtrado)

            c1.metric("Treinos", len(df_filtrado))
            c2.metric("Distância", f"{km_f:.2f} km")
            c3.metric("Tempo Total", f"{min_f} min")

            # --- 3. EXPANDER: HOJE E ESTA SEMANA (POSIÇÃO SOLICITADA) ---
            with st.expander("📌 Ver Hoje e Esta Semana"):
                km_h, min_h = extrair_stats(df_hoje)
                km_s, min_s = extrair_stats(df_semana)
                st.markdown(f"""
                **Hoje:** {len(df_hoje)} atividades | {km_h:.2f}km | {min_h}min  
                **Esta Semana:** {len(df_semana)} atividades | {km_s:.2f}km | {min_s}min
                """)

            # --- 4. LISTA COMPLETA DO MÊS SELECIONADO ---
            st.divider()
            st.subheader(f"📜 Atividades em {meses_nomes[mes_sel]}")

            if not df_filtrado.empty:
                # Tratamento de nomes e formatação
                if 'exercicios.nome' not in df_filtrado.columns:
                    df_filtrado['exercicios.nome'] = "🏃 Cardio"
                df_filtrado['exercicios.nome'] = df_filtrado['exercicios.nome'].fillna("🏃 Cardio")
                df_filtrado['Data'] = df_filtrado['data_execucao'].dt.strftime('%d/%m/%Y %H:%M')

                st.dataframe(
                    df_filtrado[['Data', 'exercicios.nome', 'detalhes']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"Nenhum registro encontrado para {meses_nomes[mes_sel]}.")

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