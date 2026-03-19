"""Calcolo del valore atteso, Kelly Criterion ed edge ponderato."""

import warnings

import config


def calculate_edge(fair_prob: float, market_odds: float) -> float:
    """Calcola l'edge percentuale rispetto alle probabilità fair.

    Formula: Edge% = (fair_prob * market_odds) - 1

    Un edge positivo indica valore favorevole al scommettitore;
    un edge negativo indica vantaggio per il bookmaker.

    Args:
        fair_prob: Probabilità fair stimata (0.0 - 1.0).
        market_odds: Quota di mercato decimale.

    Returns:
        Edge percentuale (0.02 = 2% di vantaggio).
    """
    return (fair_prob * market_odds) - 1.0


def kelly_criterion(edge: float, odds: float) -> float:
    """Calcola la dimensione ottimale della scommessa con il Kelly Criterion.

    Formula Kelly intera: f* = edge / (odds - 1)
    Formula Kelly frazionaria: f* *= KELLY_FRACTION

    Args:
        edge: Edge percentuale calcolato con calculate_edge().
        odds: Quota decimale.

    Returns:
        Frazione del bankroll da scommettere (Kelly frazionario).
        Restituisce 0.0 se l'edge è negativo.
    """
    if edge <= 0 or odds <= 1:
        return 0.0
    kelly_full = edge / (odds - 1.0)
    kelly_fractional = kelly_full * config.KELLY_FRACTION
    return min(kelly_fractional, 0.25)  # cap massimo al 25% del bankroll


def weighted_edge(
    edge_open: float,
    edge_close: float,
    weight_open: float = config.WEIGHT_OPEN,
    weight_close: float = config.WEIGHT_CLOSE,
) -> float:
    """Calcola l'edge ponderato combinando apertura e chiusura.

    Le odds di chiusura sono più informative (peso 65%) rispetto
    alle odds di apertura (peso 35%), poiché incorporano più informazioni.

    Args:
        edge_open: Edge calcolato sulle odds di apertura.
        edge_close: Edge calcolato sulle odds di chiusura.
        weight_open: Peso delle odds di apertura (default 0.35).
        weight_close: Peso delle odds di chiusura (default 0.65).

    Returns:
        Edge ponderato combinato.
    """
    if abs(weight_open + weight_close - 1.0) > 1e-6:
        warnings.warn(
            f"I pesi non sommano a 1.0: weight_open={weight_open}, weight_close={weight_close}. "
            "Il risultato potrebbe non essere un edge ponderato corretto.",
            stacklevel=2,
        )
    return edge_open * weight_open + edge_close * weight_close
