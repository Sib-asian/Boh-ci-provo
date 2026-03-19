"""Modelli dati per il sistema di pronostici calcistici."""

from dataclasses import dataclass


@dataclass
class AsianLine:
    """Rappresenta le linee Asian Handicap e Asian Total per una partita."""

    handicap_open: float
    handicap_close: float
    odds_home_open: float
    odds_away_open: float
    odds_home_close: float
    odds_away_close: float
    total_open: float
    total_close: float
    odds_over_open: float
    odds_under_open: float
    odds_over_close: float
    odds_under_close: float

    def __post_init__(self) -> None:
        """Valida che tutte le odds siano > 1.0."""
        odds_fields = [
            "odds_home_open", "odds_away_open", "odds_home_close", "odds_away_close",
            "odds_over_open", "odds_under_open", "odds_over_close", "odds_under_close",
        ]
        for field_name in odds_fields:
            value = getattr(self, field_name)
            if value <= 1.0:
                raise ValueError(
                    f"La quota '{field_name}' deve essere > 1.0, ricevuto: {value}"
                )


@dataclass
class Match:
    """Rappresenta una partita di calcio con relative linee asiatiche."""

    home_team: str
    away_team: str
    league: str
    date: str
    asian_line: AsianLine


@dataclass
class Prediction:
    """Rappresenta un pronostico generato dal sistema."""

    match: Match
    market: str                  # "AH_HOME", "AH_AWAY", "TOTAL_OVER", "TOTAL_UNDER"
    side: str                    # "HOME", "AWAY", "OVER", "UNDER"
    recommendation: str          # "PUNTA" o "BANCA"
    edge: float                  # Edge percentuale (0.02 = 2%)
    confidence: float            # Confidenza 0-100
    reasoning: str               # Spiegazione testuale in italiano
    kelly: float                 # Percentuale Kelly per il bankroll
    odds: float = 0.0            # Quota di mercato usata
    handicap_or_total: float = 0.0  # Linea AH o Total di riferimento
