# app/services/nba/prediction_service.py

import random
from typing import Dict, Any, Optional


class PredictionService:
    """
    Shadow Edge V∞ — Prediction Engine
    - Probabilités de victoire
    - Score projeté + marge
    - Simulation Monte Carlo
    - Compatible futur modèle ML externe
    """

    def __init__(self, model=None):
        self.model = model

    # ───────────────────────────────────────────────────────────
    # 1) Prédiction principale
    # ───────────────────────────────────────────────────────────
    def get_game_prediction(self, game_id: str) -> Dict[str, Any]:
        if self.model:
            try:
                return self.model.predict(game_id)
            except Exception:
                pass

        home_prob = 0.50 + random.uniform(-0.05, 0.05)
        away_prob = round(1 - home_prob, 3)
        home_prob = round(home_prob, 3)

        projected_home = int(100 + random.uniform(-10, 10))
        projected_away = int(100 + random.uniform(-10, 10))

        return {
            "home_win_prob":    home_prob,
            "away_win_prob":    away_prob,
            "projected_score":  {"home": projected_home, "away": projected_away},
            "projected_margin": projected_home - projected_away,
        }

    # ───────────────────────────────────────────────────────────
    # 2) Simulation Monte Carlo
    # ───────────────────────────────────────────────────────────
    def simulate_game(self, game_id: str, n: int = 5000) -> Dict[str, Any]:
        base = self.get_game_prediction(game_id)

        home_mean = base["projected_score"]["home"]
        away_mean = base["projected_score"]["away"]

        home_wins = 0
        margins   = []

        for _ in range(n):
            h = random.gauss(home_mean, 12)
            a = random.gauss(away_mean, 12)
            margins.append(h - a)
            if h > a:
                home_wins += 1

        return {
            "simulated_home_win_prob": round(home_wins / n, 3),
            "avg_margin":              round(sum(margins) / len(margins), 2),
            "distribution": {
                "min": round(min(margins), 2),
                "max": round(max(margins), 2),
            },
        }
