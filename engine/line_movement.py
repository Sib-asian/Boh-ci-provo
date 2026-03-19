"""Analisi del movimento delle linee e rilevamento steam move."""

import config


def handicap_movement(open_h: float, close_h: float) -> dict:
    """Analizza il movimento della linea Asian Handicap.

    Args:
        open_h: Handicap di apertura.
        close_h: Handicap di chiusura.

    Returns:
        Dizionario con direzione, entità e significatività del movimento.
    """
    delta = close_h - open_h
    entita = abs(delta)

    if entita < 1e-9:
        direction = "none"
    elif delta < 0:
        direction = "home"  # Linea favorisce più la squadra di casa
    else:
        direction = "away"  # Linea favorisce più la squadra ospite

    # Significatività: movimento >= 0.25 è significativo
    significant = entita >= 0.25

    return {
        "direction": direction,
        "delta": delta,
        "entita": entita,
        "significant": significant,
    }


def odds_movement(open_odds: float, close_odds: float) -> dict:
    """Analizza il movimento delle odds tra apertura e chiusura.

    # NOTE: utility pubblica disponibile per uso esterno e analisi avanzata.

    Args:
        open_odds: Quota di apertura.
        close_odds: Quota di chiusura.

    Returns:
        Dizionario con variazione percentuale e segnale steam move.
    """
    change = close_odds - open_odds
    pct_change = change / open_odds if open_odds else 0.0
    steam = is_steam_move(open_odds, close_odds)

    direction = "shorter" if change < 0 else ("longer" if change > 0 else "stable")

    return {
        "open": open_odds,
        "close": close_odds,
        "change": change,
        "pct_change": pct_change,
        "direction": direction,
        "steam_move": steam,
    }


def is_steam_move(
    open_odds: float, close_odds: float, threshold: float = config.STEAM_MOVE_THRESHOLD
) -> bool:
    """Rileva un possibile steam move basato sulla variazione delle odds.

    Uno steam move si verifica quando le odds si muovono rapidamente e significativamente,
    indicando scommesse massicce di giocatori professionisti (sharp money).

    Args:
        open_odds: Quota di apertura.
        close_odds: Quota di chiusura.
        threshold: Soglia percentuale per considerare uno steam move (default 8%).

    Returns:
        True se è stato rilevato uno steam move.
    """
    if open_odds <= 0:
        return False
    pct_change = abs(close_odds - open_odds) / open_odds
    return pct_change >= threshold


def line_movement_score(ah_analysis: dict, total_analysis: dict) -> float:
    """Calcola uno score composito del movimento delle linee (0-100).

    Combina il movimento dell'AH e del Total in un punteggio normalizzato.

    Args:
        ah_analysis: Dizionario restituito da analyze_ah_line().
        total_analysis: Dizionario restituito da analyze_total_line().

    Returns:
        Score composito 0-100 dove 100 indica massimo movimento.
    """
    score = 0.0

    # Contributo movimento handicap (max 40 punti)
    ah_delta = abs(ah_analysis.get("handicap_delta", 0))
    if ah_delta >= 0.5:
        score += 40.0
    elif ah_delta >= 0.25:
        score += 25.0
    elif ah_delta > 0:
        score += 10.0

    # Contributo variazione odds AH (max 30 punti)
    home_pct = abs(ah_analysis.get("home_odds_change_pct", 0))
    away_pct = abs(ah_analysis.get("away_odds_change_pct", 0))
    max_ah_pct = max(home_pct, away_pct)
    if max_ah_pct >= config.STEAM_MOVE_THRESHOLD:
        score += 30.0
    elif max_ah_pct >= 0.04:
        score += 15.0
    elif max_ah_pct > 0:
        score += 5.0

    # Contributo movimento linea Total (max 15 punti)
    total_delta = abs(total_analysis.get("total_delta", 0))
    if total_delta >= 0.5:
        score += 15.0
    elif total_delta >= 0.25:
        score += 8.0
    elif total_delta > 0:
        score += 3.0

    # Contributo variazione odds Total (max 15 punti)
    over_pct = abs(total_analysis.get("over_odds_change_pct", 0))
    under_pct = abs(total_analysis.get("under_odds_change_pct", 0))
    max_total_pct = max(over_pct, under_pct)
    if max_total_pct >= config.STEAM_MOVE_THRESHOLD:
        score += 15.0
    elif max_total_pct >= 0.04:
        score += 8.0
    elif max_total_pct > 0:
        score += 3.0

    return min(score, 100.0)
