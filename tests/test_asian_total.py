"""Test per il modulo Asian Total."""

import pytest
from engine.asian_total import calculate_total_result, expected_value_total, analyze_total_line
from data.models import AsianLine


class TestTotalLineeIntere:
    """Test per linee intere (2.0, 3.0, 4.0)."""

    def test_over_25_tre_gol(self):
        """Over 2.5, 3 gol: vincita piena."""
        assert calculate_total_result(3, 2.5, "OVER") == 1.0

    def test_over_25_due_gol(self):
        """Over 2.5, 2 gol: perdita piena."""
        assert calculate_total_result(2, 2.5, "OVER") == -1.0

    def test_under_25_due_gol(self):
        """Under 2.5, 2 gol: vincita piena."""
        assert calculate_total_result(2, 2.5, "UNDER") == 1.0

    def test_over_30_tre_gol_push(self):
        """Over 3.0, esattamente 3 gol: push."""
        assert calculate_total_result(3, 3.0, "OVER") == 0.0

    def test_under_30_tre_gol_push(self):
        """Under 3.0, esattamente 3 gol: push."""
        assert calculate_total_result(3, 3.0, "UNDER") == 0.0

    def test_over_30_quattro_gol(self):
        """Over 3.0, 4 gol: vincita piena."""
        assert calculate_total_result(4, 3.0, "OVER") == 1.0

    def test_under_30_due_gol(self):
        """Under 3.0, 2 gol: vincita piena."""
        assert calculate_total_result(2, 3.0, "UNDER") == 1.0


class TestTotalQuarterLines:
    """Test per quarter-lines (2.75, 3.25, ecc.)."""

    def test_over_275_tre_gol(self):
        """Over 2.75, 3 gol: vincita piena (split su 2.5 e 3.0 → entrambi Over)."""
        result = calculate_total_result(3, 2.75, "OVER")
        # Split: Over 2.5 → win (1.0), Over 3.0 → push (0.0) → media: 0.5
        assert result == pytest.approx(0.5, abs=1e-9)

    def test_over_275_quattro_gol(self):
        """Over 2.75, 4 gol: vincita piena."""
        result = calculate_total_result(4, 2.75, "OVER")
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_over_275_due_gol(self):
        """Over 2.75, 2 gol: perdita piena."""
        result = calculate_total_result(2, 2.75, "OVER")
        # Split: Over 2.5 → lose (-1.0), Over 3.0 → lose (-1.0) → media: -1.0
        assert result == pytest.approx(-1.0, abs=1e-9)

    def test_under_275_due_gol(self):
        """Under 2.75, 2 gol: vincita piena."""
        result = calculate_total_result(2, 2.75, "UNDER")
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_under_275_tre_gol(self):
        """Under 2.75, 3 gol: mezza perdita (split su 2.5 e 3.0)."""
        result = calculate_total_result(3, 2.75, "UNDER")
        # Split: Under 2.5 → lose (-1.0), Under 3.0 → push (0.0) → media: -0.5
        assert result == pytest.approx(-0.5, abs=1e-9)

    def test_over_325_tre_gol(self):
        """Over 3.25, 3 gol: mezza perdita."""
        result = calculate_total_result(3, 3.25, "OVER")
        # Split: Over 3.0 → push (0.0), Over 3.5 → lose (-1.0) → media: -0.5
        assert result == pytest.approx(-0.5, abs=1e-9)

    def test_over_325_quattro_gol(self):
        """Over 3.25, 4 gol: vincita piena."""
        result = calculate_total_result(4, 3.25, "OVER")
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_under_325_tre_gol(self):
        """Under 3.25, 3 gol: mezza vincita."""
        result = calculate_total_result(3, 3.25, "UNDER")
        # Split: Under 3.0 → push (0.0), Under 3.5 → win (1.0) → media: 0.5
        assert result == pytest.approx(0.5, abs=1e-9)


class TestExpectedValueTotal:
    """Test per il calcolo dell'Expected Value Total."""

    def test_ev_over_positivo(self):
        """EV Over positivo con alta probabilità over."""
        ev = expected_value_total(0.55, 0.05, 0.40, 1.95)
        assert ev > 0

    def test_ev_under_negativo(self):
        """EV Under negativo con bassa probabilità under."""
        ev = expected_value_total(0.40, 0.05, 0.55, 1.95)
        # chiamato come prob_over, push, prob_under ma per UNDER invertiamo
        # Qui testiamo la formula diretta
        assert ev < 0

    def test_ev_formula(self):
        """Verifica la formula EV per Total."""
        prob_over = 0.50
        prob_push = 0.10
        prob_under = 0.40
        odds = 2.0
        expected = prob_over * (odds - 1) + prob_push * 0 - prob_under * 1
        assert expected_value_total(prob_over, prob_push, prob_under, odds) == pytest.approx(expected, abs=1e-9)


class TestAnalyzeTotalLine:
    """Test per l'analisi della linea Total."""

    def _make_line(self, t_open=2.75, t_close=2.75) -> AsianLine:
        return AsianLine(
            handicap_open=-0.75, handicap_close=-1.0,
            odds_home_open=1.93, odds_away_open=1.97,
            odds_home_close=1.90, odds_away_close=2.00,
            total_open=t_open, total_close=t_close,
            odds_over_open=1.95, odds_under_open=1.95,
            odds_over_close=1.88, odds_under_close=2.02,
        )

    def test_total_non_mosso(self):
        line = self._make_line(2.75, 2.75)
        result = analyze_total_line(line)
        assert result["total_moved"] is False
        assert result["total_direction"] == "none"

    def test_total_alzato(self):
        line = self._make_line(2.75, 3.0)
        result = analyze_total_line(line)
        assert result["total_moved"] is True
        assert result["total_direction"] == "over"

    def test_total_abbassato(self):
        line = self._make_line(3.0, 2.75)
        result = analyze_total_line(line)
        assert result["total_moved"] is True
        assert result["total_direction"] == "under"


class TestSideInvalido:
    """Test negativi per side non valido."""

    def test_side_invalido_solleva_value_error(self):
        """Side non valido deve sollevare ValueError con messaggio che contiene 'OVER'."""
        with pytest.raises(ValueError, match="OVER"):
            calculate_total_result(3, 2.5, "INVALID")

    def test_side_vuoto_solleva_value_error(self):
        """Side vuoto deve sollevare ValueError."""
        with pytest.raises(ValueError):
            calculate_total_result(3, 2.5, "")
