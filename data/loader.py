"""Caricamento e salvataggio dei dati delle partite."""

import json
from data.models import Match, AsianLine


def asian_line_from_dict(d: dict) -> AsianLine:
    """Costruisce un oggetto AsianLine da un dizionario JSON.

    Args:
        d: Dizionario con i campi della linea asiatica.

    Returns:
        Oggetto AsianLine.
    """
    return AsianLine(
        handicap_open=d["handicap_open"],
        handicap_close=d["handicap_close"],
        odds_home_open=d["odds_home_open"],
        odds_away_open=d["odds_away_open"],
        odds_home_close=d["odds_home_close"],
        odds_away_close=d["odds_away_close"],
        total_open=d["total_open"],
        total_close=d["total_close"],
        odds_over_open=d["odds_over_open"],
        odds_under_open=d["odds_under_open"],
        odds_over_close=d["odds_over_close"],
        odds_under_close=d["odds_under_close"],
    )


def match_from_dict(item: dict) -> Match:
    """Costruisce un oggetto Match da un dizionario JSON.

    Args:
        item: Dizionario con i campi della partita (include 'asian_line').

    Returns:
        Oggetto Match.
    """
    return Match(
        home_team=item["home_team"],
        away_team=item["away_team"],
        league=item["league"],
        date=item["date"],
        asian_line=asian_line_from_dict(item["asian_line"]),
    )


def load_matches(filepath: str) -> list[Match]:
    """Carica le partite da un file JSON.

    Args:
        filepath: Percorso del file JSON contenente le partite.

    Returns:
        Lista di oggetti Match con le relative linee asiatiche.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [match_from_dict(item) for item in data]


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
