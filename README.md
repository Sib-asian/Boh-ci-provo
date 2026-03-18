# ⚽ Sistema Pronostici Calcistici — Asian Handicap & Total

Sistema professionale di pronostici calcistici basato esclusivamente su **Asian Handicap** e **Asian Total**, con rimozione del margine bookmaker, rilevamento del denaro sharp e calcolo del valore atteso (EV).

---

## 🏗️ Struttura del Progetto

```
main.py                     # Entry point CLI
config.py                   # Configurazione globale
requirements.txt
data/
    models.py               # Dataclass: AsianLine, Match, Prediction
    loader.py               # Caricamento/salvataggio JSON
    matches_sample.json     # 5 partite di esempio
engine/
    probability_engine.py   # Rimozione margine: Power, Shin, Additive
    asian_handicap.py       # Calcolo AH: linee intere, half, quarter
    asian_total.py          # Calcolo Total: linee intere, half, quarter
    line_movement.py        # Movimento linee, steam move detection
    sharp_money.py          # Sharp money, Reverse Line Movement
    value_calculator.py     # Edge, Kelly Criterion, weighted edge
    predictor.py            # Motore principale pronostici
ui/
    cli.py                  # Interfaccia CLI interattiva
    formatter.py            # Formattazione output Rich
tests/
    test_asian_handicap.py
    test_asian_total.py
    test_probability_engine.py
```

---

## 🚀 Installazione e Avvio

```bash
pip install -r requirements.txt
python main.py
```

---

## 🧮 Matematica del Sistema

### Rimozione Margine Bookmaker

Il sistema implementa tre metodi per ottenere le **probabilità fair** dalle odds di mercato:

#### Power Method (default)
Trova il parametro `k` tale che `Σ odds_i^(-k) = 1`, poi `p_i = odds_i^(-k)`.
Il metodo più preciso per mercati a due esiti. Usa `scipy.optimize.brentq`.

#### Metodo Shin
Corregge le probabilità tenendo conto dell'**asimmetria informativa** tra bookmaker e scommettitori. Stima la proporzione di insider trading `z`.

#### Metodo Additivo
Semplice normalizzazione: `p_i = (1/odds_i) / Σ(1/odds_j)`. Veloce ma meno preciso.

---

### Asian Handicap — Calcolo Risultati

Il sistema gestisce tutte le tipologie di linee:

| Tipo | Esempi | Regola |
|------|--------|--------|
| Intera | 0, ±1.0, ±2.0 | Win/Push/Loss netto |
| Half-line | ±0.5, ±1.5 | Win/Loss (no push) |
| Quarter-line | ±0.25, ±0.75, ±1.25 | Split su due linee adiacenti (media) |

**Quarter-line (es. -0.75):** La scommessa è divisa su **-0.5** e **-1.0**:
- Se home vince 2-0: -0.5 = WIN(+1), -1.0 = WIN(+1) → media = +1.0 (vincita piena)
- Se home vince 1-0: -0.5 = WIN(+1), -1.0 = PUSH(0) → media = +0.5 (mezza vincita)

---

### Expected Value (EV)

```
EV = (P_win × (odds - 1)) + (P_push × 0) - (P_lose × 1)
```

### Edge Percentuale

```
Edge% = (fair_prob × market_odds) - 1
```

Le probabilità fair di **apertura** vengono usate come modello di riferimento per valutare le odds di **chiusura**:
- **edge_open** = fair_prob_open × odds_open − 1 (valore stimato all'apertura)
- **edge_close** = fair_prob_open × odds_close − 1 (valore offerto alla chiusura)
- **weighted_edge** = 0.35 × edge_open + 0.65 × edge_close

### Kelly Criterion (Frazionario)

```
Kelly_intero = Edge / (odds - 1)
Kelly_frazionario = Kelly_intero × 0.25   (25% del Kelly pieno)
```

---

### Score Composito

```
score = edge × 0.40 + line_movement_score × 0.30 + sharp_conf × 0.20 + 0.10
```

| Componente | Peso | Descrizione |
|-----------|------|-------------|
| Edge | 40% | Valore atteso vs mercato |
| Line Movement Score | 30% | Entità e direzione movimento linee |
| Sharp Confidence | 20% | Segnali denaro professionale |
| Base | 10% | Bonus fisso |

---

## 📊 Schema `matches_sample.json`

```json
[
  {
    "home_team": "Inter Milan",
    "away_team": "AC Milan",
    "league": "Serie A",
    "date": "2026-03-20",
    "asian_line": {
      "handicap_open": -0.75,
      "handicap_close": -1.0,
      "odds_home_open": 1.93,
      "odds_away_open": 1.97,
      "odds_home_close": 1.75,
      "odds_away_close": 2.15,
      "total_open": 2.75,
      "total_close": 2.75,
      "odds_over_open": 1.95,
      "odds_under_open": 1.95,
      "odds_over_close": 1.78,
      "odds_under_close": 2.12
    }
  }
]
```

---

## 🖥️ Interfaccia CLI

```
┌─────────────────────────────────────────────────────────┐
│  ⚽ Inter Milan vs AC Milan | Serie A | 2026-03-20      │
├─────────────────────────────────────────────────────────┤
│  AH Casa        -0.75 @ 1.93    -1.00 @ 1.75   ← -1.00 │
│  AH Trasferta   +0.75 @ 1.97    +1.00 @ 2.15           │
│  Total Over     2.75 @ 1.95     2.75 @ 1.78            │
│  Total Under    2.75 @ 1.95     2.75 @ 2.12            │
├─────────────────────────────────────────────────────────┤
│  🟢 PUNTA  AH AC Milan +1.00 @ 2.15                    │
│     Edge: +3.2% | Confidenza: 49% | Kelly: 0.7%        │
│     📌 Linea AH mossa verso casa. Steam move rilevato. │
└─────────────────────────────────────────────────────────┘
```

**Opzioni menu:**
1. Analizza tutte le partite
2. Solo segnali SHARP
3. Solo mercato Asian Handicap
4. Solo mercato Asian Total
5. Filtra per edge minimo personalizzato
6. Cambia file partite

---

## 📚 Glossario

| Termine | Definizione |
|---------|-------------|
| **Asian Handicap** | Mercato che elimina il pareggio applicando un handicap alla squadra favorita |
| **Quarter Line** | Linea AH/Total a multipli di 0.25 (es. -0.75); la scommessa viene divisa a metà su due linee adiacenti |
| **Exchange Betting** | Piattaforma (es. Betfair) dove si può scommettere SIA come PUNTA (backer) che come BANCA (layer) |
| **Edge** | Vantaggio percentuale del scommettitore rispetto alle probabilità fair |
| **Sharp Money** | Scommesse di giocatori professionisti (sharp) che influenzano le linee |
| **Steam Move** | Movimento rapido e significativo delle odds (>8%) dovuto a massicce scommesse sharp |
| **Reverse Line Movement (RLM)** | La linea si muove nella direzione opposta rispetto all'azione del pubblico, indicando denaro sharp |
| **Kelly Criterion** | Formula per calcolare la dimensione ottimale della scommessa in base all'edge e alle odds |
| **Margine Bookmaker** | La commissione implicita nelle odds (overround); rimossa per ottenere probabilità fair |
| **Power Method** | Tecnica di rimozione margine basata sull'esponente k che normalizza le probabilità |

---

## ✅ Esecuzione Test

```bash
python -m pytest tests/ -v
```

72 test unitari coprono:
- Tutte le tipologie di linee AH (intere, half, quarter)
- Tutte le tipologie di linee Total (intere, half, quarter)
- Tutti i metodi di rimozione margine (Power, Shin, Additive)
- Verifica `sum(probs) == 1.0` per tutti i metodi
