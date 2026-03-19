# Configurazione globale del sistema di pronostici
# I valori possono essere sovrascritti tramite variabili d'ambiente.
import os

MIN_EDGE_THRESHOLD = float(os.environ.get("MIN_EDGE_THRESHOLD", "0.02"))
STEAM_MOVE_THRESHOLD = float(os.environ.get("STEAM_MOVE_THRESHOLD", "0.08"))
WEIGHT_OPEN = float(os.environ.get("WEIGHT_OPEN", "0.35"))
WEIGHT_CLOSE = float(os.environ.get("WEIGHT_CLOSE", "0.65"))
KELLY_FRACTION = float(os.environ.get("KELLY_FRACTION", "0.25"))
SHARP_CONFIDENCE_THRESHOLD = float(os.environ.get("SHARP_CONFIDENCE_THRESHOLD", "0.5"))
MARGIN_REMOVAL_METHOD = os.environ.get("MARGIN_REMOVAL_METHOD", "power")
BLEND_AH_TOTAL_WEIGHT = float(os.environ.get("BLEND_AH_TOTAL_WEIGHT", "0.15"))
POISSON_ENABLED = os.environ.get("POISSON_ENABLED", "true").lower() not in ("0", "false", "no")
