# app/services/nba/shotchart_service.py

from typing import List, Dict, Any


class ShotChartService:
    """
    Shadow Edge V∞ — Shot Chart Service
    Tirs par joueur, carte d'efficacité par zone,
    comparaison joueur vs défense adverse.
    """

    def __init__(self, db_client=None):
        self.db = db_client

    def get_player_shots(self, player_id: str, season: str) -> List[Dict[str, Any]]:
        """Tous les tirs d'un joueur pour une saison."""
        if self.db:
            try:
                return self.db.get_player_shots(player_id, season)
            except Exception:
                pass
        return []

    def get_shot_efficiency_map(self, player_id: str, season: str) -> Dict[str, Any]:
        """Agrège les tirs par zone et calcule l'efficacité (FG%, volume)."""
        if self.db:
            try:
                return self.db.get_shot_efficiency_map(player_id, season)
            except Exception:
                pass
        return {}

    def compare_player_vs_defense(self, player_id: str,
                                   opponent_team_id: str, season: str) -> Dict[str, Any]:
        """Zones fortes joueur vs zones faibles défense adverse."""
        if self.db:
            try:
                return self.db.compare_player_vs_defense(player_id, opponent_team_id, season)
            except Exception:
                pass
        return {}
