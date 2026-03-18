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
    n = 2  # numero di esiti

    # Stima del parametro z (proporzione insider)
    diff_sq_sum = ((p1_raw - 1.0 / sum_inv) ** 2 + (p2_raw - 1.0 / sum_inv) ** 2) * n
    discriminant = 1.0 - diff_sq_sum
    if discriminant < 0:
        discriminant = 0.0
    z = 1.0 - math.sqrt(discriminant)
    z = max(0.0, min(z, 0.5))  # Clamp z tra 0 e 0.5

    # Correzione Shin
    def shin_prob(p_raw: float) -> float:
        return (math.sqrt(z ** 2 + 4 * (1 - z) * (p_raw ** 2) / sum_inv) - z) / (2 * (1 - z))

    prob_home = shin_prob(p1_raw)
    prob_away = shin_prob(p2_raw)

    # Normalizzazione
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
