# sports/nba/services/injury_service.py

from typing import List, Dict, Any

class InjuryService:
    def __init__(self, scraper_client=None, nbainjuries_client=None):
        self.scraper = scraper_client
        self.nbainjuries = nbainjuries_client

    def get_all_injuries(self) -> List[Dict[str, Any]]:
        """
        Liste des blessures actuelles (statut, raison, équipe).
        """
        return []

    def get_team_injuries(self, team_id: str) -> List[Dict[str, Any]]:
        return []

    def get_player_injury(self, player_id: str) -> Dict[str, Any]:
        return []
