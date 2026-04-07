# sports/nba/services/props_service.py

from typing import List, Dict, Any

class PropsService:
    def __init__(self, props_scraper=None):
        self.scraper = props_scraper  # wrapper the-m-v/nba-player-props-scraper

    def get_player_props(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Retourne toutes les props d’un match.
        """
        raise NotImplementedError

    def get_props_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
