"""Asian Handicap Predictor — Streamlit Web App."""

import json
import io
import pandas as pd
import streamlit as st

import config
from data.models import AsianLine, Match
from data.loader import load_matches, asian_line_from_dict, match_from_dict
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
    nowgoal_mode = st.toggle(
        "🌏 Modalità NowGoal",
        value=False,
        help="Attiva se inserisci quote da NowGoal: inverte automaticamente il segno dell'handicap (convenzione asiatica → occidentale).",
    )
    st.markdown("---")
    st.caption("Impostazioni applicate prima di ogni analisi.")


def _apply_nowgoal(handicap_open: float, handicap_close: float) -> tuple[float, float]:
    """Se nowgoal_mode è attivo, inverte il segno degli handicap."""
    if nowgoal_mode:
        return -handicap_open, -handicap_close
    return handicap_open, handicap_close


@st.cache_data
def _load_matches_cached(path: str):
    """Carica le partite da file con caching per evitare riletture inutili del disco."""
    return load_matches(path)


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
    ah_hcap_open, ah_hcap_close = _apply_nowgoal(ah_hcap_open, ah_hcap_close)
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
_CSV_COLUMNS = [
    "home_team", "away_team", "league", "date",
    "handicap_open", "handicap_close",
    "odds_home_open", "odds_home_close",
    "odds_away_open", "odds_away_close",
    "total_open", "total_close",
    "odds_over_open", "odds_over_close",
    "odds_under_open", "odds_under_close",
]

_TEMPLATE_CSV = (
    ",".join(_CSV_COLUMNS) + "\n"
    "Inter Milan,AC Milan,Serie A,2026-03-20,-0.75,-1.0,1.93,1.75,1.97,2.15,2.75,2.75,1.95,1.78,1.95,2.12\n"
)


def _matches_from_df(df: pd.DataFrame) -> list[Match]:
    """Converte un DataFrame (colonne CSV standard) in una lista di Match."""
    matches: list[Match] = []
    for row in df.itertuples(index=False):
        h_open, h_close = _apply_nowgoal(float(row.handicap_open), float(row.handicap_close))
        asian_line = AsianLine(
            handicap_open=h_open,
            handicap_close=h_close,
            odds_home_open=float(row.odds_home_open),
            odds_away_open=float(row.odds_away_open),
            odds_home_close=float(row.odds_home_close),
            odds_away_close=float(row.odds_away_close),
            total_open=float(row.total_open),
            total_close=float(row.total_close),
            odds_over_open=float(row.odds_over_open),
            odds_under_open=float(row.odds_under_open),
            odds_over_close=float(row.odds_over_close),
            odds_under_close=float(row.odds_under_close),
        )
        matches.append(
            Match(
                home_team=str(row.home_team),
                away_team=str(row.away_team),
                league=str(row.league),
                date=str(row.date),
                asian_line=asian_line,
            )
        )
    return matches


def _render_batch_results(matches_batch: list[Match]) -> None:
    """Esegue le predizioni e mostra i risultati con bottone download CSV."""
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


with tab_batch:
    st.header("Analisi Batch")
    st.markdown(
        "Carica un file o incolla i dati per analizzare più partite in una volta."
    )

    input_tab_json, input_tab_csv, input_tab_text = st.tabs(["📄 JSON", "📊 CSV", "📋 Incolla testo"])

    # ---- JSON ----
    with input_tab_json:
        uploaded_file = st.file_uploader("Carica file JSON", type=["json"])

        if uploaded_file is not None:
            _apply_config()
            try:
                raw_data = json.load(uploaded_file)
                matches_batch: list[Match] = []
                for item in raw_data:
                    al_dict = item["asian_line"]
                    h_open, h_close = _apply_nowgoal(
                        al_dict["handicap_open"], al_dict["handicap_close"]
                    )
                    matches_batch.append(match_from_dict({
                        **item,
                        "asian_line": {**al_dict, "handicap_open": h_open, "handicap_close": h_close},
                    }))
                _render_batch_results(matches_batch)
            except (KeyError, json.JSONDecodeError) as e:
                st.error(f"Errore nel parsing del file JSON: {e}")

    # ---- CSV ----
    with input_tab_csv:
        st.download_button(
            label="⬇️ Scarica template CSV",
            data=_TEMPLATE_CSV,
            file_name="template_partite.csv",
            mime="text/csv",
        )
        uploaded_csv = st.file_uploader("Carica file CSV", type=["csv"], key="csv_uploader")

        if uploaded_csv is not None:
            _apply_config()
            try:
                df_input = pd.read_csv(uploaded_csv)
                df_input.columns = [c.strip().lower() for c in df_input.columns]
                matches_csv = _matches_from_df(df_input)
                _render_batch_results(matches_csv)
            except Exception as e:
                st.error(f"Errore nel parsing del file CSV: {e}")

    # ---- Incolla testo ----
    with input_tab_text:
        st.markdown(
            "**Come usare:** incolla i dati nel formato seguente "
            "(una partita per riga, valori separati da virgola o tab):\n\n"
            "```\n"
            "home_team, away_team, league, date, hcap_open, hcap_close, "
            "odds_h_open, odds_h_close, odds_a_open, odds_a_close, "
            "total_open, total_close, odds_over_open, odds_over_close, "
            "odds_under_open, odds_under_close\n"
            "```"
        )

        text_input = st.text_area(
            "Incolla i dati qui (con intestazione o senza):",
            height=200,
            placeholder=(
                "Inter Milan,AC Milan,Serie A,2026-03-20,"
                "-0.75,-1.0,1.93,1.75,1.97,2.15,2.75,2.75,1.95,1.78,1.95,2.12"
            ),
        )

        parse_btn = st.button("🔍 Analizza testo incollato", key="parse_text_btn")

        if parse_btn and text_input.strip():
            _apply_config()
            try:
                first_line = text_input.strip().splitlines()[0]
                # Rileva intestazione: se il primo campo corrisponde al nome colonna atteso
                first_field = first_line.split(",")[0].strip().split("\t")[0].strip().lower()
                has_header = first_field == _CSV_COLUMNS[0]
                header_arg = 0 if has_header else None
                df_text = pd.read_csv(
                    io.StringIO(text_input),
                    sep=None,
                    engine="python",
                    header=header_arg,
                )
                if not has_header:
                    if len(df_text.columns) != len(_CSV_COLUMNS):
                        st.error(
                            f"Numero di colonne non corretto: attese {len(_CSV_COLUMNS)}, "
                            f"trovate {len(df_text.columns)}."
                        )
                    else:
                        df_text.columns = _CSV_COLUMNS
                        matches_text = _matches_from_df(df_text)
                        _render_batch_results(matches_text)
                else:
                    df_text.columns = [c.strip().lower() for c in df_text.columns]
                    matches_text = _matches_from_df(df_text)
                    _render_batch_results(matches_text)
            except Exception as e:
                st.error(f"Errore nel parsing del testo incollato: {e}")

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
            matches_sample = _load_matches_cached(sample_path)
            if nowgoal_mode:
                for m in matches_sample:
                    al = m.asian_line
                    al.handicap_open, al.handicap_close = _apply_nowgoal(
                        al.handicap_open, al.handicap_close
                    )
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
