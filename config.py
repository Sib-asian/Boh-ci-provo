# Configurazione globale del sistema di pronostici
MIN_EDGE_THRESHOLD = 0.02        # Edge minimo per considerare una scommessa
STEAM_MOVE_THRESHOLD = 0.08      # Soglia per rilevare steam move (8%)
WEIGHT_OPEN = 0.35               # Peso delle odds di apertura
WEIGHT_CLOSE = 0.65              # Peso delle odds di chiusura
KELLY_FRACTION = 0.25            # Frazione Kelly (Kelly frazionario al 25%)
SHARP_CONFIDENCE_THRESHOLD = 0.5 # Soglia di confidenza per segnali sharp
MARGIN_REMOVAL_METHOD = "power"  # Metodo di rimozione margine: "power", "shin", "additive"
