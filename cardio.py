# cardio.py

def gerar_treino_esteira(t_total, t_correr, t_descanso, t_pre_pos, v_andar, v_correr):
    """
    Gera o cronograma onde o Aquecimento e Desaceleração estão DENTRO do tempo total.
    """
    cronograma = []

    # 1. Validação de segurança: o pré + pós não pode ser maior que o total
    if (t_pre_pos * 2) >= t_total:
        return [
            {"acao": "ERRO", "minutos": 0, "mensagem": "Tempo de aquecimento/desaceleração muito alto para o total!"}]

    # 2. Aquecimento Inicial
    cronograma.append({"acao": "AQUECIMENTO (ANDAR)", "minutos": t_pre_pos, "velocidade": v_andar})

    # 3. Cálculo do tempo disponível para os ciclos (MIOLO)
    tempo_miolo_restante = t_total - (t_pre_pos * 2)
    tempo_decorrido_miolo = 0

    while tempo_decorrido_miolo < tempo_miolo_restante:
        # Bloco de Corrida 🔥
        duracao_corrida = min(t_correr, tempo_miolo_restante - tempo_decorrido_miolo)
        if duracao_corrida > 0:
            cronograma.append({"acao": "CORRER", "minutos": duracao_corrida, "velocidade": v_correr})
            tempo_decorrido_miolo += duracao_corrida

        if tempo_decorrido_miolo >= tempo_miolo_restante:
            break

        # Bloco de Descanso 🧊
        duracao_descanso = min(t_descanso, tempo_miolo_restante - tempo_decorrido_miolo)
        if duracao_descanso > 0:
            cronograma.append({"acao": "DESCANSAR (ANDAR)", "minutos": duracao_descanso, "velocidade": v_andar})
            tempo_decorrido_miolo += duracao_descanso

    # 4. Desaceleração Final
    cronograma.append({"acao": "DESACELERAR (ANDAR)", "minutos": t_pre_pos, "velocidade": v_andar})

    return cronograma


def formatar_cronograma(plano):
    if plano[0].get("acao") == "ERRO":
        return f"❌ {plano[0]['mensagem']}"

    resultado = "\n--- 🏃 PLANO DE CARDIO (TEMPO TOTAL FIXO) ---\n"
    tempo_calculado = sum(etapa['minutos'] for etapa in plano)

    for i, etapa in enumerate(plano):
        emoji = "🔥" if "CORRER" in etapa['acao'] else "🚶"
        resultado += f"{i + 1}. {etapa['acao']} {emoji} | {etapa['minutos']} min | Vel: {etapa['velocidade']} km/h\n"

    resultado += f"---------------------------------------------\n"
    resultado += f"Tempo Total de Esteira: {tempo_calculado} min\n"
    return resultado


import time
import sys


def executar_cronometro_treino(plano):
    """
    Executa o treino em tempo real com contagem regressiva no terminal.
    """
    print("\n🚀 PREPARE-SE! O TREINO VAI COMEÇAR...")
    time.sleep(2)  # Pequena pausa para você subir na esteira

    for etapa in plano:
        acao = etapa['acao']
        minutos = etapa['minutos']
        vel = etapa['velocidade']
        segundos_totais = int(minutos * 60)

        print(f"\n--- 🔔 MUDANÇA DE RITMO! ---")
        print(f"AGORA: {acao}")
        print(f"VELOCIDADE: {vel} km/h")
        # Emite um "beep" no sistema (funciona na maioria dos terminais Linux)
        print('\a', end='', flush=True)

        # Contagem regressiva interna
        while segundos_totais > 0:
            mins, segs = divmod(segundos_totais, 60)
            # Formata o tempo como 00:00 e sobrescreve a mesma linha
            sys.stdout.write(f"\r⏱️ Tempo restante nesta etapa: {mins:02d}:{segs:02d} ")
            sys.stdout.flush()
            time.sleep(1)
            segundos_totais -= 1

        print(f"\n✅ Etapa concluída!")

    print("\n🏁 TREINO FINALIZADO! PARABÉNS, NATÁLIA! 🔥")