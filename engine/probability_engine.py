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


def remove_margin_iterative(
    odds_home: float, odds_away: float, tol: float = 1e-9
) -> tuple[float, float]:
    """Rimuove il margine con metodo Newton-Raphson iterativo.

    Più robusto del Power Method per odds molto asimmetriche.

    Args:
        odds_home: Quota casa.
        odds_away: Quota trasferta.
        tol: Tolleranza di convergenza.

    Returns:
        Tuple (prob_home, prob_away) con probabilità fair.
    """
    # Punto di partenza: metodo additivo
    p1 = 1.0 / odds_home
    p2 = 1.0 / odds_away

    # k iniziale: approssimazione additiva
    k = (
        math.log(2) / (math.log(odds_home) * math.log(odds_away))
        if (odds_home > 1 and odds_away > 1)
        else 1.0
    )

    # Newton-Raphson: minimizza |odds_home^(-k) + odds_away^(-k) - 1|
    log_h = math.log(odds_home)
    log_a = math.log(odds_away)

    for _ in range(100):
        fk = odds_home ** (-k) + odds_away ** (-k) - 1.0
        if abs(fk) < tol:
            break
        # Derivata: df/dk = -log(h)*h^(-k) - log(a)*a^(-k)
        dfk = -log_h * odds_home ** (-k) - log_a * odds_away ** (-k)
        if abs(dfk) < 1e-15:
            break
        k = k - fk / dfk
        k = max(0.1, min(k, 5.0))  # clamp per stabilità

    prob_home = odds_home ** (-k)
    prob_away = odds_away ** (-k)

    # Normalizzazione di sicurezza
    total = prob_home + prob_away
    if total <= 0:
        return remove_margin_additive(odds_home, odds_away)
    return prob_home / total, prob_away / total


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
        # Fallback: usa metodo iterativo (più preciso dell'additivo)
        return remove_margin_iterative(odds_home, odds_away)

    prob_home = odds_home ** (-k)
    prob_away = odds_away ** (-k)
    return prob_home, prob_away


def _lambda_from_total_odds(
    odds_over: float, odds_under: float, total_line: float
) -> float:
    """Stima il lambda Poisson (gol attesi) dalle odds Over/Under.

    Usa il metodo di bisezione: trova lambda tale che P(gol > total_line) = prob_over_fair.

    Args:
        odds_over: Quota Over.
        odds_under: Quota Under.
        total_line: Linea Total (es. 2.5, 2.75, 3.0).

    Returns:
        Lambda stimato (gol attesi nella partita).
    """
    # Probabilità fair Over usando metodo additivo (semplice e robusto)
    p_over_raw = 1.0 / odds_over
    p_under_raw = 1.0 / odds_under
    total_raw = p_over_raw + p_under_raw
    prob_over_fair = p_over_raw / total_raw

    # Bisezione per trovare lambda
    lo, hi = 0.1, 15.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        # P(gol > total_line) con Poisson(lambda=mid)
        # Per linee intere e half, calcola P(X > floor(total_line))
        floor_line = int(total_line)
        p_over_poisson = 1.0 - sum(
            (mid ** k) * math.exp(-mid) / math.factorial(k)
            for k in range(floor_line + 1)
        )
        if p_over_poisson < prob_over_fair:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def poisson_total_probs(
    odds_over: float,
    odds_under: float,
    total_line: float,
) -> tuple[float, float]:
    """Stima prob_over e prob_under usando la distribuzione di Poisson.

    Più preciso del semplice no-vig per il mercato Total, perché modella
    esplicitamente la distribuzione discreta dei gol.

    Args:
        odds_over: Quota Over di mercato.
        odds_under: Quota Under di mercato.
        total_line: Linea Total (es. 2.5, 2.75, 3.0, 3.25).

    Returns:
        Tuple (prob_over, prob_under) fair stimate con Poisson.
        Le probabilità sommano a 1 (escludendo push per linee intere).
    """
    try:
        lam = _lambda_from_total_odds(odds_over, odds_under, total_line)
    except (ValueError, OverflowError):
        # Fallback al metodo additivo
        return remove_margin_additive(odds_over, odds_under)

    floor_line = int(total_line)

    # P(X > floor_line) con Poisson(lambda)
    prob_over = 1.0 - sum(
        (lam ** k) * math.exp(-lam) / math.factorial(k)
        for k in range(floor_line + 1)
    )

    # Gestione quarter-lines: media tra floor e ceil
    remainder = total_line % 0.5
    if abs(remainder - 0.25) < 1e-9:
        # Quarter line: P_over è media tra P(X > floor) e P(X > floor+1)
        p_over_high = 1.0 - sum(
            (lam ** k) * math.exp(-lam) / math.factorial(k)
            for k in range(floor_line + 2)
        )
        prob_over = (prob_over + p_over_high) / 2.0

    prob_under = 1.0 - prob_over

    # Clamp per sicurezza
    prob_over = max(0.01, min(0.99, prob_over))
    prob_under = max(0.01, min(0.99, prob_under))

    # Normalizzazione
    total = prob_over + prob_under
    return prob_over / total, prob_under / total
