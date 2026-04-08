# sports/nba/services/shotchart_service.py

from typing import List, Dict, Any

class ShotChartService:
    def __init__(self, db_client=None):
        self.db = db_client  # ou connexion aux données du repo toddwschneider

    def get_player_shots(self, player_id: str, season: str) -> List[Dict[str, Any]]:
        """
        Retourne tous les tirs d'un joueur pour une saison.
        """
        # TODO: brancher sur ta source (DB, CSV, API interne)
        raise NotImplementedError

    def get_shot_efficiency_map(self, player_id: str, season: str) -> Dict[str, Any]:
        """
        Agrège les tirs par zone et calcule l'efficacité.
        """
        # TODO: groupby zone, calcul FG%, volume, etc.
        raise NotImplementedError

    def compare_player_vs_defense(self, player_id: str, opponent_team_id: str, season: str) -> Dict[str, Any]:
        """
        Compare les zones fortes du joueur vs les zones faibles de la défense.
        """
        raise NotImplementedError
