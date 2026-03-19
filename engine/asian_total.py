"""Calcolo Asian Total (Over/Under) per tutte le tipologie di linee."""

from data.models import AsianLine


def calculate_total_result(total_goals: int, line: float, side: str) -> float:
    """Calcola il risultato di una scommessa Asian Total.

    Gestisce linee intere, half-lines e quarter-lines con split automatico.

    Args:
        total_goals: Totale gol nella partita.
        line: Linea Over/Under (es. 2.5, 2.75, 3.0, 3.25).
        side: "OVER" o "UNDER".

    Returns:
        1.0  = vincita piena
        0.5  = mezza vincita (quarter-line)
        0.0  = push (rimborso)
        -0.5 = mezza perdita (quarter-line)
        -1.0 = perdita piena
    """
    if side not in ("OVER", "UNDER"):
        raise ValueError(f"Side deve essere 'OVER' o 'UNDER', ricevuto: {side}")

    # Gestione quarter-lines (2.75, 3.25, ecc.)
    remainder = line % 0.5
    if abs(remainder - 0.25) < 1e-9:
        # Quarter line: split su due linee adiacenti
        line_low = line - 0.25
        line_high = line + 0.25
        result_low = _total_single_line(total_goals, line_low, side)
        result_high = _total_single_line(total_goals, line_high, side)
        return (result_low + result_high) / 2.0

    return _total_single_line(total_goals, line, side)


def _total_single_line(total_goals: int, line: float, side: str) -> float:
    """Calcola il risultato per una singola linea Total (intera o half).

    Args:
        total_goals: Totale gol.
        line: Linea Over/Under.
        side: "OVER" o "UNDER".

    Returns:
        1.0 vincita, 0.0 push, -1.0 perdita.
    """
    if side == "OVER":
        if total_goals > line:
            return 1.0
        elif abs(total_goals - line) < 1e-9:
            return 0.0
        else:
            return -1.0
    else:  # UNDER
        if total_goals < line:
            return 1.0
        elif abs(total_goals - line) < 1e-9:
            return 0.0
        else:
            return -1.0


def expected_value_total(
    prob_over: float, prob_push: float, prob_under: float, odds: float
) -> float:
    """Calcola l'Expected Value di una scommessa Asian Total.

    Formula: EV = (prob_win * (odds-1)) + (prob_push * 0) - (prob_lose * 1)

    # NOTE: utilizzata dai test e disponibile per uso esterno.

    Args:
        prob_over: Probabilità Over.
        prob_push: Probabilità push (rimborso).
        prob_under: Probabilità Under.
        odds: Quota decimale.

    Returns:
        Expected Value (positivo = valore favorevole al scommettitore).
    """
    return (prob_over * (odds - 1.0)) + (prob_push * 0.0) - (prob_under * 1.0)


def analyze_total_line(line: AsianLine) -> dict:
    """Analizza la linea Asian Total confrontando apertura e chiusura.

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        Dizionario con analisi del movimento della linea Total.
    """
    total_moved = abs(line.total_close - line.total_open) > 1e-9
    over_odds_change = line.odds_over_close - line.odds_over_open
    under_odds_change = line.odds_under_close - line.odds_under_open

    over_odds_pct = over_odds_change / line.odds_over_open if line.odds_over_open else 0
    under_odds_pct = under_odds_change / line.odds_under_open if line.odds_under_open else 0

    # Direzione movimento linea Total
    if abs(line.total_close - line.total_open) < 1e-9:
        total_direction = "none"
    elif line.total_close > line.total_open:
        total_direction = "over"    # Linea si alza = più gol attesi
    else:
        total_direction = "under"   # Linea si abbassa = meno gol attesi

    return {
        "total_open": line.total_open,
        "total_close": line.total_close,
        "total_moved": total_moved,
        "total_direction": total_direction,
        "total_delta": line.total_close - line.total_open,
        "odds_over_open": line.odds_over_open,
        "odds_over_close": line.odds_over_close,
        "odds_under_open": line.odds_under_open,
        "odds_under_close": line.odds_under_close,
        "over_odds_change_pct": over_odds_pct,
        "under_odds_change_pct": under_odds_pct,
    }
