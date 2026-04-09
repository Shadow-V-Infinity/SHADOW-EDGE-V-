# app/services/nba/player_profile_service.py

from app.services.nba.shotchart_service      import ShotChartService
from app.services.nba.tracking_service       import TrackingService
from app.services.nba.pbp_analysis_service   import PbpAnalysisService
from app.services.nba.injury_service         import InjuryService
from app.services.nba.matchup_service        import MatchupService
from app.services.nba.playtype_service       import PlayTypeService
from app.services.nba.props_service          import PropsService
from app.services.nba.player_profile_utils   import (
    build_shotchart_heatmap,
    build_playtype_radar,
    get_player_clips,
)

from nba_api.stats.endpoints import commonplayerinfo, playergamelog


class PlayerProfileService:
    """
    Shadow Edge V∞ — Player Profile Service
    Pack complet : infos, derniers matchs, shotchart, playtypes,
    tracking, props, blessure, clips vidéo.
    """

    def __init__(self):
        self.shotchart  = ShotChartService()
        self.tracking   = TrackingService()
        self.pbp        = PbpAnalysisService()
        self.injuries   = InjuryService()
        self.matchups   = MatchupService()
        self.playtypes  = PlayTypeService()
        self.props      = PropsService()

    # ───────────────────────────────────────────────────────────
    # Infos générales joueur
    # ───────────────────────────────────────────────────────────
    def get_player_info(self, player_id: str) -> dict:
        try:
            info    = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
            row     = info["resultSets"][0]["rowSet"][0]
            headers = info["resultSets"][0]["headers"]
            return {headers[i]: row[i] for i in range(len(headers))}
        except Exception as e:
            print(f"[PlayerProfileService] get_player_info({player_id}) error: {e}")
            return {}

    # ───────────────────────────────────────────────────────────
    # Derniers matchs
    # ───────────────────────────────────────────────────────────
    def get_last_games(self, player_id: str, n: int = 5) -> list:
        try:
            logs    = playergamelog.PlayerGameLog(player_id=player_id).get_dict()
            rows    = logs["resultSets"][0]["rowSet"]
            headers = logs["resultSets"][0]["headers"]
            return [
                {
                    "GAME_DATE": r[headers.index("GAME_DATE")],
                    "MATCHUP":   r[headers.index("MATCHUP")],
                    "PTS":       r[headers.index("PTS")],
                    "REB":       r[headers.index("REB")],
                    "AST":       r[headers.index("AST")],
                    "MIN":       r[headers.index("MIN")],
                }
                for r in rows[:n]
            ]
        except Exception as e:
            print(f"[PlayerProfileService] get_last_games({player_id}) error: {e}")
            return []

    # ───────────────────────────────────────────────────────────
    # Pack complet
    # ───────────────────────────────────────────────────────────
    def get_player_profile(self, player_id: str) -> dict:
        shots     = self.shotchart.get_player_shots(player_id, "2024-25")
        playtypes = self.playtypes.get_player_playtypes(player_id, "2024-25")

        return {
            "info":       self.get_player_info(player_id),
            "last_games": self.get_last_games(player_id),

            # ShotChart
            "shotchart_raw":     shots,
            "shotchart_heatmap": build_shotchart_heatmap(shots),

            # PlayTypes
            "playtypes_raw":   playtypes,
            "playtypes_radar": build_playtype_radar(playtypes) if playtypes else {},

            # Tracking
            "tracking": self.tracking.get_player_tracking(player_id, "2024-25"),

            # Props
            "props": self.props.get_props_by_player(player_id),

            # Injury
            "injury": self.injuries.get_player_injury(player_id),

            # Clips vidéo
            "clips": get_player_clips(self.pbp, player_id),
        }
