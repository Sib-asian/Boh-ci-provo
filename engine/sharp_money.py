"""Rilevamento del denaro sharp e del Reverse Line Movement."""

import config
from data.models import AsianLine
from engine.line_movement import is_steam_move, handicap_movement


def _compute_sharp_signals(line: AsianLine) -> dict:
    """Helper interno condiviso: calcola una volta sola tutti i segnali sharp.

    Evita il doppio calcolo quando `detect_sharp_side()` e
    `sharp_confidence_score()` vengono chiamati in sequenza.

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        Dizionario con movimento AH e steam moves pre-calcolati.
    """
    return {
        "ah_move": handicap_movement(line.handicap_open, line.handicap_close),
        "steam_home": is_steam_move(line.odds_home_open, line.odds_home_close),
        "steam_away": is_steam_move(line.odds_away_open, line.odds_away_close),
        "steam_over": is_steam_move(line.odds_over_open, line.odds_over_close),
        "steam_under": is_steam_move(line.odds_under_open, line.odds_under_close),
    }


def _detect_sharp_side_from_signals(signals: dict, line: AsianLine) -> str:
    """Versione interna di detect_sharp_side che usa segnali pre-calcolati.

    Args:
        signals: Dizionario restituito da _compute_sharp_signals().
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        "HOME", "AWAY", "OVER", "UNDER" o "NONE".
    """
    ah_move = signals["ah_move"]
    steam_home = signals["steam_home"]
    steam_away = signals["steam_away"]
    steam_over = signals["steam_over"]
    steam_under = signals["steam_under"]

    if ah_move["direction"] == "home":
        # Azione normale: sharp ha puntato HOME → linea si muove verso HOME + odds home si accorciano
        if steam_home and line.odds_home_close < line.odds_home_open:
            return "HOME"
        # RLM: linea verso HOME ma odds AWAY si accorciano → sharp su AWAY (contrario alla linea)
        if steam_away and line.odds_away_close < line.odds_away_open:
            return "AWAY"
    elif ah_move["direction"] == "away":
        # Azione normale: sharp ha puntato AWAY → linea si muove verso AWAY + odds away si accorciano
        if steam_away and line.odds_away_close < line.odds_away_open:
            return "AWAY"
        # RLM: linea verso AWAY ma odds HOME si accorciano → sharp su HOME (contrario alla linea)
        if steam_home and line.odds_home_close < line.odds_home_open:
            return "HOME"

    # Analisi mercato Total
    total_moved = abs(line.total_close - line.total_open) > 1e-9
    if total_moved:
        if line.total_close > line.total_open:
            # Linea alzata = public scommette OVER, ma se UNDER si accorcia = sharp su UNDER
            if steam_under and line.odds_under_close < line.odds_under_open:
                return "UNDER"
            return "OVER"
        else:
            if steam_over and line.odds_over_close < line.odds_over_open:
                return "OVER"
            return "UNDER"

    # Verifica steam moves isolati nel Total
    if steam_over and line.odds_over_close < line.odds_over_open:
        return "OVER"
    if steam_under and line.odds_under_close < line.odds_under_open:
        return "UNDER"

    # Verifica steam moves isolati nell'AH
    if steam_home and line.odds_home_close < line.odds_home_open:
        return "HOME"
    if steam_away and line.odds_away_close < line.odds_away_open:
        return "AWAY"

    return "NONE"


def detect_sharp_side(line: AsianLine) -> str:
    """Rileva quale lato del mercato è supportato dal denaro sharp.

    Analizza il movimento delle linee e delle odds per identificare
    dove si trova il denaro professionale (sharp money).

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        "HOME", "AWAY", "OVER", "UNDER" o "NONE".
    """
    return _detect_sharp_side_from_signals(_compute_sharp_signals(line), line)


def reverse_line_movement(public_side: str, line_moved_to: str) -> bool:
    """Verifica se si è verificato un Reverse Line Movement (RLM).

    Il RLM avviene quando la linea si muove nella direzione opposta
    rispetto all'azione del pubblico, indicando forte denaro sharp.

    # NOTE: utility pubblica disponibile per uso esterno e analisi avanzata.

    Args:
        public_side: Lato preferito dal pubblico ("HOME"/"AWAY"/"OVER"/"UNDER").
        line_moved_to: Direzione verso cui si è mossa la linea.

    Returns:
        True se la linea si muove contro il pubblico (= sharp action).
    """
    opposites = {
        "HOME": "AWAY",
        "AWAY": "HOME",
        "OVER": "UNDER",
        "UNDER": "OVER",
    }
    return opposites.get(public_side, "") == line_moved_to


def sharp_confidence_score(line: AsianLine) -> float:
    """Calcola uno score di confidenza per i segnali sharp (0.0 - 1.0).

    Combina più indicatori di denaro professionale in un unico punteggio.
    I segnali intermedi vengono calcolati una sola volta tramite
    _compute_sharp_signals() per evitare calcoli ridondanti.

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        Score di confidenza tra 0.0 (nessun segnale) e 1.0 (massima confidenza).
    """
    # Calcola tutti i segnali una sola volta (evita doppio calcolo con detect_sharp_side)
    signals = _compute_sharp_signals(line)
    ah_move = signals["ah_move"]
    steam_home = signals["steam_home"]
    steam_away = signals["steam_away"]
    steam_over = signals["steam_over"]
    steam_under = signals["steam_under"]

    score = 0.0
    indicators = 0

    # Indicatore 1: Movimento significativo della linea AH
    if ah_move["significant"]:
        entita = ah_move["entita"]
        if entita >= 0.75:
            score += 0.45  # movimento molto forte
        elif entita >= 0.50:
            score += 0.38  # movimento forte
        else:
            score += 0.30  # movimento standard (≥0.25)
        indicators += 1

    # Indicatore 2: Steam move nelle odds AH
    if steam_home or steam_away:
        score += 0.25
        indicators += 1

    # Indicatore 3: Steam move nelle odds Total
    if steam_over or steam_under:
        score += 0.20
        indicators += 1

    # Indicatore 4: Movimento della linea Total
    total_delta = abs(line.total_close - line.total_open)
    if total_delta >= 0.50:
        score += 0.20  # movimento molto forte
        indicators += 1
    elif total_delta >= 0.25:
        score += 0.15  # movimento standard
        indicators += 1

    # Indicatore 5: Convergenza segnali (bonus per coerenza)
    # Riusa i segnali già calcolati per evitare il doppio calcolo
    sharp_side = _detect_sharp_side_from_signals(signals, line)
    if sharp_side != "NONE" and indicators >= 2:
        score += 0.10

    return min(score, 1.0)
