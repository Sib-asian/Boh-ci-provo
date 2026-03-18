"""Rilevamento del denaro sharp e del Reverse Line Movement."""

import config
from data.models import AsianLine
from engine.line_movement import is_steam_move, handicap_movement


def detect_sharp_side(line: AsianLine) -> str:
    """Rileva quale lato del mercato è supportato dal denaro sharp.

    Analizza il movimento delle linee e delle odds per identificare
    dove si trova il denaro professionale (sharp money).

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        "HOME", "AWAY", "OVER", "UNDER" o "NONE".
    """
    ah_move = handicap_movement(line.handicap_open, line.handicap_close)

    # Steam moves nelle odds AH
    steam_home = is_steam_move(line.odds_home_open, line.odds_home_close)
    steam_away = is_steam_move(line.odds_away_open, line.odds_away_close)
    steam_over = is_steam_move(line.odds_over_open, line.odds_over_close)
    steam_under = is_steam_move(line.odds_under_open, line.odds_under_close)

    # Reverse Line Movement (RLM):
    # Se la linea si muove verso HOME ma le odds HOME si accorciano molto
    # significa che i bookmaker reagiscono a scommesse sull'HOME (sharp)
    if ah_move["direction"] == "home":
        # Linea verso casa: ci aspettiamo odds home più corte
        if steam_home and line.odds_home_close < line.odds_home_open:
            return "HOME"
        # RLM: linea verso casa ma odds away si accorciano = sharp su AWAY
        if steam_away and line.odds_away_close < line.odds_away_open:
            return "AWAY"
    elif ah_move["direction"] == "away":
        # Linea verso trasferta: ci aspettiamo odds away più corte
        if steam_away and line.odds_away_close < line.odds_away_open:
            return "AWAY"
        # RLM: linea verso trasferta ma odds home si accorciano = sharp su HOME
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


def reverse_line_movement(public_side: str, line_moved_to: str) -> bool:
    """Verifica se si è verificato un Reverse Line Movement (RLM).

    Il RLM avviene quando la linea si muove nella direzione opposta
    rispetto all'azione del pubblico, indicando forte denaro sharp.

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

    Args:
        line: Oggetto AsianLine con i dati della partita.

    Returns:
        Score di confidenza tra 0.0 (nessun segnale) e 1.0 (massima confidenza).
    """
    score = 0.0
    indicators = 0

    # Indicatore 1: Movimento significativo della linea AH
    ah_move = handicap_movement(line.handicap_open, line.handicap_close)
    if ah_move["significant"]:
        score += 0.30
        indicators += 1

    # Indicatore 2: Steam move nelle odds AH
    steam_home = is_steam_move(line.odds_home_open, line.odds_home_close)
    steam_away = is_steam_move(line.odds_away_open, line.odds_away_close)
    if steam_home or steam_away:
        score += 0.25
        indicators += 1

    # Indicatore 3: Steam move nelle odds Total
    steam_over = is_steam_move(line.odds_over_open, line.odds_over_close)
    steam_under = is_steam_move(line.odds_under_open, line.odds_under_close)
    if steam_over or steam_under:
        score += 0.20
        indicators += 1

    # Indicatore 4: Movimento della linea Total
    if abs(line.total_close - line.total_open) >= 0.25:
        score += 0.15
        indicators += 1

    # Indicatore 5: Convergenza segnali (bonus per coerenza)
    sharp_side = detect_sharp_side(line)
    if sharp_side != "NONE" and indicators >= 2:
        score += 0.10

    return min(score, 1.0)
