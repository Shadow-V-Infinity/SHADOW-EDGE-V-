# app/services/nba/trends_service.py

from typing import Dict, Any


class TrendsService:
    """
    Shadow Edge V∞ — Trends Engine
    Forme, moyenne de points, séries, momentum global.
    """

    def __init__(self, source=None):
        self.source = source

    def get_trends(self, game_id: str) -> Dict[str, Any]:
        if self.source:
            try:
                return self.source.get_trends(game_id)
            except Exception:
                pass
        return {
            "home": {
                "form":        None,
                "avg_points":  None,
                "avg_allowed": None,
                "streak":      None,
            },
            "away": {
                "form":        None,
                "avg_points":  None,
                "avg_allowed": None,
                "streak":      None,
            },
        }
