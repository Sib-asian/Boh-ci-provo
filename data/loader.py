"""Caricamento e salvataggio dei dati delle partite."""

import json
from data.models import Match, AsianLine


def load_matches(filepath: str) -> list[Match]:
    """Carica le partite da un file JSON.

    Args:
        filepath: Percorso del file JSON contenente le partite.

    Returns:
        Lista di oggetti Match con le relative linee asiatiche.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = []
    for item in data:
        al = item["asian_line"]
        asian_line = AsianLine(
            handicap_open=al["handicap_open"],
            handicap_close=al["handicap_close"],
            odds_home_open=al["odds_home_open"],
            odds_away_open=al["odds_away_open"],
            odds_home_close=al["odds_home_close"],
            odds_away_close=al["odds_away_close"],
            total_open=al["total_open"],
            total_close=al["total_close"],
            odds_over_open=al["odds_over_open"],
            odds_under_open=al["odds_under_open"],
            odds_over_close=al["odds_over_close"],
            odds_under_close=al["odds_under_close"],
        )
        match = Match(
            home_team=item["home_team"],
            away_team=item["away_team"],
            league=item["league"],
            date=item["date"],
            asian_line=asian_line,
        )
        matches.append(match)

    return matches


def save_matches(matches: list[Match], filepath: str) -> None:
    """Salva le partite in un file JSON.

    Args:
        matches: Lista di oggetti Match da salvare.
        filepath: Percorso del file JSON di destinazione.
    """
    data = []
    for m in matches:
        al = m.asian_line
        data.append({
            "home_team": m.home_team,
            "away_team": m.away_team,
            "league": m.league,
            "date": m.date,
            "asian_line": {
                "handicap_open": al.handicap_open,
                "handicap_close": al.handicap_close,
                "odds_home_open": al.odds_home_open,
                "odds_away_open": al.odds_away_open,
                "odds_home_close": al.odds_home_close,
                "odds_away_close": al.odds_away_close,
                "total_open": al.total_open,
                "total_close": al.total_close,
                "odds_over_open": al.odds_over_open,
                "odds_under_open": al.odds_under_open,
                "odds_over_close": al.odds_over_close,
                "odds_under_close": al.odds_under_close,
            },
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
