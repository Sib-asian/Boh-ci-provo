"""Interfaccia CLI con Rich per il sistema di pronostici calcistici."""

import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box

from data.loader import load_matches
from data.models import Match, Prediction
from engine.predictor import generate_predictions
from ui.formatter import (
    format_match_header,
    format_lines_table,
    format_prediction_text,
)
import config

console = Console()

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "matches_sample.json",
)


def show_banner() -> None:
    """Mostra il banner di benvenuto del sistema."""
    banner = Text()
    banner.append("⚽  SISTEMA PRONOSTICI CALCISTICI  ⚽\n", style="bold yellow")
    banner.append("Asian Handicap & Asian Total — Exchange Edition\n", style="cyan")
    banner.append("Basato su: Power Method | Shin Method | Sharp Money | Steam Move", style="dim")
    console.print(Panel(banner, box=box.DOUBLE, border_style="yellow", padding=(1, 4)))


def show_main_menu() -> str:
    """Mostra il menu principale e ritorna la scelta dell'utente.

    Returns:
        Stringa con la scelta dell'utente.
    """
    console.print("\n[bold cyan]MENU PRINCIPALE[/bold cyan]")
    console.print("  [bold white]1[/bold white] — Analizza tutte le partite")
    console.print("  [bold white]2[/bold white] — Solo segnali SHARP")
    console.print("  [bold white]3[/bold white] — Solo mercato Asian Handicap")
    console.print("  [bold white]4[/bold white] — Solo mercato Asian Total")
    console.print("  [bold white]5[/bold white] — Filtra per edge minimo personalizzato")
    console.print("  [bold white]6[/bold white] — Cambia file partite")
    console.print("  [bold white]0[/bold white] — Esci\n")

    choice = Prompt.ask("[bold yellow]Scelta", choices=["0", "1", "2", "3", "4", "5", "6"])
    return choice


def display_match_predictions(
    match: Match,
    predictions: list[Prediction],
    min_edge: float = config.MIN_EDGE_THRESHOLD,
    only_sharp: bool = False,
    only_ah: bool = False,
    only_total: bool = False,
) -> None:
    """Mostra le linee e i pronostici di una singola partita.

    Args:
        match: Oggetto Match.
        predictions: Lista di pronostici generati.
        min_edge: Filtro edge minimo.
        only_sharp: Se True, mostra solo pronostici con segnale sharp.
        only_ah: Se True, mostra solo pronostici AH.
        only_total: Se True, mostra solo pronostici Total.
    """
    header = format_match_header(match)
    console.print(Rule(f"[bold white]{header}[/bold white]", style="yellow"))

    # Tabella linee
    lines_table = format_lines_table(match)
    console.print(lines_table)

    # Filtra pronostici
    filtered = [p for p in predictions if p.edge >= min_edge]
    if only_sharp:
        from engine.sharp_money import detect_sharp_side, sharp_confidence_score
        sharp_side = detect_sharp_side(match.asian_line)
        filtered = [p for p in filtered if p.side == sharp_side]
    if only_ah:
        filtered = [p for p in filtered if p.market.startswith("AH")]
    if only_total:
        filtered = [p for p in filtered if p.market.startswith("TOTAL")]

    if not filtered:
        console.print("  [dim]Nessun pronostico con valore sufficiente per questa partita.[/dim]\n")
        return

    console.print(f"  [bold green]✓ {len(filtered)} pronostico/i trovato/i[/bold green]\n")
    for pred in filtered:
        pred_text = format_prediction_text(pred)
        console.print(Panel(pred_text, border_style="green" if pred.recommendation == "PUNTA" else "red",
                            box=box.ROUNDED, padding=(0, 2)))

    console.print()


def run_analysis(
    filepath: str,
    min_edge: float = config.MIN_EDGE_THRESHOLD,
    only_sharp: bool = False,
    only_ah: bool = False,
    only_total: bool = False,
) -> None:
    """Esegue l'analisi completa delle partite e mostra i pronostici.

    Args:
        filepath: Percorso al file JSON delle partite.
        min_edge: Filtro edge minimo.
        only_sharp: Solo segnali sharp.
        only_ah: Solo mercato AH.
        only_total: Solo mercato Total.
    """
    try:
        matches = load_matches(filepath)
    except FileNotFoundError:
        console.print(f"[bold red]Errore:[/bold red] File non trovato: {filepath}")
        return
    except Exception as e:
        console.print(f"[bold red]Errore nel caricamento:[/bold red] {e}")
        return

    console.print(f"\n[bold cyan]Analisi di {len(matches)} partite...[/bold cyan]\n")

    total_predictions = 0
    for match in matches:
        predictions = generate_predictions(match)
        total_predictions += len(predictions)
        display_match_predictions(
            match,
            predictions,
            min_edge=min_edge,
            only_sharp=only_sharp,
            only_ah=only_ah,
            only_total=only_total,
        )

    console.print(Rule(style="yellow"))
    console.print(
        f"[bold yellow]Totale pronostici generati:[/bold yellow] [bold white]{total_predictions}[/bold white]\n"
    )


def run_cli() -> None:
    """Esegue il loop principale della CLI."""
    show_banner()
    filepath = DEFAULT_DATA_PATH

    while True:
        choice = show_main_menu()

        if choice == "0":
            console.print("\n[bold yellow]Arrivederci! Buona fortuna! ⚽[/bold yellow]\n")
            break

        elif choice == "1":
            run_analysis(filepath)

        elif choice == "2":
            run_analysis(filepath, only_sharp=True)

        elif choice == "3":
            run_analysis(filepath, only_ah=True)

        elif choice == "4":
            run_analysis(filepath, only_total=True)

        elif choice == "5":
            min_edge = FloatPrompt.ask(
                "[bold yellow]Edge minimo (%)[/bold yellow]",
                default=2.0,
            )
            run_analysis(filepath, min_edge=min_edge / 100.0)

        elif choice == "6":
            new_path = Prompt.ask(
                "[bold yellow]Percorso file JSON[/bold yellow]",
                default=DEFAULT_DATA_PATH,
            )
            if os.path.exists(new_path):
                filepath = new_path
                console.print(f"[green]File impostato: {filepath}[/green]")
            else:
                console.print(f"[red]File non trovato: {new_path}[/red]")
