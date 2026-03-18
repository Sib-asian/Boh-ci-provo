"""Asian Handicap Predictor — Streamlit Web App."""

import json
import io
import pandas as pd
import streamlit as st

import config
from data.models import AsianLine, Match
from data.loader import load_matches
from engine.predictor import generate_predictions

st.set_page_config(
    page_title="Asian Handicap Predictor",
    page_icon="⚽",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — configurazione
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configurazione")

    margin_method = st.selectbox(
        "Metodo rimozione margine",
        options=["power", "shin", "additive"],
        index=["power", "shin", "additive"].index(config.MARGIN_REMOVAL_METHOD),
    )

    kelly_fraction = st.slider(
        "Kelly Fraction",
        min_value=0.05,
        max_value=0.50,
        value=config.KELLY_FRACTION,
        step=0.05,
        format="%.2f",
    )

    min_edge = st.slider(
        "Min Edge Threshold",
        min_value=0.01,
        max_value=0.10,
        value=config.MIN_EDGE_THRESHOLD,
        step=0.005,
        format="%.3f",
    )

    sharp_conf_threshold = st.slider(
        "Sharp Confidence Threshold",
        min_value=0.30,
        max_value=0.80,
        value=config.SHARP_CONFIDENCE_THRESHOLD,
        step=0.05,
        format="%.2f",
    )

    st.markdown("---")
    st.caption("Impostazioni applicate prima di ogni analisi.")


def _apply_config() -> None:
    """Aggiorna i valori di config con quelli scelti in sidebar."""
    config.MARGIN_REMOVAL_METHOD = margin_method
    config.KELLY_FRACTION = kelly_fraction
    config.MIN_EDGE_THRESHOLD = min_edge
    config.SHARP_CONFIDENCE_THRESHOLD = sharp_conf_threshold


def _build_match_from_form(
    home_team: str,
    away_team: str,
    league: str,
    date: str,
    ah_hcap_open: float,
    ah_hcap_close: float,
    odds_home_open: float,
    odds_home_close: float,
    odds_away_open: float,
    odds_away_close: float,
    total_open: float,
    total_close: float,
    odds_over_open: float,
    odds_over_close: float,
    odds_under_open: float,
    odds_under_close: float,
) -> Match:
    """Costruisce un oggetto Match dai valori del form."""
    asian_line = AsianLine(
        handicap_open=ah_hcap_open,
        handicap_close=ah_hcap_close,
        odds_home_open=odds_home_open,
        odds_away_open=odds_away_open,
        odds_home_close=odds_home_close,
        odds_away_close=odds_away_close,
        total_open=total_open,
        total_close=total_close,
        odds_over_open=odds_over_open,
        odds_under_open=odds_under_open,
        odds_over_close=odds_over_close,
        odds_under_close=odds_under_close,
    )
    return Match(
        home_team=home_team,
        away_team=away_team,
        league=league,
        date=date,
        asian_line=asian_line,
    )


def _render_predictions(predictions: list) -> None:
    """Mostra i pronostici come card espandibili."""
    if not predictions:
        st.info("Nessun pronostico supera la soglia di edge impostata.")
        return

    for pred in predictions:
        icon = "🟢" if pred.recommendation == "PUNTA" else "🔴"
        market_label = pred.market.replace("_", " ")
        header = f"{icon} {pred.recommendation} — {market_label} @ {pred.odds:.2f}"

        with st.expander(header, expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("Edge", f"{pred.edge * 100:.1f}%")
            c2.metric("Confidenza", f"{pred.confidence:.0f}%")
            c3.metric("Kelly", f"{pred.kelly * 100:.1f}%")
            st.markdown(f"**Reasoning:** {pred.reasoning}")


def _predictions_to_df(matches: list[Match]) -> pd.DataFrame:
    """Genera tutte le predizioni per una lista di partite e restituisce un DataFrame."""
    rows = []
    for match in matches:
        preds = generate_predictions(match)
        for p in preds:
            rows.append(
                {
                    "Partita": f"{match.home_team} vs {match.away_team}",
                    "Lega": match.league,
                    "Data": match.date,
                    "Mercato": p.market,
                    "Lato": p.side,
                    "Edge%": round(p.edge * 100, 2),
                    "Confidenza%": round(p.confidence, 1),
                    "Kelly%": round(p.kelly * 100, 2),
                    "Recommendation": p.recommendation,
                    "Quota": round(p.odds, 2),
                    "Reasoning": p.reasoning,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_single, tab_batch, tab_example = st.tabs(
    ["🔍 Analisi Singola", "📦 Analisi Batch", "📊 Dati di Esempio"]
)

# ---------------------------------------------------------------------------
# Tab 1 — Analisi singola
# ---------------------------------------------------------------------------
with tab_single:
    st.header("Analisi Singola Partita")

    with st.form("match_form"):
        st.subheader("Dati Partita")
        col_a, col_b, col_c, col_d = st.columns(4)
        home_team = col_a.text_input("Home Team", value="Juventus")
        away_team = col_b.text_input("Away Team", value="Inter")
        league = col_c.text_input("Lega", value="Serie A")
        date = col_d.text_input("Data (YYYY-MM-DD)", value="2024-03-15")

        st.subheader("Asian Handicap")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Apertura**")
            ah_hcap_open = st.number_input("Handicap Open", value=-0.5, step=0.25, format="%.2f")
            odds_home_open = st.number_input("Odds Home Open", value=1.90, min_value=1.01, step=0.01, format="%.2f")
            odds_away_open = st.number_input("Odds Away Open", value=2.00, min_value=1.01, step=0.01, format="%.2f")
        with col2:
            st.markdown("**Chiusura**")
            ah_hcap_close = st.number_input("Handicap Close", value=-0.75, step=0.25, format="%.2f")
            odds_home_close = st.number_input("Odds Home Close", value=1.85, min_value=1.01, step=0.01, format="%.2f")
            odds_away_close = st.number_input("Odds Away Close", value=2.05, min_value=1.01, step=0.01, format="%.2f")

        st.subheader("Total (Over/Under)")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Apertura**")
            total_open = st.number_input("Total Open", value=2.50, step=0.25, format="%.2f")
            odds_over_open = st.number_input("Odds Over Open", value=1.88, min_value=1.01, step=0.01, format="%.2f")
            odds_under_open = st.number_input("Odds Under Open", value=2.02, min_value=1.01, step=0.01, format="%.2f")
        with col4:
            st.markdown("**Chiusura**")
            total_close = st.number_input("Total Close", value=2.75, step=0.25, format="%.2f")
            odds_over_close = st.number_input("Odds Over Close", value=1.83, min_value=1.01, step=0.01, format="%.2f")
            odds_under_close = st.number_input("Odds Under Close", value=2.07, min_value=1.01, step=0.01, format="%.2f")

        submitted = st.form_submit_button("🔍 Analizza Partita")

    if submitted:
        _apply_config()
        match = _build_match_from_form(
            home_team=home_team,
            away_team=away_team,
            league=league,
            date=date,
            ah_hcap_open=ah_hcap_open,
            ah_hcap_close=ah_hcap_close,
            odds_home_open=odds_home_open,
            odds_home_close=odds_home_close,
            odds_away_open=odds_away_open,
            odds_away_close=odds_away_close,
            total_open=total_open,
            total_close=total_close,
            odds_over_open=odds_over_open,
            odds_over_close=odds_over_close,
            odds_under_open=odds_under_open,
            odds_under_close=odds_under_close,
        )
        with st.spinner("Analisi in corso…"):
            predictions = generate_predictions(match)

        st.subheader(f"Pronostici: {home_team} vs {away_team}")
        _render_predictions(predictions)

# ---------------------------------------------------------------------------
# Tab 2 — Analisi Batch
# ---------------------------------------------------------------------------
with tab_batch:
    st.header("Analisi Batch")
    st.markdown(
        "Carica un file JSON con la stessa struttura di `data/matches_sample.json` "
        "per analizzare più partite in una volta."
    )

    uploaded_file = st.file_uploader("Carica file JSON", type=["json"])

    if uploaded_file is not None:
        _apply_config()
        try:
            raw_data = json.load(uploaded_file)
            # Build Match objects manually from raw JSON
            matches_batch: list[Match] = []
            for item in raw_data:
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
                matches_batch.append(
                    Match(
                        home_team=item["home_team"],
                        away_team=item["away_team"],
                        league=item["league"],
                        date=item["date"],
                        asian_line=asian_line,
                    )
                )

            with st.spinner("Analisi in corso…"):
                df_batch = _predictions_to_df(matches_batch)

            if df_batch.empty:
                st.info("Nessun pronostico supera la soglia di edge per le partite caricate.")
            else:
                st.success(f"Trovati {len(df_batch)} pronostici su {len(matches_batch)} partite.")
                display_cols = ["Partita", "Mercato", "Lato", "Edge%", "Confidenza%", "Kelly%", "Recommendation"]
                st.dataframe(df_batch[display_cols], use_container_width=True)

                csv_buffer = io.StringIO()
                df_batch.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="⬇️ Scarica CSV",
                    data=csv_buffer.getvalue(),
                    file_name="pronostici_batch.csv",
                    mime="text/csv",
                )
        except (KeyError, json.JSONDecodeError) as e:
            st.error(f"Errore nel parsing del file JSON: {e}")

# ---------------------------------------------------------------------------
# Tab 3 — Dati di Esempio
# ---------------------------------------------------------------------------
with tab_example:
    st.header("Dati di Esempio")
    st.markdown("Analizza le partite di esempio incluse nel progetto (`data/matches_sample.json`).")

    if st.button("📂 Carica partite di esempio"):
        _apply_config()
        try:
            sample_path = "data/matches_sample.json"
            matches_sample = load_matches(sample_path)
            with st.spinner("Analisi in corso…"):
                df_sample = _predictions_to_df(matches_sample)

            if df_sample.empty:
                st.info("Nessun pronostico supera la soglia di edge per le partite di esempio.")
            else:
                st.success(f"Trovati {len(df_sample)} pronostici su {len(matches_sample)} partite di esempio.")
                display_cols = ["Partita", "Mercato", "Lato", "Edge%", "Confidenza%", "Kelly%", "Recommendation"]
                st.dataframe(df_sample[display_cols], use_container_width=True)

                csv_buffer = io.StringIO()
                df_sample.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="⬇️ Scarica CSV",
                    data=csv_buffer.getvalue(),
                    file_name="pronostici_esempio.csv",
                    mime="text/csv",
                )
        except FileNotFoundError:
            st.error("File `data/matches_sample.json` non trovato.")
        except (KeyError, json.JSONDecodeError) as e:
            st.error(f"Errore nel parsing dei dati di esempio: {e}")
