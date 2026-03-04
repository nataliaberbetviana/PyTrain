"""
pytrain/db.py
Funções de acesso ao banco de dados (Supabase).
Todas recebem `supabase` e `uid` como parâmetros explícitos — sem depender de session_state.
"""

import re
import pandas as pd
from datetime import datetime


# ── Histórico de treinos ───────────────────────────────────────────────────────

def registrar_historico(supabase, uid: str, fuso, ex_id, detalhes: str, tipo: str = "musculacao"):
    """Insere um registro no histórico de treinos."""
    supabase.table("historico_treinos").insert({
        "user_id":       uid,
        "exercicio_id":  ex_id,
        "data_execucao": datetime.now(fuso).isoformat(),
        "detalhes":      detalhes,
        "tipo":          tipo,
    }).execute()


def buscar_historico_completo(supabase, uid: str):
    """Retorna todos os registros de histórico do usuário com join em exercicios."""
    return supabase.table("historico_treinos")\
        .select("*,exercicios(nome)")\
        .eq("user_id", uid)\
        .order("data_execucao", desc=True)\
        .execute()


# ── Exercícios ─────────────────────────────────────────────────────────────────

def ultima_carga(supabase, uid: str, fuso, ex_id):
    """
    Retorna (detalhes, data_formatada) do último registro do exercício,
    ou (None, None) se não houver histórico.
    """
    try:
        res = supabase.table("historico_treinos")\
            .select("detalhes,data_execucao")\
            .eq("user_id", uid)\
            .eq("exercicio_id", ex_id)\
            .order("data_execucao", desc=True)\
            .limit(1)\
            .execute()
        if res.data:
            det  = res.data[0]["detalhes"]
            data = pd.to_datetime(res.data[0]["data_execucao"]).astimezone(fuso).strftime("%d/%m")
            return det, data
    except Exception:
        pass
    return None, None


def verificar_pr(supabase, uid: str, ex_id, peso_atual: float) -> bool:
    """Retorna True se `peso_atual` é maior que qualquer registro anterior."""
    try:
        res = supabase.table("historico_treinos")\
            .select("detalhes")\
            .eq("user_id", uid)\
            .eq("exercicio_id", ex_id)\
            .execute()
        if not res.data:
            return False
        max_peso = 0.0
        for row in res.data:
            m = re.search(r"([\d.]+)kg", str(row.get("detalhes", "")))
            if m:
                max_peso = max(max_peso, float(m.group(1)))
        return peso_atual > max_peso
    except Exception:
        return False


# ── Conquistas ─────────────────────────────────────────────────────────────────

def desbloquear_conquista(supabase, uid: str, fuso, conquista_id: str):
    """Insere conquista se ainda não existir para o usuário."""
    try:
        ex = supabase.table("conquistas")\
            .select("id")\
            .eq("user_id", uid)\
            .eq("conquista_id", conquista_id)\
            .execute()
        if not ex.data:
            supabase.table("conquistas").insert({
                "user_id":        uid,
                "conquista_id":   conquista_id,
                "desbloqueada_em": datetime.now(fuso).isoformat(),
            }).execute()
    except Exception:
        pass


def verificar_conquistas_treino(supabase, uid: str, fuso, total_treinos: int, streak: int):
    """Desbloqueia conquistas de treino de acordo com os totais informados."""
    mapa = {
        1:   "primeiro_treino",
        5:   "treinos_5",
        10:  "treinos_10",
        25:  "treinos_25",
        50:  "treinos_50",
        100: "treinos_100",
    }
    for limite, cid in mapa.items():
        if total_treinos >= limite:
            desbloquear_conquista(supabase, uid, fuso, cid)

    streak_mapa = {3: "streak_3", 7: "streak_7", 30: "streak_30"}
    for limite, cid in streak_mapa.items():
        if streak >= limite:
            desbloquear_conquista(supabase, uid, fuso, cid)