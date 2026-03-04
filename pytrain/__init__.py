"""
pytrain — biblioteca interna do PyTrain PRO
"""
from .utils  import (
    FRASES, CONQUISTAS_DEF,
    fmt_tempo, fmt_mm_ss,
    extrair_stats, extrair_peso_total,
    calcular_streak, frase_aba,
)
from .auth   import (
    cookie_get, cookie_set,
    fazer_login, restaurar_sessao, fazer_logout,
    verificar_perfil,
)
from .db     import (
    registrar_historico, buscar_historico_completo,
    ultima_carga, verificar_pr,
    desbloquear_conquista, verificar_conquistas_treino,
)
from .cardio import (
    gerar_etapas, distancia_ciclo,
    calcular_estado_cardio,
    gerar_treino_esteira, formatar_cronograma,
)