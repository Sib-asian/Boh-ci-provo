"""Test per edge case critici del sistema di pronostici calcistici."""

import warnings

import pytest

from data.models import AsianLine, Match
from engine.probability_engine import remove_margin_shin
from engine.value_calculator import weighted_edge, kelly_criterion
from engine.sharp_money import detect_sharp_side
from engine.predictor import generate_predictions


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_line(
    hcap_open=0.0, hcap_close=0.0,
    total_open=2.5, total_close=2.5,
    oh=1.90, oc=1.90, ah=1.90, ac=1.90,
    oov=1.90, ocv=1.90, ouv=1.90, ucv=1.90,
) -> AsianLine:
    return AsianLine(
        handicap_open=hcap_open,
        handicap_close=hcap_close,
        odds_home_open=oh,
        odds_home_close=oc,
        odds_away_open=ah,
        odds_away_close=ac,
        total_open=total_open,
        total_close=total_close,
        odds_over_open=oov,
        odds_over_close=ocv,
        odds_under_open=ouv,
        odds_under_close=ucv,
    )


def _make_match(line: AsianLine) -> Match:
    return Match(
        home_team="Team A",
        away_team="Team B",
        league="Test League",
        date="2026-01-01",
        asian_line=line,
    )


# ---------------------------------------------------------------------------
# engine/probability_engine.py — Shin odds estreme
# ---------------------------------------------------------------------------

class TestShinOddsEstreme:
    """Verifica che remove_margin_shin non sollevi eccezioni con odds estreme."""

    def test_shin_odds_molto_estreme(self):
        """Odds 1.05 / 15.0 — nessuna eccezione, somma ≈ 1.0."""
        p_home, p_away = remove_margin_shin(1.05, 15.0)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)
        assert p_home > 0
        assert p_away > 0

    def test_shin_odds_massimamente_sbilanciate(self):
        """Odds 1.01 / 50.0 — nessuna eccezione, somma ≈ 1.0."""
        p_home, p_away = remove_margin_shin(1.01, 50.0)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)
        assert p_home > 0
        assert p_away > 0

    def test_shin_odds_bilanciate(self):
        """Odds 1.90 / 1.90 — deve restituire circa (0.5, 0.5)."""
        p_home, p_away = remove_margin_shin(1.90, 1.90)
        assert p_home == pytest.approx(0.5, abs=0.02)
        assert p_away == pytest.approx(0.5, abs=0.02)


# ---------------------------------------------------------------------------
# engine/value_calculator.py — edge e Kelly edge case
# ---------------------------------------------------------------------------

class TestWeightedEdgePesiNonNormalizzati:
    """Verifica che weighted_edge emetta un warning se i pesi non sommano a 1."""

    def test_pesi_non_sommano_a_uno_emette_warning(self):
        """weight_open=0.5, weight_close=0.5 — non deve crashare, emette warning."""
        # Pesi che NON sommano a 1 → devono scatenare UserWarning
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = weighted_edge(0.03, 0.04, weight_open=0.5, weight_close=0.6)
        assert any(issubclass(w.category, UserWarning) for w in caught)
        # Il risultato deve essere la somma pesata matematica
        assert result == pytest.approx(0.03 * 0.5 + 0.04 * 0.6, abs=1e-9)

    def test_pesi_corretti_nessun_warning(self):
        """Con weight_open=0.35, weight_close=0.65 non deve emettere warning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            weighted_edge(0.03, 0.04, weight_open=0.35, weight_close=0.65)
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) == 0


class TestKellyCriterionEdgeCase:
    """Test per kelly_criterion con valori limite."""

    def test_kelly_criterion_odds_esattamente_uno(self):
        """kelly_criterion(0.05, 1.0) deve restituire 0.0 (denominatore zero protetto)."""
        assert kelly_criterion(0.05, 1.0) == 0.0

    def test_kelly_criterion_edge_negativo(self):
        """Edge negativo deve restituire 0.0."""
        assert kelly_criterion(-0.05, 1.90) == 0.0

    def test_kelly_criterion_edge_zero(self):
        """Edge zero deve restituire 0.0."""
        assert kelly_criterion(0.0, 1.90) == 0.0


# ---------------------------------------------------------------------------
# engine/sharp_money.py — detect_sharp_side edge case
# ---------------------------------------------------------------------------

class TestDetectSharpSideEdgeCase:
    """Test per detect_sharp_side con mercati piatti."""

    def test_detect_sharp_side_tutto_piatto(self):
        """AsianLine con tutti i valori open == close deve restituire 'NONE'."""
        line = _make_line(
            hcap_open=0.0, hcap_close=0.0,
            total_open=2.5, total_close=2.5,
            oh=1.90, oc=1.90, ah=1.90, ac=1.90,
            oov=1.90, ocv=1.90, ouv=1.90, ucv=1.90,
        )
        assert detect_sharp_side(line) == "NONE"

    def test_detect_sharp_side_nessun_movimento_ah_ne_total(self):
        """Linea AH invariata, Total invariato — nessuno steam move → 'NONE'."""
        line = _make_line(
            hcap_open=-0.5, hcap_close=-0.5,
            total_open=2.75, total_close=2.75,
            oh=1.93, oc=1.93, ah=1.97, ac=1.97,
            oov=1.88, ocv=1.88, ouv=2.02, ucv=2.02,
        )
        assert detect_sharp_side(line) == "NONE"


# ---------------------------------------------------------------------------
# engine/predictor.py — generate_predictions con dati piatti
# ---------------------------------------------------------------------------

class TestGeneratePredictionsPartitaPiatta:
    """Verifica che generate_predictions non sollevi eccezioni con dati piatti."""

    def test_partita_completamente_piatta(self):
        """Un Match dove tutti open == close non solleva eccezioni."""
        line = _make_line(
            hcap_open=0.0, hcap_close=0.0,
            total_open=2.5, total_close=2.5,
            oh=1.90, oc=1.90, ah=1.90, ac=1.90,
            oov=1.90, ocv=1.90, ouv=1.90, ucv=1.90,
        )
        match = _make_match(line)
        result = generate_predictions(match)
        assert isinstance(result, list)
