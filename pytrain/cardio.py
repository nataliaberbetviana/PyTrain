"""
pytrain/cardio.py
Lógica de treino de cardio/esteira.
- Geração de etapas
- Timer baseado em tempo real (não em contagem de reruns)
- Cálculo de distância por etapa
"""

import time


# ── Geração de etapas ──────────────────────────────────────────────────────────

def gerar_etapas(n_ciclos: int, t_anda: float, v_anda: float,
                 t_corre: float, v_corre: float) -> list[tuple]:
    """
    Gera a lista de etapas do treino intervalado.
    Cada etapa é uma tupla: (nome: str, duracao_seg: int, velocidade: float)
    """
    etapas = []
    total = int(n_ciclos)
    for i in range(total):
        etapas.append((
            f"Caminhada {i+1}/{total}",
            int(t_anda * 60),
            v_anda,
        ))
        etapas.append((
            f"Corrida {i+1}/{total}",
            int(t_corre * 60),
            v_corre,
        ))
    return etapas


def distancia_ciclo(t_anda: float, v_anda: float, t_corre: float, v_corre: float) -> float:
    """Distância percorrida em um ciclo completo (km)."""
    return (v_anda * (t_anda / 60)) + (v_corre * (t_corre / 60))


# ── Timer em tempo real ────────────────────────────────────────────────────────

def calcular_estado_cardio(params: dict) -> dict:
    """
    Calcula o estado atual do cardio usando `time.time()` como referência,
    independente da frequência de reruns do Streamlit.

    Recebe `params` (dict salvo em session_state) e retorna um dict com:
      - etapa_idx: int          índice atual
      - seg_restantes: int      segundos restantes na etapa
      - dist_real: float        distância percorrida até agora (km)
      - nome_etapa: str
      - velocidade: float
      - concluido: bool
      - params: dict            params atualizados (com etapa_start)
    """
    etapas   = params["etapas"]
    idx      = params["etapa_idx"]

    # Garante que o timestamp de início da etapa existe
    if "etapa_start" not in params:
        params["etapa_start"] = time.time()

    agora            = time.time()
    decorrido_etapa  = agora - params["etapa_start"]

    # Avança etapas se o tempo real já passou
    while idx < len(etapas) and decorrido_etapa >= etapas[idx][1]:
        decorrido_etapa -= etapas[idx][1]
        idx += 1
        params["etapa_start"] = agora - decorrido_etapa   # ajusta o início da nova etapa
        params["etapa_idx"]   = idx

    # Treino concluído
    if idx >= len(etapas):
        dist = _calcular_distancia_total(etapas, len(etapas), 0)
        return {
            "concluido":     True,
            "etapa_idx":     idx,
            "seg_restantes": 0,
            "dist_real":     dist,
            "nome_etapa":    "",
            "velocidade":    0.0,
            "params":        params,
        }

    nome_et, dur_et, vel_et = etapas[idx]
    seg_restantes = max(0, int(dur_et - decorrido_etapa))
    dist_real     = _calcular_distancia_total(etapas, idx, decorrido_etapa)

    return {
        "concluido":     False,
        "etapa_idx":     idx,
        "seg_restantes": seg_restantes,
        "dist_real":     dist_real,
        "nome_etapa":    nome_et,
        "velocidade":    vel_et,
        "params":        params,
    }


def _calcular_distancia_total(etapas: list, idx_atual: int, decorrido_atual: float) -> float:
    """Soma a distância de todas as etapas concluídas + fração da etapa atual."""
    dist = 0.0
    for i, (_, dur, vel) in enumerate(etapas):
        if i < idx_atual:
            dist += vel * (dur / 3600)
        elif i == idx_atual:
            frac = min(decorrido_atual, dur)
            dist += vel * (frac / 3600)
            break
    return dist


# ── Gerador de cronograma (terminal / cardio.py original) ─────────────────────

def gerar_treino_esteira(t_total, t_correr, t_descanso, t_pre_pos,
                         v_andar, v_correr) -> list[dict]:
    """
    Gera cronograma com Aquecimento e Desaceleração dentro do tempo total.
    Compatível com o cardio.py original.
    """
    if (t_pre_pos * 2) >= t_total:
        return [{"acao": "ERRO", "minutos": 0,
                 "mensagem": "Tempo de aquecimento/desaceleração muito alto para o total!"}]

    cronograma = [{"acao": "AQUECIMENTO (ANDAR)", "minutos": t_pre_pos, "velocidade": v_andar}]

    tempo_miolo = t_total - (t_pre_pos * 2)
    decorrido   = 0

    while decorrido < tempo_miolo:
        dur_c = min(t_correr,   tempo_miolo - decorrido)
        if dur_c > 0:
            cronograma.append({"acao": "CORRER", "minutos": dur_c, "velocidade": v_correr})
            decorrido += dur_c
        if decorrido >= tempo_miolo:
            break
        dur_d = min(t_descanso, tempo_miolo - decorrido)
        if dur_d > 0:
            cronograma.append({"acao": "DESCANSAR (ANDAR)", "minutos": dur_d, "velocidade": v_andar})
            decorrido += dur_d

    cronograma.append({"acao": "DESACELERAR (ANDAR)", "minutos": t_pre_pos, "velocidade": v_andar})
    return cronograma


def formatar_cronograma(plano: list[dict]) -> str:
    if plano[0].get("acao") == "ERRO":
        return f"❌ {plano[0]['mensagem']}"

    resultado = "\n--- 🏃 PLANO DE CARDIO (TEMPO TOTAL FIXO) ---\n"
    for i, etapa in enumerate(plano):
        emoji = "🔥" if "CORRER" in etapa["acao"] else "🚶"
        resultado += f"{i+1}. {etapa['acao']} {emoji} | {etapa['minutos']} min | Vel: {etapa['velocidade']} km/h\n"
    resultado += f"-------------------------------------------\n"
    resultado += f"Tempo Total: {sum(e['minutos'] for e in plano)} min\n"
    return resultado