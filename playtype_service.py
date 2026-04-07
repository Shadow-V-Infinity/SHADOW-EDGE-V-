# sports/nba/services/playtype_service.py

from typing import Dict, Any

class PlayTypeService:
    def __init__(self, playtype_source=None):
        self.source = playtype_source  # wrapper gabrielsalamanca/nba-play-types

    def get_player_playtypes(self, player_id: str, season: str) -> Dict[str, Any]:
        """
        Profil offensif par type d’action (PnR, ISO, Spot-Up, etc.).
        """
        raise NotImplementedError

    def get_playtype_efficiency(self, player_id: str, season: str) -> Dict[str, Any]:
        raise NotImplementedError
