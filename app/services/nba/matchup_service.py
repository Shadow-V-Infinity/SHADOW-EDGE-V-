# app/services/nba/matchup_service.py

from typing import List, Dict, Any


class MatchupService:
    """
    Shadow Edge V∞ — Matchup Service
    Détection des mismatchs défensifs/offensifs.
    """

    def __init__(self, matchup_source=None):
        self.source = matchup_source

    def get_matchups(self, game_id: str) -> List[Dict[str, Any]]:
        """Matchups individuels pour un match."""
        if self.source:
            try:
                return self.source.get_matchups(game_id)
            except Exception:
                pass
        return []

    def get_player_matchup(self, player_id: str, opponent_team_id: str) -> Dict[str, Any]:
        """Matchup d'un joueur face à une équipe."""
        if self.source:
            try:
                return self.source.get_player_matchup(player_id, opponent_team_id)
            except Exception:
                pass
        return {"player_id": player_id, "opponent_team_id": opponent_team_id, "data": None}

    def get_mismatch_alerts(self, game_id: str) -> List[Dict[str, Any]]:
        """Détection automatique des mismatchs critiques."""
        if self.source:
            try:
                return self.source.get_mismatch_alerts(game_id)
            except Exception:
                pass
        return []
