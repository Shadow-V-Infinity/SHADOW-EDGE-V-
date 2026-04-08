# sports/nba/services/trends_service.py

class TrendsService:
    """
    Shadow Edge V∞ — Trends Engine
    Analyse des tendances récentes :
    - Forme
    - Points marqués / encaissés
    - Séries
    - Momentum global
    Pour l'instant : placeholder propre et stable.
    """

    def get_trends(self, game_id):
        """
        Retourne les tendances home/away.
        Placeholder pour éviter les crashs.
        """
        return {
            "home": {
                "form": None,
                "avg_points": None,
                "avg_allowed": None,
                "streak": None,
            },
            "away": {
                "form": None,
                "avg_points": None,
                "avg_allowed": None,
                "streak": None,
            }
        }
