"""Test per il motore di calcolo delle probabilità (margin removal)."""

import pytest
from engine.probability_engine import (
    remove_margin_power,
    remove_margin_shin,
    remove_margin_additive,
    implied_probability,
    fair_odds,
)


class TestImpliedProbability:
    """Test per la probabilità implicita."""

    def test_quota_due(self):
        assert implied_probability(2.0) == pytest.approx(0.5, abs=1e-9)

    def test_quota_190(self):
        assert implied_probability(1.90) == pytest.approx(1 / 1.90, abs=1e-9)

    def test_quota_invalida(self):
        with pytest.raises(ValueError):
            implied_probability(0.0)

    def test_quota_negativa(self):
        with pytest.raises(ValueError):
            implied_probability(-1.5)


class TestFairOdds:
    """Test per la conversione probabilità → quota fair."""

    def test_prob_mezzo(self):
        assert fair_odds(0.5) == pytest.approx(2.0, abs=1e-9)

    def test_prob_invalida_zero(self):
        with pytest.raises(ValueError):
            fair_odds(0.0)

    def test_prob_invalida_uno(self):
        with pytest.raises(ValueError):
            fair_odds(1.0)


class TestRemoveMarginPower:
    """Test per il Power Method di rimozione margine."""

    def test_somma_probabilita_uguale_uno(self):
        """La somma delle probabilità fair deve essere 1.0."""
        p_home, p_away = remove_margin_power(1.90, 1.90)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_somma_con_margine(self):
        """Anche con odds sbilanciate la somma deve essere 1.0."""
        p_home, p_away = remove_margin_power(1.70, 2.20)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_probabilita_positive(self):
        p_home, p_away = remove_margin_power(1.85, 2.05)
        assert p_home > 0
        assert p_away > 0

    def test_odds_bilanciate_prob_uguali(self):
        """Con odds bilanciate le probabilità sono uguali."""
        p_home, p_away = remove_margin_power(1.95, 1.95)
        assert p_home == pytest.approx(p_away, abs=1e-6)

    def test_favorita_prob_maggiore(self):
        """La squadra favorita ha probabilità maggiore."""
        p_home, p_away = remove_margin_power(1.70, 2.30)
        assert p_home > p_away

    def test_varie_combinazioni(self):
        """Test su diverse combinazioni di odds."""
        for o1, o2 in [(1.80, 2.10), (1.95, 1.95), (1.60, 2.50), (2.0, 2.0)]:
            p1, p2 = remove_margin_power(o1, o2)
            assert p1 + p2 == pytest.approx(1.0, abs=1e-6)


class TestRemoveMarginShin:
    """Test per il Metodo Shin di rimozione margine."""

    def test_somma_probabilita_uguale_uno(self):
        p_home, p_away = remove_margin_shin(1.90, 1.90)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_somma_con_odds_sbilanciate(self):
        p_home, p_away = remove_margin_shin(1.70, 2.20)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-6)

    def test_probabilita_positive(self):
        p_home, p_away = remove_margin_shin(1.85, 2.05)
        assert p_home > 0
        assert p_away > 0

    def test_favorita_prob_maggiore(self):
        p_home, p_away = remove_margin_shin(1.70, 2.30)
        assert p_home > p_away

    def test_varie_combinazioni(self):
        for o1, o2 in [(1.80, 2.10), (1.95, 1.95), (1.60, 2.50), (2.0, 2.0)]:
            p1, p2 = remove_margin_shin(o1, o2)
            assert p1 + p2 == pytest.approx(1.0, abs=1e-6)


class TestRemoveMarginAdditive:
    """Test per il Metodo Additivo di rimozione margine."""

    def test_somma_probabilita_uguale_uno(self):
        p_home, p_away = remove_margin_additive(1.90, 1.90)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-9)

    def test_somma_con_odds_sbilanciate(self):
        p_home, p_away = remove_margin_additive(1.70, 2.20)
        assert p_home + p_away == pytest.approx(1.0, abs=1e-9)

    def test_probabilita_positive(self):
        p_home, p_away = remove_margin_additive(1.85, 2.05)
        assert p_home > 0
        assert p_away > 0

    def test_odds_bilanciate_prob_uguali(self):
        p_home, p_away = remove_margin_additive(1.95, 1.95)
        assert p_home == pytest.approx(p_away, abs=1e-9)

    def test_favorita_prob_maggiore(self):
        p_home, p_away = remove_margin_additive(1.70, 2.30)
        assert p_home > p_away

    def test_varie_combinazioni(self):
        for o1, o2 in [(1.80, 2.10), (1.95, 1.95), (1.60, 2.50), (2.0, 2.0)]:
            p1, p2 = remove_margin_additive(o1, o2)
            assert p1 + p2 == pytest.approx(1.0, abs=1e-9)


class TestCoerenzaMetodi:
    """Test di coerenza tra i diversi metodi di margin removal."""

    def test_tutti_i_metodi_sommano_a_uno(self):
        """Tutti i metodi devono restituire probabilità che sommano a 1.0."""
        odds_pairs = [(1.90, 1.90), (1.75, 2.15), (2.0, 2.0)]
        for o1, o2 in odds_pairs:
            p_pow = remove_margin_power(o1, o2)
            p_shin = remove_margin_shin(o1, o2)
            p_add = remove_margin_additive(o1, o2)
            assert sum(p_pow) == pytest.approx(1.0, abs=1e-6), f"Power method fallisce con {o1}/{o2}"
            assert sum(p_shin) == pytest.approx(1.0, abs=1e-6), f"Shin method fallisce con {o1}/{o2}"
            assert sum(p_add) == pytest.approx(1.0, abs=1e-9), f"Additive method fallisce con {o1}/{o2}"

    def test_direzione_coerente(self):
        """Tutti i metodi devono concordare su quale squadra è favorita."""
        p_pow = remove_margin_power(1.70, 2.30)
        p_shin = remove_margin_shin(1.70, 2.30)
        p_add = remove_margin_additive(1.70, 2.30)

        # Con odds 1.70 < 2.30, la squadra home è favorita
        assert p_pow[0] > p_pow[1], "Power: home deve essere favorita"
        assert p_shin[0] > p_shin[1], "Shin: home deve essere favorita"
        assert p_add[0] > p_add[1], "Additive: home deve essere favorita"
