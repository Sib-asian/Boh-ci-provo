"""Test esaustivi per il modulo Asian Handicap."""

import pytest
from engine.asian_handicap import calculate_ah_result, expected_value_ah, analyze_ah_line
from data.models import AsianLine


class TestAHLineeIntere:
    """Test per linee intere (0, ±1.0, ±2.0)."""

    def test_linea_zero_casa_vince(self):
        """Home vince con linea 0: 2-1."""
        assert calculate_ah_result(2, 1, 0.0, "HOME") == 1.0

    def test_linea_zero_pareggio(self):
        """Linea 0, pareggio: push."""
        assert calculate_ah_result(1, 1, 0.0, "HOME") == 0.0

    def test_linea_zero_away_vince(self):
        """Linea 0, home perde: perdita piena."""
        assert calculate_ah_result(0, 1, 0.0, "HOME") == -1.0

    def test_linea_meno_uno_home_vince_di_due(self):
        """Home -1.0, home vince 2-0: vincita piena."""
        assert calculate_ah_result(2, 0, -1.0, "HOME") == 1.0

    def test_linea_meno_uno_home_vince_di_uno(self):
        """Home -1.0, home vince 1-0: push."""
        assert calculate_ah_result(1, 0, -1.0, "HOME") == 0.0

    def test_linea_meno_uno_home_pareggio(self):
        """Home -1.0, pareggio: perdita piena."""
        assert calculate_ah_result(1, 1, -1.0, "HOME") == -1.0

    def test_linea_piu_uno_away_side(self):
        """Away +1.0 (home -1.0 per away), home vince 2-0: perdita AWAY."""
        assert calculate_ah_result(2, 0, -1.0, "AWAY") == -1.0

    def test_linea_piu_uno_away_vince(self):
        """Away +1.0, away vince 0-1: vincita AWAY."""
        assert calculate_ah_result(0, 1, -1.0, "AWAY") == 1.0


class TestAHHalfLines:
    """Test per half-lines (±0.5, ±1.5)."""

    def test_meno_mezzo_home_vince(self):
        """Home -0.5, home vince 1-0: vincita piena."""
        assert calculate_ah_result(1, 0, -0.5, "HOME") == 1.0

    def test_meno_mezzo_pareggio(self):
        """Home -0.5, pareggio: perdita piena (non c'è push con half-line)."""
        assert calculate_ah_result(0, 0, -0.5, "HOME") == -1.0

    def test_piu_mezzo_away_pareggio(self):
        """Away +0.5, pareggio: vincita piena."""
        assert calculate_ah_result(0, 0, -0.5, "AWAY") == 1.0

    def test_meno_uno_mezzo_home_vince_due_zero(self):
        """Home -1.5, home vince 2-0: vincita piena."""
        assert calculate_ah_result(2, 0, -1.5, "HOME") == 1.0

    def test_meno_uno_mezzo_home_vince_uno_zero(self):
        """Home -1.5, home vince 1-0: perdita piena."""
        assert calculate_ah_result(1, 0, -1.5, "HOME") == -1.0


class TestAHQuarterLines:
    """Test per quarter-lines (±0.25, ±0.75, ±1.25)."""

    def test_meno_zero25_home_vince(self):
        """Home -0.25, home vince 1-0: vincita piena."""
        result = calculate_ah_result(1, 0, -0.25, "HOME")
        assert result == 1.0

    def test_meno_zero25_pareggio(self):
        """Home -0.25, pareggio: mezza perdita (split su 0 e -0.5)."""
        result = calculate_ah_result(0, 0, -0.25, "HOME")
        # Split: -0 = push (0.0) e -0.5 = perdita (-1.0) → media: -0.5
        assert result == pytest.approx(-0.5, abs=1e-9)

    def test_meno_zero75_home_vince_di_uno(self):
        """Home -0.75, home vince 1-0: mezza vincita."""
        result = calculate_ah_result(1, 0, -0.75, "HOME")
        # Split: -0.5 = vincita (1.0) e -1.0 = push (0.0) → media: 0.5
        assert result == pytest.approx(0.5, abs=1e-9)

    def test_meno_zero75_home_vince_di_due(self):
        """Home -0.75, home vince 2-0: vincita piena."""
        result = calculate_ah_result(2, 0, -0.75, "HOME")
        # Split: -0.5 = vincita (1.0) e -1.0 = vincita (1.0) → media: 1.0
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_piu_zero25_away_pareggio(self):
        """Away +0.25, pareggio: mezza vincita AWAY."""
        result = calculate_ah_result(0, 0, -0.25, "AWAY")
        # Away con handicap +0.25 → mezza vincita
        assert result == pytest.approx(0.5, abs=1e-9)

    def test_meno_uno25_home_vince_di_due(self):
        """Home -1.25, home vince 2-0: vincita piena (split -1.0=win, -1.5=win)."""
        result = calculate_ah_result(2, 0, -1.25, "HOME")
        # Split: -1.0 → adjusted=1.0 → WIN, -1.5 → adjusted=0.5 → WIN → media: 1.0
        assert result == pytest.approx(1.0, abs=1e-9)

    def test_meno_uno25_home_vince_di_tre(self):
        """Home -1.25, home vince 3-0: vincita piena."""
        result = calculate_ah_result(3, 0, -1.25, "HOME")
        assert result == pytest.approx(1.0, abs=1e-9)


class TestExpectedValueAH:
    """Test per il calcolo dell'Expected Value AH."""

    def test_ev_positivo(self):
        """EV positivo quando prob_win alta e odds favorevoli."""
        ev = expected_value_ah(0.55, 0.05, 0.40, 1.95)
        assert ev > 0

    def test_ev_negativo(self):
        """EV negativo quando prob_win bassa."""
        ev = expected_value_ah(0.40, 0.05, 0.55, 1.95)
        assert ev < 0

    def test_ev_formula(self):
        """Verifica formula EV: prob_win*(odds-1) - prob_lose."""
        prob_win = 0.50
        prob_push = 0.10
        prob_lose = 0.40
        odds = 2.0
        expected = prob_win * (odds - 1) + prob_push * 0 - prob_lose * 1
        assert expected_value_ah(prob_win, prob_push, prob_lose, odds) == pytest.approx(expected, abs=1e-9)


class TestAnalyzeAHLine:
    """Test per l'analisi della linea AH."""

    def _make_line(self, h_open=-0.75, h_close=-1.0) -> AsianLine:
        return AsianLine(
            handicap_open=h_open, handicap_close=h_close,
            odds_home_open=1.93, odds_away_open=1.97,
            odds_home_close=1.90, odds_away_close=2.00,
            total_open=2.75, total_close=2.75,
            odds_over_open=1.95, odds_under_open=1.95,
            odds_over_close=1.88, odds_under_close=2.02,
        )

    def test_handicap_moved(self):
        line = self._make_line()
        result = analyze_ah_line(line)
        assert result["handicap_moved"] is True
        assert result["handicap_direction"] == "home"

    def test_handicap_stabile(self):
        line = self._make_line(h_open=-0.5, h_close=-0.5)
        result = analyze_ah_line(line)
        assert result["handicap_moved"] is False
        assert result["handicap_direction"] == "none"


class TestSideInvalido:
    """Test negativi per side non valido."""

    def test_side_invalido_solleva_value_error(self):
        """Side non valido deve sollevare ValueError con messaggio che contiene 'HOME'."""
        with pytest.raises(ValueError, match="HOME"):
            calculate_ah_result(2, 1, -0.5, "INVALID")

    def test_side_vuoto_solleva_value_error(self):
        """Side vuoto deve sollevare ValueError."""
        with pytest.raises(ValueError):
            calculate_ah_result(2, 1, -0.5, "")
