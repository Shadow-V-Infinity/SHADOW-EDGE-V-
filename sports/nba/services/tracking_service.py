# sports/nba/services/tracking_service.py

from typing import Dict, Any

class TrackingService:
    def __init__(self, api_client=None):
        self.api = api_client  # client vers ton module neilp92/nba-tracking

    def get_player_tracking(self, player_id: str, season: str) -> Dict[str, Any]:
        """
        Vitesse, distance, drives, touches, rebonds contestés, etc.
        """
        raise NotImplementedError

    def get_team_tracking(self, team_id: str, season: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_drive_stats(self, player_id: str, season: str) -> Dict[str, Any]:
        raise NotImplementedError
