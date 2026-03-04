"""
pytrain/utils.py
Funções utilitárias gerais: formatação, frases, conquistas, stats.
"""

import re
import random
import pandas as pd
from datetime import datetime, timedelta

# ── Frases motivacionais ───────────────────────────────────────────────────────

FRASES = [
    "O único treino ruim é aquele que não aconteceu. 💜",
    "Cada rep te aproxima da melhor versão de você. 🔥",
    "Consistência bate perfeição sempre. 🏆",
    "Seu corpo consegue. É sua mente que precisa ser convencida. 💪",
    "Pequenos progressos ainda são progressos. ⚡",
    "Você não vai se arrepender de ter treinado. Promessa. 🌟",
    "A dor de hoje é a força de amanhã. 🚀",
    "Foco. Disciplina. Resultado. 🎯",
    "Mais um dia, mais um treino, mais uma conquista. ✨",
    "Você é mais forte do que imagina. Sempre. 💫",
    "Não espere motivação. Crie o hábito. 🔑",
    "Cada gota de suor é um investimento em você mesma. 💧",
    "O corpo alcança o que a mente acredita. 🧠",
    "Descanso é parte do treino. Volta amanhã mais forte. 😴",
    "Ninguém se arrepende de ter se exercitado. Nunca. 🙌",
    "Sua única competição é quem você era ontem. 📈",
    "Vai com tudo. Você merece sentir essa sensação no fim. 🎉",
    "Treinar é um presente que você dá pro seu futuro. 🎁",
    "Um passo de cada vez. O caminho se faz caminhando. 👣",
    "Força não é o que você tem. É o que você descobre quando não aguenta mais. 💎",
    "Hoje pode ser difícil. Amanhã vai valer a pena. ☀️",
    "Seu esforço não some. Ele se acumula. 📊",
    "Seja orgulhosa de cada treino. Você apareceu. Isso já é tudo. 🌸",
    "A versão mais forte de você está sendo construída agora. 🏗️",
    "Não precisa ser perfeito. Precisa ser constante. 🔄",
    "Você já fez isso antes. Você faz de novo. 💥",
    "Cada série é uma escolha por você mesma. ❤️",
    "O cansaço passa. O orgulho fica. 🥇",
    "Mais forte do que qualquer desculpa. 🚫",
    "Você não treina pra impressionar ninguém. Treina pra se sentir incrível. 🌟",
]

# ── Definição de conquistas ────────────────────────────────────────────────────

CONQUISTAS_DEF = [
    {"id": "primeiro_treino",    "emoji": "🌱", "nome": "Primeiro passo",      "desc": "Completou o primeiro treino"},
    {"id": "treinos_5",          "emoji": "🔥", "nome": "Pegando fogo",         "desc": "5 treinos concluídos"},
    {"id": "treinos_10",         "emoji": "💪", "nome": "Dez e contando",       "desc": "10 treinos concluídos"},
    {"id": "treinos_25",         "emoji": "⚡", "nome": "Máquina",              "desc": "25 treinos concluídos"},
    {"id": "treinos_50",         "emoji": "🚀", "nome": "Imparável",            "desc": "50 treinos concluídos"},
    {"id": "treinos_100",        "emoji": "🏆", "nome": "Lendária",             "desc": "100 treinos concluídos"},
    {"id": "streak_3",           "emoji": "📅", "nome": "3 dias seguidos",      "desc": "Treinou 3 dias consecutivos"},
    {"id": "streak_7",           "emoji": "🗓️", "nome": "Semana cheia",         "desc": "Treinou 7 dias consecutivos"},
    {"id": "streak_30",          "emoji": "🌙", "nome": "Mês invicta",          "desc": "Treinou 30 dias consecutivos"},
    {"id": "pr_primeiro",        "emoji": "🎯", "nome": "Novo recorde!",        "desc": "Bateu o primeiro PR"},
    {"id": "cardio_5km",         "emoji": "🏃", "nome": "5 km!",               "desc": "Correu 5 km em uma sessão"},
    {"id": "cardio_10km",        "emoji": "🛣️", "nome": "10 km!",              "desc": "Correu 10 km em uma sessão"},
    {"id": "peso_registrado",    "emoji": "⚖️", "nome": "Me pesando",           "desc": "Registrou o peso corporal"},
    {"id": "medidas_registradas","emoji": "📏", "nome": "Me medindo",           "desc": "Registrou as medidas corporais"},
]

# ── Formatação ─────────────────────────────────────────────────────────────────

def fmt_tempo(minutos: int) -> str:
    """Formata minutos em string legível: '1h 30min' ou '45min'."""
    if minutos >= 60:
        h, m = divmod(minutos, 60)
        return f"{h}h {m}min" if m else f"{h}h"
    return f"{minutos}min"


def fmt_mm_ss(segundos: int) -> str:
    """Formata segundos em 'MM:SS'."""
    m, s = divmod(max(0, segundos), 60)
    return f"{m:02d}:{s:02d}"

# ── Extração de stats do histórico ────────────────────────────────────────────

def extrair_stats(df: pd.DataFrame):
    """
    Varre a coluna 'detalhes' e extrai km, minutos e volume (kg × séries × reps).
    Retorna: (km_total: float, min_total: int, kg_total: float)
    """
    if df.empty or "detalhes" not in df.columns:
        return 0.0, 0, 0.0

    km_total = 0.0
    min_total = 0
    kg_total = 0.0

    for det in df["detalhes"].dropna():
        det = str(det)
        m = re.search(r"([\d.]+)km", det)
        if m:
            km_total += float(m.group(1))
        for mm in re.findall(r"(\d+)min", det):
            min_total += int(mm)
        m_kg = re.search(r"([\d.]+)kg", det)
        m_sets = re.search(r"(\d+)x(\d+)", det)
        if m_kg and m_sets:
            kg_total += float(m_kg.group(1)) * int(m_sets.group(1)) * int(m_sets.group(2))

    return km_total, min_total, kg_total


def extrair_peso_total(df: pd.DataFrame) -> float:
    """Atalho que retorna apenas o volume de kg."""
    _, _, kg = extrair_stats(df)
    return kg

# ── Streak ─────────────────────────────────────────────────────────────────────

def calcular_streak(df_hist: pd.DataFrame, hoje) -> int:
    """
    Calcula quantos dias consecutivos o usuário treinou até hoje.
    `hoje` deve ser um objeto `date`.
    """
    if df_hist.empty:
        return 0
    datas = sorted(df_hist["data_execucao"].dt.date.unique(), reverse=True)
    streak = 0
    ref = hoje
    for d in datas:
        if d == ref or d == ref - timedelta(days=1):
            streak += 1
            ref = d
        else:
            break
    return streak

# ── Frase por aba (stateful via st.session_state) ─────────────────────────────

def frase_aba(nome_aba: str, session_state) -> str:
    """
    Retorna uma frase motivacional, trocando sempre que o usuário muda de aba.
    Recebe `st.session_state` explicitamente para evitar importar streamlit aqui.
    """
    if session_state.get("aba_anterior") != nome_aba:
        session_state["frase_idx"] = (session_state.get("frase_idx", 0) + 1) % len(FRASES)
        session_state["aba_anterior"] = nome_aba
    return FRASES[session_state.get("frase_idx", 0)]