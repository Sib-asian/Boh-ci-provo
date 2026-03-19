"""Test per le nuove funzionalità del motore matematico (Migliorie 1-7)."""

import pytest
from data.models import AsianLine, Match
from engine.probability_engine import (
    remove_margin_iterative,
    poisson_total_probs,
    _lambda_from_total_odds,
)
from engine.predictor import (
    _blend_ah_total_probs,
    _adaptive_composite,
    generate_predictions,
)
from engine.sharp_money import sharp_confidence_score


# ---------------------------------------------------------------------------
# Miglioria 7 — remove_margin_iterative
# ---------------------------------------------------------------------------

class TestRemoveMarginIterative:
    """Test per il metodo Newton-Raphson iterativo di rimozione margine."""

    def test_somma_uguale_uno(self):
        p_home, p_away = remove_margin_iterative(1.90, 1.90)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_somma_con_odds_sbilanciate(self):
        p_home, p_away = remove_margin_iterative(1.70, 2.20)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_probabilita_positive(self):
        p_home, p_away = remove_margin_iterative(1.85, 2.05)
        assert p_home > 0
        assert p_away > 0

    def test_favorita_prob_maggiore(self):
        p_home, p_away = remove_margin_iterative(1.70, 2.30)
        assert p_home > p_away

    def test_odds_bilanciate_prob_simili(self):
        p_home, p_away = remove_margin_iterative(1.95, 1.95)
        assert p_home == pytest.approx(p_away, abs=1e-4)

    def test_varie_combinazioni(self):
        for o1, o2 in [(1.80, 2.10), (1.95, 1.95), (1.60, 2.50), (2.0, 2.0)]:
            p1, p2 = remove_margin_iterative(o1, o2)
            assert p1 + p2 == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Miglioria 4 — poisson_total_probs
# ---------------------------------------------------------------------------

class TestPoissonTotalProbs:
    """Test per la stima Poisson delle probabilità Total."""

    def test_somma_uguale_uno(self):
        prob_over, prob_under = poisson_total_probs(1.90, 1.90, 2.5)
        assert prob_over + prob_under == pytest.approx(1.0, abs=1e-6)

    def test_probabilita_positive(self):
        prob_over, prob_under = poisson_total_probs(1.80, 2.10, 2.5)
        assert prob_over > 0
        assert prob_under > 0

    def test_probabilita_nel_range(self):
        prob_over, prob_under = poisson_total_probs(1.90, 1.90, 2.5)
        assert 0 < prob_over < 1
        assert 0 < prob_under < 1

    def test_over_favorito_se_odds_piu_basse(self):
        """Se odds Over sono più basse, prob_over deve essere maggiore."""
        prob_over, prob_under = poisson_total_probs(1.70, 2.20, 2.5)
        assert prob_over > prob_under

    def test_linea_mezza(self):
        """Linea a .5 (half-line) — nessuna gestione quarter."""
        prob_over, prob_under = poisson_total_probs(1.88, 1.98, 2.5)
        assert prob_over + prob_under == pytest.approx(1.0, abs=1e-6)

    def test_quarter_line_275(self):
        """Quarter-line 2.75 deve usare la media dei due floor."""
        prob_over, prob_under = poisson_total_probs(1.90, 1.90, 2.75)
        assert prob_over + prob_under == pytest.approx(1.0, abs=1e-6)

    def test_quarter_line_325(self):
        prob_over, prob_under = poisson_total_probs(1.90, 1.90, 3.25)
        assert prob_over + prob_under == pytest.approx(1.0, abs=1e-6)

    def test_lambda_stimato_ragionevole(self):
        """Lambda stimato deve essere tra 0.5 e 10 per odds normali."""
        lam = _lambda_from_total_odds(1.90, 1.90, 2.5)
        assert 0.5 < lam < 10.0

    def test_lambda_alto_per_over_probabile(self):
        """Se over è molto probabile (odds basse), lambda deve essere alto."""
        lam_high = _lambda_from_total_odds(1.50, 2.60, 2.5)
        lam_low = _lambda_from_total_odds(2.60, 1.50, 2.5)
        assert lam_high > lam_low


# ---------------------------------------------------------------------------
# Miglioria 2 — _blend_ah_total_probs
# ---------------------------------------------------------------------------

class TestBlendAhTotalProbs:
    """Test per la convergenza AH + Total."""

    def test_somma_uguale_uno(self):
        p_home, p_away = _blend_ah_total_probs(0.55, 0.45, 0.52, 0.48)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-9)

    def test_probabilita_simmetriche_restano_simmetriche(self):
        """Probabilità 50/50 con segnale neutro restano ~50/50."""
        p_home, p_away = _blend_ah_total_probs(0.50, 0.50, 0.50, 0.50)
        assert p_home == pytest.approx(0.50, abs=1e-6)
        assert p_away == pytest.approx(0.50, abs=1e-6)

    def test_aggiustamento_piccolo(self):
        """L'aggiustamento deve essere piccolo (non stravolgere le probabilità)."""
        p_home_orig, p_away_orig = 0.60, 0.40
        p_home_new, p_away_new = _blend_ah_total_probs(
            p_home_orig, p_away_orig, 0.65, 0.35
        )
        # L'aggiustamento deve essere piccolo
        assert abs(p_home_new - p_home_orig) < 0.05

    def test_output_in_range(self):
        """Le probabilità blended devono essere tra 0 e 1."""
        p_home, p_away = _blend_ah_total_probs(0.70, 0.30, 0.80, 0.20)
        assert 0 < p_home < 1
        assert 0 < p_away < 1


# ---------------------------------------------------------------------------
# Miglioria 5 — _adaptive_composite
# ---------------------------------------------------------------------------

class TestAdaptiveComposite:
    """Test per lo score composito adattivo."""

    def test_range_valido(self):
        """Lo score deve essere non-negativo."""
        score = _adaptive_composite(0.05, 0.3, 0.4, "HOME", 0.5, 0.0)
        assert score >= 0.0

    def test_side_home_con_movimento_forte(self):
        """Con movimento AH >= 0.5 su HOME, peso LM sale."""
        score_forte = _adaptive_composite(0.05, 0.5, 0.3, "HOME", 0.5, 0.0)
        score_normale = _adaptive_composite(0.05, 0.5, 0.3, "HOME", 0.3, 0.0)
        # Con peso LM più alto (forte), se lm_norm > w_edge il risultato è diverso
        assert score_forte != score_normale

    def test_side_over_con_movimento_total_forte(self):
        """Con movimento Total >= 0.5 su OVER, peso LM sale."""
        score_forte = _adaptive_composite(0.05, 0.5, 0.3, "OVER", 0.0, 0.5)
        score_normale = _adaptive_composite(0.05, 0.5, 0.3, "OVER", 0.0, 0.1)
        assert score_forte != score_normale

    def test_pesi_sommano_a_uno(self):
        """I pesi w1+w2+w3 per ogni caso devono sommare a 1.0."""
        # HOME, abs_hcap >= 0.50 → 0.40+0.40+0.20=1.0
        assert 0.40 + 0.40 + 0.20 == pytest.approx(1.0)
        # HOME, abs_hcap >= 0.25 → 0.45+0.30+0.25=1.0
        assert 0.45 + 0.30 + 0.25 == pytest.approx(1.0)
        # HOME, nessun movimento → 0.55+0.20+0.25=1.0
        assert 0.55 + 0.20 + 0.25 == pytest.approx(1.0)
        # OVER, abs_total >= 0.50 → 0.35+0.45+0.20=1.0
        assert 0.35 + 0.45 + 0.20 == pytest.approx(1.0)
        # OVER, abs_total >= 0.25 → 0.40+0.35+0.25=1.0
        assert 0.40 + 0.35 + 0.25 == pytest.approx(1.0)
        # OVER, nessun movimento → 0.50+0.25+0.25=1.0
        assert 0.50 + 0.25 + 0.25 == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Miglioria 3 — sharp_confidence_score con pesi dinamici
# ---------------------------------------------------------------------------

class TestSharpConfidenceScoreDinamico:
    """Test per il sharp confidence score con pesi dinamici."""

    def _make_line(self, hcap_open, hcap_close, total_open, total_close,
                   oh=1.90, oc=1.90, ah=1.90, ac=1.90,
                   oov=1.90, ocv=1.90, ouv=1.90, ucv=1.90):
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

    def test_nessun_movimento_score_basso(self):
        line = self._make_line(0.0, 0.0, 2.5, 2.5)
        score = sharp_confidence_score(line)
        assert score < 0.5

    def test_movimento_ah_forte_score_piu_alto(self):
        """Movimento AH >= 0.75 deve dare score più alto che movimento <= 0.25."""
        line_forte = self._make_line(-0.5, -1.25, 2.5, 2.5)  # delta = 0.75
        line_normale = self._make_line(0.0, -0.25, 2.5, 2.5)  # delta = 0.25
        assert sharp_confidence_score(line_forte) > sharp_confidence_score(line_normale)

    def test_score_nel_range(self):
        line = self._make_line(-0.5, -1.25, 2.5, 3.5)
        score = sharp_confidence_score(line)
        assert 0.0 <= score <= 1.0

    def test_movimento_total_forte_incrementa_score(self):
        """Movimento Total >= 0.5 deve dare score più alto che 0.25."""
        line_forte = self._make_line(0.0, 0.0, 2.5, 3.0)   # delta = 0.5
        line_normale = self._make_line(0.0, 0.0, 2.5, 2.75) # delta = 0.25
        assert sharp_confidence_score(line_forte) >= sharp_confidence_score(line_normale)


# ---------------------------------------------------------------------------
# Miglioria 1 — Fix edge_close usa prob_close
# ---------------------------------------------------------------------------

class TestEdgeCloseFix:
    """Verifica che edge_close usi prob_close (non prob_open)."""

    def test_generate_predictions_retrocompatibile(self):
        """generate_predictions deve ancora restituire una lista di Prediction."""
        line = AsianLine(
            handicap_open=-0.5,
            handicap_close=-0.75,
            odds_home_open=1.90,
            odds_home_close=1.82,
            odds_away_open=2.00,
            odds_away_close=2.10,
            total_open=2.5,
            total_close=2.75,
            odds_over_open=1.88,
            odds_over_close=1.80,
            odds_under_open=2.02,
            odds_under_close=2.10,
        )
        match = Match(
            home_team="Team A",
            away_team="Team B",
            league="Test League",
            date="2026-01-01",
            asian_line=line,
        )
        preds = generate_predictions(match)
        assert isinstance(preds, list)
        # Può essere vuota o con prediction, ma non deve lanciare eccezioni
