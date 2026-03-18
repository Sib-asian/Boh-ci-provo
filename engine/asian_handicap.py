"""Calcolo Asian Handicap per tutte le tipologie di linee."""

from data.models import AsianLine


def calculate_ah_result(
    home_goals: int, away_goals: int, handicap: float, side: str
) -> float:
    """Calcola il risultato di una scommessa Asian Handicap.

    Gestisce linee intere, half-lines e quarter-lines con split su due linee adiacenti.

    Args:
        home_goals: Gol segnati dalla squadra di casa.
        away_goals: Gol segnati dalla squadra ospite.
        handicap: Handicap applicato alla squadra di casa (negativo = favorita).
        side: "HOME" o "AWAY".

    Returns:
        1.0  = vincita piena
        0.5  = mezza vincita (quarter-line)
        0.0  = push (rimborso)
        -0.5 = mezza perdita (quarter-line)
        -1.0 = perdita piena
    """
    if side not in ("HOME", "AWAY"):
        raise ValueError(f"Side deve essere 'HOME' o 'AWAY', ricevuto: {side}")

    # Per il lato AWAY, invertiamo il punto di vista
    if side == "AWAY":
        return calculate_ah_result(away_goals, home_goals, -handicap, "HOME")

    # Gestione quarter-lines (±0.25, ±0.75, ±1.25, ecc.)
    remainder = abs(handicap) % 0.5
    if abs(remainder - 0.25) < 1e-9:
        # Quarter line: split su due linee adiacenti
        if handicap > 0:
            line_low = handicap - 0.25
            line_high = handicap + 0.25
        else:
            line_low = handicap - 0.25
            line_high = handicap + 0.25

        result_low = _ah_single_line(home_goals, away_goals, line_low)
        result_high = _ah_single_line(home_goals, away_goals, line_high)
        return (result_low + result_high) / 2.0

    return _ah_single_line(home_goals, away_goals, handicap)


def _ah_single_line(home_goals: int, away_goals: int, handicap: float) -> float:
    """Calcola il risultato per una singola linea AH (intera o half).

    Args:
        home_goals: Gol casa.
        away_goals: Gol ospite.
        handicap: Linea di handicap (es. -1.0, -0.5, 0.0, +0.5).

    Returns:
        1.0 vincita, 0.0 push, -1.0 perdita.
    """
    adjusted = home_goals + handicap - away_goals

    if adjusted > 0:
        return 1.0
    elif abs(adjusted) < 1e-9:
        return 0.0
    else:
        return -1.0


def expected_value_ah(
    prob_win: float, prob_push: float, prob_lose: float, odds: float
) -> float:
    """Calcola l'Expected Value di una scommessa Asian Handicap.

    Formula: EV = (prob_win * (odds-1)) + (prob_push * 0) - (prob_lose * 1)

    Args:
        prob_win: Probabilità di vincita piena.
        prob_push: Probabilità di push (rimborso).
        prob_lose: Probabilità di perdita.
        odds: Quota decimale.

    Returns:
        Expected Value (positivo = valore favorevole al scommettitore).
    """
    return (prob_win * (odds - 1.0)) + (prob_push * 0.0) - (prob_lose * 1.0)


def analyze_ah_line(line: AsianLine) -> dict:
    """Analizza la linea Asian Handicap confrontando apertura e chiusura.

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        Dizionario con analisi del movimento della linea AH.
    """
    handicap_moved = abs(line.handicap_close - line.handicap_open) > 1e-9
    home_odds_change = line.odds_home_close - line.odds_home_open
    away_odds_change = line.odds_away_close - line.odds_away_open

    # Variazione percentuale delle odds
    home_odds_pct = home_odds_change / line.odds_home_open if line.odds_home_open else 0
    away_odds_pct = away_odds_change / line.odds_away_open if line.odds_away_open else 0

    # Determinazione direzione movimento handicap
    if abs(line.handicap_close - line.handicap_open) < 1e-9:
        handicap_direction = "none"
    elif line.handicap_close < line.handicap_open:
        handicap_direction = "home"   # Linea si muove verso casa (più favorita)
    else:
        handicap_direction = "away"   # Linea si muove verso trasferta

    return {
        "handicap_open": line.handicap_open,
        "handicap_close": line.handicap_close,
        "handicap_moved": handicap_moved,
        "handicap_direction": handicap_direction,
        "handicap_delta": line.handicap_close - line.handicap_open,
        "odds_home_open": line.odds_home_open,
        "odds_home_close": line.odds_home_close,
        "odds_away_open": line.odds_away_open,
        "odds_away_close": line.odds_away_close,
        "home_odds_change_pct": home_odds_pct,
        "away_odds_change_pct": away_odds_pct,
    }
