# sports/nba/services/prediction_service.py

from typing import Dict, Any, Optional
import random
import math


class PredictionService:
    """
    Shadow Edge V∞ — Prediction Engine
    - Probabilités de victoire
    - Score projeté
    - Marge projetée
    - Simulation Monte Carlo
    - Compatible avec un futur modèle ML externe
    """

    def __init__(self, model=None):
        self.model = model  # futur modèle ML (optionnel)

    # ---------------------------------------------------------
    # 1) PREDICTION PRINCIPALE
    # ---------------------------------------------------------
    def get_game_prediction(self, game_id: str) -> Dict[str, Any]:
        """
        Retourne :
        - probabilité de victoire home/away
        - score projeté
        - marge
        """

        # Si un modèle ML est branché
        if self.model:
            try:
                return self.model.predict(game_id)
            except Exception:
                pass  # fallback sur modèle interne

        # Modèle interne simple (placeholder intelligent)
        home_prob = 0.50 + random.uniform(-0.05, 0.05)
        away_prob = 1 - home_prob

        projected_home = int(100 + random.uniform(-10, 10))
        projected_away = int(100 + random.uniform(-10, 10))

        margin = projected_home - projected_away

        return {
            "home_win_prob": round(home_prob, 3),
            "away_win_prob": round(away_prob, 3),
            "projected_score": {
                "home": projected_home,
                "away": projected_away,
            },
            "projected_margin": margin,
        }

    # ---------------------------------------------------------
    # 2) SIMULATION MONTE CARLO
    # ---------------------------------------------------------
    def simulate_game(self, game_id: str, n: int = 5000) -> Dict[str, Any]:
        """
        Simulation Monte Carlo basée sur le modèle interne.
        """

        base = self.get_game_prediction(game_id)

        home_mean = base["projected_score"]["home"]
        away_mean = base["projected_score"]["away"]

        home_wins = 0
        margins = []

        for _ in range(n):
            h = random.gauss(home_mean, 12)
            a = random.gauss(away_mean, 12)
            margins.append(h - a)
            if h > a:
                home_wins += 1

        return {
            "simulated_home_win_prob": round(home_wins / n, 3),
            "avg_margin": round(sum(margins) / len(margins), 2),
            "distribution": {
                "min": round(min(margins), 2),
                "max": round(max(margins), 2),
            },
        }
