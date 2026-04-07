# sports/nba/services/prediction_service.py

from typing import Dict, Any

class PredictionService:
    def __init__(self, model=None):
        self.model = model  # wrapper k-p-kelly/nba-predictions

    def get_game_prediction(self, game_id: str) -> Dict[str, Any]:
        """
        Probabilité de victoire, score projeté, marge.
        """
        raise NotImplementedError

    def simulate_game(self, game_id: str, n: int = 10000) -> Dict[str, Any]:
        """
        Simulation Monte Carlo.
        """
        raise NotImplementedError
