# sports/nba/services/matchup_service.py

from typing import List, Dict, Any

class MatchupService:
    def __init__(self, matchup_source=None):
        self.source = matchup_source  # wrapper joshua-berry/nba-matchups

    def get_matchups(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Matchups individuels pour un match.
        """
        raise NotImplementedError

    def get_player_matchup(self, player_id: str, opponent_team_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_mismatch_alerts(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Détection automatique des mismatchs.
        """
        raise NotImplementedError
