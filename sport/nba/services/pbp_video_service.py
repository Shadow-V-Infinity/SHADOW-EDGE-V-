# sports/nba/services/pbp_video_service.py

from typing import Dict, Any, List

class PbpVideoService:
    def __init__(self, scraper_client=None):
        self.scraper = scraper_client  # wrapper autour du repo alexnobert

    def get_video_clip(self, game_id: str, event_id: str) -> Dict[str, Any]:
        """
        Retourne l'URL (ou chemin) du clip vidéo pour un event.
        """
        raise NotImplementedError

    def get_clutch_clips(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Clips des actions clutch d'un match.
        """
        raise NotImplementedError
