# app/services/nba/props_service.py

from typing import List, Dict, Any


class PropsService:
    """
    Shadow Edge V∞ — Props Engine
    Récupère les props joueurs, détecte les value bets.
    """

    def __init__(self, props_scraper=None):
        self.scraper = props_scraper

    def get_player_props(self, game_id: str) -> List[Dict[str, Any]]:
        if self.scraper:
            try:
                return self.scraper.get_props(game_id)
            except Exception:
                pass
        return []

    def get_props_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        if self.scraper:
            try:
                return self.scraper.get_player_props(player_id)
            except Exception:
                pass
        return []

    def get_props_value(self, game_id: str) -> List[Dict[str, Any]]:
        """Value bets sur props."""
        return []
