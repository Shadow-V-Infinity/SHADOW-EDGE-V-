# app/services/nba/tracking_service.py

from typing import Dict, Any


class TrackingService:
    """
    Shadow Edge V∞ — Tracking Service
    Vitesse, distance, drives, touches, rebonds contestés…
    """

    def __init__(self, api_client=None):
        self.api = api_client

    def get_player_tracking(self, player_id: str, season: str) -> Dict[str, Any]:
        if self.api:
            try:
                return self.api.get_player_tracking(player_id, season)
            except Exception:
                pass
        return {}

    def get_team_tracking(self, team_id: str, season: str) -> Dict[str, Any]:
        if self.api:
            try:
                return self.api.get_team_tracking(team_id, season)
            except Exception:
                pass
        return {}

    def get_drive_stats(self, player_id: str, season: str) -> Dict[str, Any]:
        if self.api:
            try:
                return self.api.get_drive_stats(player_id, season)
            except Exception:
                pass
        return {}
