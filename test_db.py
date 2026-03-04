import os
from cardio import gerar_treino_esteira, formatar_cronograma
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

def registrar_no_historico(ex_id, detalhes, tipo="musculacao"):
    """Salva a execução no banco de dados."""
    try:
        agora = datetime.now().isoformat()
        dados = {
            "exercicio_id": ex_id,
            "data_execucao": agora,
            "detalhes": detalhes,
            "tipo": tipo
        }
        supabase.table("historico_treinos").insert(dados).execute()
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")


def visualizar_historico():
    print("\n--- 📜 MEU HISTÓRICO RECENTE ---")
    # Busca os últimos 15 treinos fazendo um 'join' com a tabela de exercícios para pegar o nome
    res = supabase.table("historico_treinos").select("data_execucao, detalhes, exercicios(nome)").order("data_execucao",
                                                                                                        desc=True).limit(
        15).execute()

    if not res.data:
        print("Nenhum treino registrado ainda.")
        return

    for item in res.data:
        data = datetime.fromisoformat(item['data_execucao']).strftime("%d/%m %H:%M")
        # Trata o caso de cardio que pode não ter um link direto com a tabela 'exercicios' dependendo de como você salvou
        nome = item['exercicios']['nome'] if item['exercicios'] else "Cardio/Config Salva"
        print(f"[{data}] {nome}: {item['detalhes']}")


def menu_zerar_dados():
    print("\n--- 🧹 ZERAR DADOS (CUIDADO!) ---")
    print("1. Apagar APENAS o Histórico")
    print("2. Zerar todos os Pesos (Mantém os nomes)")
    print("3. Apagar TUDO (Exercícios, Cardio e Histórico)")
    print("4. Voltar")

    escolha = input("O que deseja zerar? ")
    confirmar = input(f"Tem certeza? Digite 'ZERA' para confirmar: ")

    # Esta string é o formato que o banco espera para um ID do tipo UUID
    UUID_ZERO = "00000000-0000-0000-0000-000000000000"

    if confirmar.upper() != "ZERA":
        print("Operação cancelada.")
        return

    try:
        if escolha == "1":
            # Deleta histórico comparando com o formato UUID correto
            supabase.table("historico_treinos").delete().neq("id", UUID_ZERO).execute()
            print("✅ Histórico limpo!")

        elif escolha == "2":
            # Reseta pesos: Onde o ID for diferente do UUID de zeros (ou seja, todos)
            supabase.table("exercicios").update({"peso_kg": 0}).neq("id", UUID_ZERO).execute()
            print("✅ Todos os pesos resetados para 0kg!")

        elif escolha == "3":
            # Apaga tudo usando a comparação de UUID em todas as tabelas
            supabase.table("historico_treinos").delete().neq("id", UUID_ZERO).execute()
            supabase.table("exercicios").delete().neq("id", UUID_ZERO).execute()
            supabase.table("configuracao_cardio").delete().neq("id", UUID_ZERO).execute()
            print("✅ Sistema resetado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao zerar: {e}")

# Configurações de Conexão
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(url, key)
    print("🚀 PyTrain API: Sistema Online!")
except Exception as e:
    print(f"❌ Conexão falhou: {e}")


# --- AUXILIARES ---

def exercicio_existe(nome_teste):
    """Verifica se o nome já existe no banco (ignora maiúsculas/minúsculas)."""
    res = supabase.table("exercicios").select("nome").execute()
    nomes_no_banco = [ex['nome'].strip().lower() for ex in res.data]
    return nome_teste.strip().lower() in nomes_no_banco


# --- MÓDULO DE GERENCIAMENTO ---

def cadastrar_novo_exercicio():
    print("\n--- ✨ CADASTRAR NOVO EXERCÍCIO ---")
    nome_input = input("Nome do exercício: ").strip()

    if exercicio_existe(nome_input):
        print(f"⚠️ Erve: O exercício '{nome_input}' já existe no seu catálogo!")
        return None

    try:
        peso = int(input("Peso inicial (kg): ") or 0)
        series = int(input("Séries: ") or 3)
        reps = int(input("Repetições: ") or 12)

        novo = {
            "nome": nome_input,
            "peso_kg": peso,
            "series": series,
            "repeticoes": reps,
            "tipo_repeticao": "movimento"
        }
        res = supabase.table("exercicios").insert(novo).execute()
        print(f"✅ '{nome_input}' adicionado com sucesso!")
        return res.data[0]
    except Exception as e:
        print(f"❌ Erro ao cadastrar: {e}")
        return None


def editar_exercicio_api(id_ex, novos_dados):
    # Se estiver tentando mudar o nome, verifica se o novo nome já existe
    if "nome" in novos_dados and exercicio_existe(novos_dados["nome"]):
        print(f"⚠️ Erro: Não é possível mudar para '{novos_dados['nome']}' porque esse nome já existe!")
        return

    try:
        supabase.table("exercicios").update(novos_dados).eq("id", id_ex).execute()
        print(f"✅ Alteração concluída!")
    except Exception as e:
        print(f"❌ Erro na edição: {e}")


def listar_serie(letra):
    res = supabase.table("exercicios").select("*").eq("serie_tipo", letra.upper()).execute()
    return res.data


# --- MÓDULO DE EXECUÇÃO ---

def atualizar_peso_manual(id_ex, novo_peso):
    try:
        supabase.table("exercicios").update({"peso_kg": novo_peso}).eq("id", id_ex).execute()
        return True
    except:
        return False


def resumo_do_dia():
    print("\n--- 🏁 RESUMO DO TREINO DE HOJE ---")
    hoje = datetime.now().date().isoformat()
    volume_total = 0

    try:
        res = supabase.table("historico_treinos") \
            .select("detalhes, exercicios(nome, series, repeticoes)") \
            .gte("data_execucao", hoje).execute()

        if not res.data:
            print("Nenhum registro hoje.")
            return

        for item in res.data:
            nome = item['exercicios']['nome'] if item['exercicios'] else "Cardio"
            print(f"✅ {nome}: {item['detalhes']}")

            # Cálculo de Volume (apenas se for musculação)
            if item['exercicios']:
                # Extraímos o peso do texto "80kg | 3x12" ou usamos os campos da tabela
                peso = int(item['detalhes'].split('kg')[0])
                volume_ex = peso * item['exercicios']['series'] * item['exercicios']['repeticoes']
                volume_total += volume_ex

        print("-" * 30)
        print(f"📊 VOLUME TOTAL MOVIDO: {volume_total} kg")
        print("Parabéns, Natália! 🚀")
    except Exception as e:
        print(f"❌ Erro no resumo: {e}")


def calendario_semanal():
    import datetime as dt
    print("\n--- 📅 FREQUÊNCIA NA SEMANA ---")

    hoje = dt.date.today()
    inicio_semana = hoje - dt.timedelta(days=hoje.weekday())  # Segunda-feira

    res = supabase.table("historico_treinos") \
        .select("data_execucao") \
        .gte("data_execucao", inicio_semana.isoformat()) \
        .execute()

    # Dias que tiveram treino
    dias_treinados = {datetime.fromisoformat(treino['data_execucao']).date() for treino in res.data}

    dias_nome = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    display = ""

    for i in range(7):
        dia_foco = inicio_semana + dt.timedelta(days=i)
        status = "✅" if dia_foco in dias_treinados else "❌"
        display += f"{dias_nome[i]}: {status}  "

    print(display)


def exportar_dados_csv():
    import csv
    print("⏳ Gerando ficheiro de backup...")

    try:
        res = supabase.table("historico_treinos").select("data_execucao, detalhes, tipo, exercicios(nome)").execute()

        filename = f"treinos_natalia_{datetime.now().strftime('%Y%m%d')}.csv"

        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Data", "Exercicio", "Detalhes", "Tipo"])

            for linha in res.data:
                data = datetime.fromisoformat(linha['data_execucao']).strftime("%d/%m/%Y %H:%M")
                nome = linha['exercicios']['nome'] if linha['exercicios'] else "Cardio"
                writer.writerow([data, nome, linha['detalhes'], linha['tipo']])

        print(f"✅ Sucesso! Ficheiro '{filename}' criado na pasta do projeto.")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")

# --- MENU ---

if __name__ == "__main__":
    while True:
        print("\n--- 📱 MENU PYTRAIN ---")
        print("1. Treinar (Série A/B/C)")
        print("2. Gerenciar Catálogo")
        print("3. Editar Exercício")
        print("4. Cardio (Esteira)")
        print("5. Ver Histórico e Frequência")
        print("6. Exportar Backup (CSV)")
        print("7. Configurações (Zerar Dados)")
        print("8. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            letra = input("Qual série hoje? ").upper()
            treino = listar_serie(letra)
            if not treino:
                print(f"⚠️ Ninguém na Série {letra}.")
            else:
                for ex in treino:
                    print(f"\n🏋️ {ex['nome']} | Último: {ex['peso_kg']}kg")
                    nova_carga = input(f"Peso hoje (Enter para manter {ex['peso_kg']}kg): ")
                    peso_atual = int(nova_carga) if nova_carga.strip() else ex['peso_kg']

                    if nova_carga.strip():
                        atualizar_peso_manual(ex['id'], peso_atual)

                    # REGISTRA NO HISTÓRICO
                    registrar_no_historico(ex['id'], f"{peso_atual}kg | {ex['series']}x{ex['repeticoes']}")

                print("\n🏆 Treino Concluído!")
                resumo_do_dia()  # Mostra o resumo logo após terminar a série

        elif opcao == "2":
            cadastrar_novo_exercicio()

        elif opcao == "3":
            # Listagem para edição
            res = supabase.table("exercicios").select("id, nome").execute()
            for i, ex in enumerate(res.data):
                print(f"[{i}] {ex['nome']}")

            try:
                idx = int(input("Número do exercício para editar: "))
                id_edit = res.data[idx]['id']
                print("\nO que deseja mudar?")
                novo_nome = input("Novo nome (Enter para manter): ").strip()
                nova_serie = input("Nova Série (A/B/C) (Enter para manter): ").upper()
                dados = {}
                if novo_nome: dados["nome"] = novo_nome
                if nova_serie: dados["serie_tipo"] = nova_serie
                if dados: editar_exercicio_api(id_edit, dados)
            except:
                print("❌ Seleção inválida.")

        elif opcao == "4":
            print("\n--- 🏃 MÓDULO ESTEIRA ---")
            print("1. Usar um Setting Salvo")
            print("2. Criar Novo Treino")
            sub_opcao = input("Escolha: ")

            # ... seu código de cardio aqui ...
            # Lembre-se de adicionar ao final da execução do cardio:
            # registrar_no_historico(None, f"{t_total}min de Esteira", tipo="cardio")


        elif opcao == "5":

            visualizar_historico()

            calendario_semanal()

        elif opcao == "6":

            exportar_dados_csv()

        elif opcao == "7":

            menu_zerar_dados()