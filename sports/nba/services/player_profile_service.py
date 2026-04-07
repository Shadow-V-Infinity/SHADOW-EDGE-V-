# sports/nba/services/player_profile_service.py

from sports.nba.services.shotchart_service import ShotChartService
from sports.nba.services.tracking_service import TrackingService
from sports.nba.services.pbp_analysis_service import PbpAnalysisService
from sports.nba.services.injury_service import InjuryService
from sports.nba.services.matchup_service import MatchupService
from sports.nba.services.playtype_service import PlayTypeService
from sports.nba.services.props_service import PropsService

from sports.nba.services.player_profile_utils import (
    build_shotchart_heatmap,
    build_playtype_radar,
    get_player_clips,
)

from nba_api.stats.endpoints import commonplayerinfo, playergamelog


class PlayerProfileService:
    def __init__(self):
        self.shotchart = ShotChartService()
        self.tracking = TrackingService()
        self.pbp = PbpAnalysisService()
        self.injuries = InjuryService()
        self.matchups = MatchupService()
        self.playtypes = PlayTypeService()
        self.props = PropsService()

    # ---------------------------------------------------------------
    # Infos générales joueur
    # ---------------------------------------------------------------
    def get_player_info(self, player_id):
        try:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
            row = info["resultSets"][0]["rowSet"][0]
            headers = info["resultSets"][0]["headers"]
            return {headers[i]: row[i] for i in range(len(headers))}
        except:
            return {}

    # ---------------------------------------------------------------
    # Derniers matchs
    # ---------------------------------------------------------------
    def get_last_games(self, player_id, n=5):
        try:
            logs = playergamelog.PlayerGameLog(player_id=player_id).get_dict()
            rows = logs["resultSets"][0]["rowSet"]
            headers = logs["resultSets"][0]["headers"]

            return [
                {
                    "GAME_DATE": r[headers.index("GAME_DATE")],
                    "MATCHUP": r[headers.index("MATCHUP")],
                    "PTS": r[headers.index("PTS")],
                    "REB": r[headers.index("REB")],
                    "AST": r[headers.index("AST")],
                    "MIN": r[headers.index("MIN")],
                }
                for r in rows[:n]
            ]
        except:
            return []

    # ---------------------------------------------------------------
    # Pack complet Player Profile
    # ---------------------------------------------------------------
    def get_player_profile(self, player_id):
        shots = self.shotchart.get_player_shots(player_id, "2024-25")
        playtypes = self.playtypes.get_player_playtypes(player_id, "2024-25")

        return {
            "info": self.get_player_info(player_id),
            "last_games": self.get_last_games(player_id),

            # Shotchart
            "shotchart_raw": shots,
            "shotchart_heatmap": build_shotchart_heatmap(shots),

            # Playtypes
            "playtypes_raw": playtypes,
            "playtypes_radar": build_playtype_radar(playtypes),

            # Tracking
            "tracking": self.tracking.get_player_tracking(player_id, "2024-25"),

            # Props
            "props": self.props.get_props_by_player(player_id),

            # Injury
            "injury": self.injuries.get_player_injury(player_id),

            # Clips vidéo
            "clips": get_player_clips(self.pbp, player_id),
        }
