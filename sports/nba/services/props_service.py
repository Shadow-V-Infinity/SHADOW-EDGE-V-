# sports/nba/services/props_service.py

from typing import List, Dict, Any


class PropsService:
    """
    Shadow Edge V∞ — Props Engine
    - Récupère les props d’un match
    - Peut utiliser un scraper externe (optionnel)
    - Fournit un fallback propre si rien n’est disponible
    """

    def __init__(self, props_scraper=None):
        self.scraper = props_scraper  # futur scraper externe

    # ---------------------------------------------------------
    # 1) PROPS PAR MATCH
    # ---------------------------------------------------------
    def get_player_props(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Retourne toutes les props d’un match.
        Si un scraper est branché → utilise le scraper.
        Sinon → renvoie un placeholder propre.
        """

        # Si un scraper externe est branché
        if self.scraper:
            try:
                return self.scraper.get_props(game_id)
            except Exception:
                pass  # fallback

        # Placeholder propre
        return [
            {
                "player": None,
                "market": None,
                "line": None,
                "odds": None,
                "book": None,
                "value": None,
            }
        ]

    # ---------------------------------------------------------
    # 2) PROPS PAR JOUEUR
    # ---------------------------------------------------------
    def get_props_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        """
        Retourne les props d’un joueur.
        """
        if self.scraper:
            try:
                return self.scraper.get_player_props(player_id)
            except Exception:
                pass

        return []

    # ---------------------------------------------------------
    # 3) VALUE BETS (placeholder)
    # ---------------------------------------------------------
    def get_props_value(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Détection de value bets sur les props.
        Pour l’instant : placeholder propre.
        """
        return []
