"""Motore principale di generazione dei pronostici calcistici."""

import config
from data.models import Match, Prediction, AsianLine
from engine.probability_engine import (
    remove_margin_power,
    remove_margin_shin,
    remove_margin_additive,
)
from engine.asian_handicap import analyze_ah_line
from engine.asian_total import analyze_total_line
from engine.line_movement import line_movement_score, handicap_movement, odds_movement
from engine.sharp_money import detect_sharp_side, sharp_confidence_score
from engine.value_calculator import calculate_edge, kelly_criterion, weighted_edge


def _get_fair_probs(
    odds_home: float, odds_away: float, method: str = config.MARGIN_REMOVAL_METHOD
) -> tuple[float, float]:
    """Seleziona il metodo di rimozione margine e restituisce probabilità fair.

    Args:
        odds_home: Quota casa.
        odds_away: Quota trasferta.
        method: Metodo da usare ("power", "shin", "additive").

    Returns:
        Tuple (prob_home, prob_away) con probabilità fair.
    """
    if method == "shin":
        return remove_margin_shin(odds_home, odds_away)
    elif method == "additive":
        return remove_margin_additive(odds_home, odds_away)
    else:
        return remove_margin_power(odds_home, odds_away)


def _build_reasoning_ah(
    side: str,
    handicap: float,
    odds: float,
    edge: float,
    ah_analysis: dict,
    sharp_side: str,
    sharp_conf: float,
    lm_score: float,
) -> str:
    """Genera il testo di reasoning per un pronostico AH.

    Args:
        side: "HOME" o "AWAY".
        handicap: Linea di handicap.
        odds: Quota utilizzata.
        edge: Edge calcolato.
        ah_analysis: Analisi del movimento AH.
        sharp_side: Lato sharp rilevato.
        sharp_conf: Confidenza sharp.
        lm_score: Score movimento linee.

    Returns:
        Stringa di reasoning in italiano.
    """
    parts = []

    # Movimento linea AH
    if ah_analysis["handicap_moved"]:
        direction = "verso casa" if ah_analysis["handicap_direction"] == "home" else "verso trasferta"
        parts.append(
            f"Linea AH mossa {direction} (da {ah_analysis['handicap_open']:+.2f} a {ah_analysis['handicap_close']:+.2f})"
        )

    # Steam move
    side_key = "home" if side == "HOME" else "away"
    pct_key = f"{side_key}_odds_change_pct"
    odds_pct = abs(ah_analysis.get(pct_key, 0)) * 100
    if odds_pct >= config.STEAM_MOVE_THRESHOLD * 100:
        parts.append(f"Steam move rilevato sulle odds ({odds_pct:.1f}% variazione)")

    # Sharp money
    if sharp_side == side and sharp_conf >= config.SHARP_CONFIDENCE_THRESHOLD:
        parts.append(
            f"Denaro sharp rilevato su {side} (confidenza: {sharp_conf * 100:.0f}%)"
        )
    elif sharp_side not in ("NONE", side) and sharp_conf >= config.SHARP_CONFIDENCE_THRESHOLD:
        parts.append("Reverse Line Movement: linea contraria all'azione sharp")

    # Edge
    parts.append(f"Edge calcolato: {edge * 100:+.1f}%")

    if not parts:
        parts.append(f"Valore identificato a quota {odds:.2f} con edge {edge * 100:+.1f}%")

    return ". ".join(parts) + "."


def _build_reasoning_total(
    side: str,
    total_line: float,
    odds: float,
    edge: float,
    total_analysis: dict,
    sharp_side: str,
    sharp_conf: float,
) -> str:
    """Genera il testo di reasoning per un pronostico Total.

    Args:
        side: "OVER" o "UNDER".
        total_line: Linea Total.
        odds: Quota utilizzata.
        edge: Edge calcolato.
        total_analysis: Analisi del movimento Total.
        sharp_side: Lato sharp rilevato.
        sharp_conf: Confidenza sharp.

    Returns:
        Stringa di reasoning in italiano.
    """
    parts = []

    # Movimento linea Total
    if total_analysis["total_moved"]:
        direction = "alzata" if total_analysis["total_direction"] == "over" else "abbassata"
        parts.append(
            f"Linea Total {direction} (da {total_analysis['total_open']:.2f} a {total_analysis['total_close']:.2f})"
        )

    # Steam move Total
    side_key = "over" if side == "OVER" else "under"
    pct_key = f"{side_key}_odds_change_pct"
    odds_pct = abs(total_analysis.get(pct_key, 0)) * 100
    if odds_pct >= config.STEAM_MOVE_THRESHOLD * 100:
        parts.append(f"Steam move rilevato sulle odds {side} ({odds_pct:.1f}% variazione)")

    # Sharp money sul Total
    if sharp_side == side and sharp_conf >= config.SHARP_CONFIDENCE_THRESHOLD:
        parts.append(
            f"Denaro sharp rilevato su {side} (confidenza: {sharp_conf * 100:.0f}%)"
        )

    # Edge
    parts.append(f"Edge calcolato: {edge * 100:+.1f}%")

    if not parts:
        parts.append(f"Valore identificato a quota {odds:.2f} con edge {edge * 100:+.1f}%")

    return ". ".join(parts) + "."


def generate_predictions(match: Match) -> list[Prediction]:
    """Genera tutti i pronostici per una partita.

    Pipeline:
    1. Calcola probabilità fair (apertura e chiusura) per AH e Total
    2. Calcola edge su tutti i mercati
    3. Analizza movimento linee
    4. Rileva sharp money
    5. Score composito e filtraggio
    6. Assegna PUNTA/BANCA
    7. Genera reasoning in italiano

    Args:
        match: Oggetto Match con le linee asiatiche.

    Returns:
        Lista di oggetti Prediction con edge > MIN_EDGE_THRESHOLD.
    """
    line = match.asian_line
    predictions: list[Prediction] = []

    # --- Probabilità fair AH ---
    prob_home_open, prob_away_open = _get_fair_probs(
        line.odds_home_open, line.odds_away_open
    )
    prob_home_close, prob_away_close = _get_fair_probs(
        line.odds_home_close, line.odds_away_close
    )

    # --- Probabilità fair Total ---
    prob_over_open, prob_under_open = _get_fair_probs(
        line.odds_over_open, line.odds_under_open
    )
    prob_over_close, prob_under_close = _get_fair_probs(
        line.odds_over_close, line.odds_under_close
    )

    # --- Analisi movimenti ---
    ah_analysis = analyze_ah_line(line)
    total_analysis = analyze_total_line(line)

    # --- Sharp money ---
    sharp_side = detect_sharp_side(line)
    sharp_conf = sharp_confidence_score(line)

    # --- Score movimento linee ---
    lm_score = line_movement_score(ah_analysis, total_analysis)

    # --- Calcolo edge per ogni mercato ---
    markets = [
        {
            "market": "AH_HOME",
            "side": "HOME",
            "odds_open": line.odds_home_open,
            "odds_close": line.odds_home_close,
            "prob_open": prob_home_open,
            "prob_close": prob_home_close,
            "handicap_or_total": line.handicap_close,
        },
        {
            "market": "AH_AWAY",
            "side": "AWAY",
            "odds_open": line.odds_away_open,
            "odds_close": line.odds_away_close,
            "prob_open": prob_away_open,
            "prob_close": prob_away_close,
            "handicap_or_total": -line.handicap_close,
        },
        {
            "market": "TOTAL_OVER",
            "side": "OVER",
            "odds_open": line.odds_over_open,
            "odds_close": line.odds_over_close,
            "prob_open": prob_over_open,
            "prob_close": prob_over_close,
            "handicap_or_total": line.total_close,
        },
        {
            "market": "TOTAL_UNDER",
            "side": "UNDER",
            "odds_open": line.odds_under_open,
            "odds_close": line.odds_under_close,
            "prob_open": prob_under_open,
            "prob_close": prob_under_close,
            "handicap_or_total": line.total_close,
        },
    ]

    for m in markets:
        # Edge calcolato usando la probabilità di apertura come modello di riferimento
        # (le odds di apertura riflettono il mercato prima dell'azione sharp)
        # edge_open = valore stimato al momento dell'apertura
        # edge_close = valore offerto al momento della chiusura (price da battere)
        edge_open = calculate_edge(m["prob_open"], m["odds_open"])
        edge_close = calculate_edge(m["prob_open"], m["odds_close"])
        w_edge = weighted_edge(edge_open, edge_close)

        if w_edge <= config.MIN_EDGE_THRESHOLD:
            continue

        # Score composito
        sharp_norm = sharp_conf  # già 0-1
        lm_norm = lm_score / 100.0
        composite = w_edge * 0.40 + lm_norm * 0.30 + sharp_norm * 0.20 + 0.10

        # Confidenza: score composito scalato a 0-100
        confidence = min(composite * 100.0, 100.0)

        # Kelly criterion
        kelly = kelly_criterion(w_edge, m["odds_close"])

        # PUNTA = scommessa standard su exchange
        # BANCA = lay bet su exchange
        recommendation = "PUNTA"

        # Reasoning
        side = m["side"]
        if side in ("HOME", "AWAY"):
            reasoning = _build_reasoning_ah(
                side=side,
                handicap=m["handicap_or_total"],
                odds=m["odds_close"],
                edge=w_edge,
                ah_analysis=ah_analysis,
                sharp_side=sharp_side,
                sharp_conf=sharp_conf,
                lm_score=lm_score,
            )
        else:
            reasoning = _build_reasoning_total(
                side=side,
                total_line=m["handicap_or_total"],
                odds=m["odds_close"],
                edge=w_edge,
                total_analysis=total_analysis,
                sharp_side=sharp_side,
                sharp_conf=sharp_conf,
            )

        pred = Prediction(
            match=match,
            market=m["market"],
            side=side,
            recommendation=recommendation,
            edge=w_edge,
            confidence=confidence,
            reasoning=reasoning,
            kelly=kelly,
            odds=m["odds_close"],
            handicap_or_total=m["handicap_or_total"],
        )
        predictions.append(pred)

    # Ordina per edge decrescente
    predictions.sort(key=lambda p: p.edge, reverse=True)
    return predictions
