# app/services/nba/injury_service.py

from typing import List, Dict, Any


class InjuryService:
    """
    Shadow Edge V∞ — Injury Service
    Source: scraper externe (optionnel) ou nbainjuries.com
    Fallback propre si aucune source n'est disponible.
    """

    def __init__(self, scraper_client=None, nbainjuries_client=None):
        self.scraper     = scraper_client
        self.nbainjuries = nbainjuries_client

    def get_all_injuries(self) -> List[Dict[str, Any]]:
        """Toutes les blessures actuelles."""
        if self.scraper:
            try:
                return self.scraper.get_all_injuries()
            except Exception:
                pass
        if self.nbainjuries:
            try:
                return self.nbainjuries.get_all()
            except Exception:
                pass
        return []

    def get_team_injuries(self, team_id: str) -> List[Dict[str, Any]]:
        """Blessures d'une équipe."""
        if self.scraper:
            try:
                return self.scraper.get_team_injuries(team_id)
            except Exception:
                pass
        return []

    def get_player_injury(self, player_id: str) -> Dict[str, Any]:
        """Statut blessure d'un joueur."""
        if self.scraper:
            try:
                return self.scraper.get_player_injury(player_id)
            except Exception:
                pass
        return {"player_id": player_id, "status": None, "reason": None}
