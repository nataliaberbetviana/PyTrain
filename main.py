import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Componentes de estética Rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint

console = Console()

# --- CONFIGURAÇÃO ---
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(URL, KEY)
    rprint("[bold green]🚀 PyTrain API: Sistema Online![/bold green]")
except Exception as e:
    rprint(f"[bold red]❌ Conexão falhou: {e}[/bold red]")


# --- MÓDULO DE DADOS ---

def registrar_no_historico(ex_id, detalhes, tipo="musculacao"):
    try:
        dados = {
            "exercicio_id": ex_id,
            "data_execucao": datetime.now().isoformat(),
            "detalhes": detalhes,
            "tipo": tipo
        }
        supabase.table("historico_treinos").insert(dados).execute()
    except Exception as e:
        console.print(f"[red]⚠️ Erro ao salvar histórico: {e}[/red]")


def resumo_do_dia_visual():
    hoje = datetime.now().date().isoformat()
    volume_total = 0
    try:
        res = supabase.table("historico_treinos") \
            .select("detalhes, exercicios(nome, series, repeticoes)") \
            .gte("data_execucao", hoje).execute()

        if not res.data:
            return

        table = Table(title=f"🏁 Resumo de Hoje - {datetime.now().strftime('%d/%m/%Y')}", header_style="bold magenta")
        table.add_column("Exercício", style="cyan")
        table.add_column("Detalhes", justify="center")
        table.add_column("Volume Est.", style="green")

        for item in res.data:
            nome = item['exercicios']['nome'] if item['exercicios'] else "Cardio"
            detalhes = item['detalhes']
            vol_ex = 0
            if item['exercicios']:
                try:
                    peso = int(detalhes.split('kg')[0])
                    vol_ex = peso * item['exercicios']['series'] * item['exercicios']['repeticoes']
                    volume_total += vol_ex
                except:
                    pass
            table.add_row(nome, detalhes, f"{vol_ex} kg" if vol_ex > 0 else "-")

        console.print(table)
        console.print(Panel(f"[bold green]📊 VOLUME TOTAL MOVIDO: {volume_total} kg[/bold green]", expand=False))
    except Exception as e:
        console.print(f"[red]❌ Erro no resumo: {e}[/red]")


def exibir_calendario_semanal():
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    try:
        res = supabase.table("historico_treinos").select("data_execucao").gte("data_execucao",
                                                                              inicio_semana.isoformat()).execute()
        dias_treinados = {datetime.fromisoformat(t['data_execucao']).date() for t in res.data}
        dias_nome = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        cal_str = ""
        for i, nome in enumerate(dias_nome):
            dia_foco = inicio_semana + timedelta(days=i)
            status = "[green]✅[/green]" if dia_foco in dias_treinados else "[red]⚪[/red]"
            cal_str += f"{nome} {status}   "

        console.print(Panel(cal_str, title="📅 Frequência Semanal", border_style="blue", expand=False))
    except Exception as e:
        console.print(f"[red]❌ Erro no calendário: {e}[/red]")


# --- MÓDULO DE GERENCIAMENTO ---

def cadastrar_novo_exercicio():
    console.print("\n[bold cyan]--- ✨ CADASTRAR NOVO EXERCÍCIO ---[/bold cyan]")
    nome = Prompt.ask("Nome do exercício")

    # Validação simples
    res = supabase.table("exercicios").select("nome").execute()
    if any(ex['nome'].lower() == nome.lower() for ex in res.data):
        rprint(f"[yellow]⚠️ O exercício '{nome}' já existe![/yellow]")
        return

    try:
        peso = int(Prompt.ask("Peso inicial (kg)", default="0"))
        series = int(Prompt.ask("Séries", default="3"))
        reps = int(Prompt.ask("Repetições", default="12"))
        serie_tipo = Prompt.ask("Série", choices=["A", "B", "C"]).upper()

        novo = {"nome": nome, "peso_kg": peso, "series": series, "repeticoes": reps, "serie_tipo": serie_tipo}
        supabase.table("exercicios").insert(novo).execute()
        rprint(f"[bold green]✅ '{nome}' adicionado à Série {serie_tipo}![/bold green]")
    except Exception as e:
        rprint(f"[red]❌ Erro: {e}[/red]")


def exportar_backup():
    try:
        res = supabase.table("historico_treinos").select("data_execucao, detalhes, exercicios(nome)").execute()
        filename = f"backup_treinos_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["Data", "Exercicio", "Detalhes"])
            for r in res.data:
                nome = r['exercicios']['nome'] if r['exercicios'] else "Cardio"
                w.writerow([r['data_execucao'], nome, r['detalhes']])
        rprint(f"[bold green]✅ Backup salvo: {filename}[/bold green]")
    except Exception as e:
        rprint(f"[red]❌ Erro no backup: {e}[/red]")


def menu_zerar_dados():
    console.print(Panel("[bold red]⚠️ ZONA DE PERIGO[/bold red]\n1. Zerar Histórico\n2. Zerar Pesos\n3. Apagar TUDO",
                        border_style="red"))
    escolha = Prompt.ask("Escolha", choices=["1", "2", "3", "4"], default="4")
    if escolha == "4": return

    confirmar = Prompt.ask("Digite [bold red]ZERA[/bold red] para confirmar")
    if confirmar != "ZERA": return

    UUID_ZERO = "00000000-0000-0000-0000-000000000000"
    try:
        if escolha == "1":
            supabase.table("historico_treinos").delete().neq("id", UUID_ZERO).execute()
        elif escolha == "2":
            supabase.table("exercicios").update({"peso_kg": 0}).neq("id", UUID_ZERO).execute()
        elif escolha == "3":
            supabase.table("historico_treinos").delete().neq("id", UUID_ZERO).execute()
            supabase.table("exercicios").delete().neq("id", UUID_ZERO).execute()
        rprint("[bold green]✅ Operação concluída![/bold green]")
    except Exception as e:
        rprint(f"[red]❌ Erro: {e}[/red]")


def editar_catalogo_visual():
    console.print("\n[bold cyan]📝 EDITAR CATÁLOGO DE EXERCÍCIOS[/bold cyan]")

    try:
        # Busca todos os exercícios ordenados por série e nome
        res = supabase.table("exercicios").select("id, nome, serie_tipo, peso_kg, series, repeticoes").order(
            "serie_tipo").execute()

        if not res.data:
            rprint("[yellow]Nenhum exercício encontrado para editar.[/yellow]")
            return

        # Tabela para seleção
        table = Table(title="Selecione o Exercício", header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Nome", style="cyan")
        table.add_column("Série", justify="center")
        table.add_column("Config Atual", justify="right")

        for i, ex in enumerate(res.data):
            table.add_row(str(i), ex['nome'], ex['serie_tipo'],
                          f"{ex['series']}x{ex['repeticoes']} - {ex['peso_kg']}kg")

        console.print(table)

        idx = int(Prompt.ask("\nDigite o número do exercício que deseja editar (ou '99' para cancelar)"))
        if idx == 99: return

        ex_selecionado = res.data[idx]

        rprint(f"\n[yellow]Editando: {ex_selecionado['nome']}[/yellow]")
        rprint("[gray](Pressione Enter para manter o valor atual)[/gray]\n")

        novo_nome = Prompt.ask("Novo nome", default=ex_selecionado['nome'])
        nova_serie = Prompt.ask("Nova Série", choices=["A", "B", "C"], default=ex_selecionado['serie_tipo']).upper()
        novas_series = int(Prompt.ask("Novas Séries", default=str(ex_selecionado['series'])))
        novas_reps = int(Prompt.ask("Novas Repetições", default=str(ex_selecionado['repeticoes'])))

        dados_atualizados = {
            "nome": novo_nome,
            "serie_tipo": nova_serie,
            "series": novas_series,
            "repeticoes": novas_reps
        }

        supabase.table("exercicios").update(dados_atualizados).eq("id", ex_selecionado['id']).execute()
        rprint(f"\n[bold green]✅ '{novo_nome}' atualizado com sucesso![/bold green]")

    except Exception as e:
        rprint(f"[red]❌ Erro na edição: {e}[/red]")

# --- MAIN LOOP ---

if __name__ == "__main__":
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(Panel.fit(
            "[bold magenta]🏋️ PYTRAIN PRO[/bold magenta]",
            subtitle="Natália Berbet Viana",
            border_style="cyan"
        ))

        exibir_calendario_semanal()

        table = Table(show_header=False, box=None)
        # Seção de Treino
        table.add_row("[bold yellow]1[/bold yellow]", "🚀 Iniciar Treino (Série A/B/C)")
        table.add_row("[bold yellow]2[/bold yellow]", "✨ Novo Exercício (Catálogo)")

        # Seção de Consulta e Relatórios
        table.add_row("[bold yellow]3[/bold yellow]", "📜 Ver Histórico de Treinos")
        table.add_row("[bold yellow]4[/bold yellow]", "📝 Editar Catálogo (Nomes/Séries)")
        table.add_row("[bold yellow]5[/bold yellow]", "📊 Resumo de Hoje (Volume Total)")

        # Seção de Utilidades
        table.add_row("[bold yellow]6[/bold yellow]", "📦 Exportar Backup (CSV)")
        table.add_row("[bold yellow]7[/bold yellow]", "🧹 Configurações (Zerar Dados)")
        table.add_row("[bold red]0[/bold red]", "❌ Sair")

        console.print(table)

        opcao = Prompt.ask("\nEscolha uma opção", choices=["1", "2", "3", "4", "5", "6", "7", "0"])

        if opcao == "1":
            letra = Prompt.ask("Série", choices=["A", "B", "C"]).upper()
            res = supabase.table("exercicios").select("*").eq("serie_tipo", letra).execute()
            if not res.data:
                rprint("[yellow]Nenhum exercício nesta série.[/yellow]")
            else:
                for ex in res.data:
                    console.print(f"\n[bold cyan]▶ {ex['nome']}[/bold cyan] [white]({ex['peso_kg']}kg)[/white]")
                    nova_carga = console.input("[gray]Nova carga (ou Enter): [/gray]")
                    peso = int(nova_carga) if nova_carga.strip() else ex['peso_kg']

                    if nova_carga.strip():
                        supabase.table("exercicios").update({"peso_kg": peso}).eq("id", ex['id']).execute()

                    registrar_no_historico(ex['id'], f"{peso}kg | {ex['series']}x{ex['repeticoes']}")

                resumo_do_dia_visual()
            input("\nPressione Enter para continuar...")

        elif opcao == "2":
            cadastrar_novo_exercicio()
            input("\nEnter...")

        elif opcao == "3":
            visualizar_historico()  # Chamada da função que estava faltando no menu
            input("\nPressione Enter para voltar...")

        elif opcao == "4":
            editar_catalogo_visual()  # Agora na sua própria opção
            input("\nPressione Enter para voltar...")

        elif opcao == "5":
            resumo_do_dia_visual()  # Caso queira ver o volume sem precisar treinar
            input("\nEnter...")

        elif opcao == "6":
            exportar_backup()
            input("\nEnter...")

        elif opcao == "7":
            menu_zerar_dados()
            input("\nEnter...")

        elif opcao == "0":
            rprint("[bold red]👋 Tchau, Natália![/bold red]")
            break