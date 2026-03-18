"""Formattazione output per la CLI con Rich."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from data.models import Match, Prediction


def format_match_header(match: Match) -> str:
    """Formatta l'intestazione di una partita.

    Args:
        match: Oggetto Match.

    Returns:
        Stringa formattata con nome partita, lega e data.
    """
    return f"⚽ {match.home_team} vs {match.away_team} | {match.league} | {match.date}"


def format_lines_table(match: Match) -> Table:
    """Crea una tabella Rich con le linee di apertura e chiusura.

    Args:
        match: Oggetto Match con le linee asiatiche.

    Returns:
        Oggetto Table di Rich con le linee formattate.
    """
    line = match.asian_line
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Mercato", style="white", min_width=12)
    table.add_column("Apertura", style="yellow", min_width=20)
    table.add_column("Chiusura", style="green", min_width=20)
    table.add_column("Movimento", style="magenta", min_width=10)

    # AH Home
    ah_home_moved = abs(line.handicap_close - line.handicap_open) > 1e-9
    ah_move_str = f"{'← ' if ah_home_moved else ''}{line.handicap_close:+.2f}" if ah_home_moved else "—"

    table.add_row(
        "AH Casa",
        f"{line.handicap_open:+.2f} @ {line.odds_home_open:.2f}",
        f"{line.handicap_close:+.2f} @ {line.odds_home_close:.2f}",
        f"[yellow]{ah_move_str}[/yellow]" if ah_home_moved else "—",
    )

    # AH Away
    table.add_row(
        "AH Trasferta",
        f"{-line.handicap_open:+.2f} @ {line.odds_away_open:.2f}",
        f"{-line.handicap_close:+.2f} @ {line.odds_away_close:.2f}",
        "—",
    )

    # Total
    total_moved = abs(line.total_close - line.total_open) > 1e-9
    total_move_str = f"← {line.total_close:.2f}" if total_moved else "—"

    table.add_row(
        "Total Over",
        f"{line.total_open:.2f} @ {line.odds_over_open:.2f}",
        f"{line.total_close:.2f} @ {line.odds_over_close:.2f}",
        f"[yellow]{total_move_str}[/yellow]" if total_moved else "—",
    )
    table.add_row(
        "Total Under",
        f"{line.total_open:.2f} @ {line.odds_under_open:.2f}",
        f"{line.total_close:.2f} @ {line.odds_under_close:.2f}",
        "—",
    )

    return table


def format_prediction_text(pred: Prediction) -> Text:
    """Formatta un singolo pronostico con colori Rich.

    Args:
        pred: Oggetto Prediction.

    Returns:
        Oggetto Text di Rich formattato.
    """
    t = Text()

    # Icona e raccomandazione
    if pred.recommendation == "PUNTA":
        t.append("🟢 PUNTA  ", style="bold green")
    else:
        t.append("🔴 BANCA  ", style="bold red")

    # Mercato e linea
    market_label = _market_label(pred)
    t.append(f"{market_label} @ {pred.odds:.2f}\n", style="bold white")

    # Statistiche
    t.append(f"   Edge: ", style="dim")
    edge_color = "green" if pred.edge > 0.05 else ("yellow" if pred.edge > 0.02 else "white")
    t.append(f"{pred.edge * 100:+.1f}%", style=f"bold {edge_color}")
    t.append(" | Confidenza: ", style="dim")
    t.append(f"{pred.confidence:.0f}%", style="bold cyan")
    t.append(" | Kelly: ", style="dim")
    t.append(f"{pred.kelly * 100:.1f}%\n", style="bold magenta")

    # Reasoning
    t.append(f"   📌 {pred.reasoning}", style="italic dim")

    return t


def _market_label(pred: Prediction) -> str:
    """Restituisce l'etichetta leggibile del mercato.

    Args:
        pred: Oggetto Prediction.

    Returns:
        Stringa con etichetta del mercato.
    """
    if pred.market == "AH_HOME":
        return f"AH {pred.match.home_team} {pred.handicap_or_total:+.2f}"
    elif pred.market == "AH_AWAY":
        return f"AH {pred.match.away_team} {pred.handicap_or_total:+.2f}"
    elif pred.market == "TOTAL_OVER":
        return f"Over {pred.handicap_or_total:.2f}"
    elif pred.market == "TOTAL_UNDER":
        return f"Under {pred.handicap_or_total:.2f}"
    return pred.market
