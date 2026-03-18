"""Motore di calcolo delle probabilità fair con rimozione del margine bookmaker."""

import math
from scipy.optimize import brentq


def implied_probability(odds: float) -> float:
    """Calcola la probabilità implicita da una quota decimale.

    Args:
        odds: Quota decimale (es. 1.90).

    Returns:
        Probabilità implicita (0.0 - 1.0).
    """
    if odds <= 0:
        raise ValueError(f"La quota deve essere positiva, ricevuto: {odds}")
    return 1.0 / odds


def fair_odds(prob: float) -> float:
    """Calcola la quota fair da una probabilità.

    Args:
        prob: Probabilità (0.0 - 1.0).

    Returns:
        Quota decimale fair.
    """
    if prob <= 0 or prob >= 1:
        raise ValueError(f"La probabilità deve essere tra 0 e 1, ricevuta: {prob}")
    return 1.0 / prob


def remove_margin_power(odds_home: float, odds_away: float) -> tuple[float, float]:
    """Rimuove il margine bookmaker con il Power Method.

    Trova il parametro k tale che sum(odds_i^(-k)) = 1, poi p_i = odds_i^(-k).
    Questo è il metodo più preciso per mercati a due esiti.

    Args:
        odds_home: Quota casa.
        odds_away: Quota trasferta.

    Returns:
        Tuple (prob_home, prob_away) con probabilità fair normalizzate a 1.
    """
    def equation(k: float) -> float:
        return odds_home ** (-k) + odds_away ** (-k) - 1.0

    # Trova k nell'intervallo [0.5, 3.0]
    try:
        k = brentq(equation, 0.5, 3.0)
    except ValueError:
        # Fallback: usa metodo additivo
        return remove_margin_additive(odds_home, odds_away)

    prob_home = odds_home ** (-k)
    prob_away = odds_away ** (-k)
    return prob_home, prob_away


def remove_margin_shin(odds_home: float, odds_away: float) -> tuple[float, float]:
    """Rimuove il margine bookmaker con il Metodo di Shin.

    Il metodo Shin tiene conto dell'asimmetria informativa tra bookmaker e scommettitori.
    Particolarmente efficace per mercati con forte presenza di insider trading.

    Args:
        odds_home: Quota casa.
        odds_away: Quota trasferta.

    Returns:
        Tuple (prob_home, prob_away) con probabilità fair corrette con Shin.
    """
    p1_raw = 1.0 / odds_home
    p2_raw = 1.0 / odds_away
    sum_inv = p1_raw + p2_raw

    # Usa brentq per trovare z in modo preciso
    def shin_equation(z: float) -> float:
        if abs(1 - z) < 1e-12:
            return 1e12  # valore molto grande per indicare che z=1 non è valido
        p1_shin = (math.sqrt(z**2 + 4*(1-z)*(p1_raw**2)/sum_inv) - z) / (2*(1-z))
        p2_shin = (math.sqrt(z**2 + 4*(1-z)*(p2_raw**2)/sum_inv) - z) / (2*(1-z))
        return p1_shin + p2_shin - 1.0

    try:
        z = brentq(shin_equation, 0.0, 0.5 - 1e-9)
    except ValueError:
        z = 0.0

    def shin_prob(p_raw: float) -> float:
        if abs(1 - z) < 1e-12:
            return p_raw / sum_inv
        return (math.sqrt(z**2 + 4*(1-z)*(p_raw**2)/sum_inv) - z) / (2*(1-z))

    prob_home = shin_prob(p1_raw)
    prob_away = shin_prob(p2_raw)
    total = prob_home + prob_away
    return prob_home / total, prob_away / total


def remove_margin_additive(odds_home: float, odds_away: float) -> tuple[float, float]:
    """Rimuove il margine bookmaker con il Metodo Additivo (Normalizzazione).

    Divide ogni probabilità implicita per la somma totale delle probabilità implicite.
    Metodo semplice e veloce, meno preciso del Power Method.

    Args:
        odds_home: Quota casa.
        odds_away: Quota trasferta.

    Returns:
        Tuple (prob_home, prob_away) con probabilità fair normalizzate a 1.
    """
    p_home = 1.0 / odds_home
    p_away = 1.0 / odds_away
    total = p_home + p_away
    return p_home / total, p_away / total
