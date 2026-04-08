# sports/nba/services/playtype_service.py

from typing import Dict, Any
from nba_api.stats.endpoints import leaguedashteamstats
import time

class PlayTypeService:
    def __init__(self, playtype_source=None):
        self.source = playtype_source

    # ---------------------------------------------------------
    # 🔥 SAFE NBA API WRAPPER (évite les crashs Render)
    # ---------------------------------------------------------
    def _safe_team_stats(self, retries=3, delay=1.0):
        for _ in range(retries):
            try:
                return leaguedashteamstats.LeagueDashTeamStats().get_dict()
            except Exception:
                time.sleep(delay)
        return None

    # ---------------------------------------------------------
    # 🔥 PLAYTYPES JOUEUR (pas encore implémenté)
    # ---------------------------------------------------------
    def get_player_playtypes(self, player_id: str, season: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_playtype_efficiency(self, player_id: str, season: str) -> Dict[str, Any]:
        raise NotImplementedError

    # ---------------------------------------------------------
    # 🔥 PLAYTYPES ÉQUIPE — VERSION RÉALISTE SHADOW EDGE V∞
    # ---------------------------------------------------------
    def get_team_playtypes(self, team_name: str) -> Dict[str, Any]:
        """
        Génère un profil de playtypes d'équipe basé sur :
        - Pace (transition)
        - 3PA rate (spot-up)
        - AST% (handoff / mouvement)
        - Usage intérieur (post-up)
        - Isolation approximée via AST% inverse
        - Pick & Roll via ratio drives / assists
        """

        # Si une source externe existe
        if self.source:
            try:
                return self.source.get_team_playtypes(team_name)
            except Exception:
                pass

        # -----------------------------
        # 1) Récupération stats NBA API
        # -----------------------------
        stats = self._safe_team_stats()
        if not stats:
            return self._fallback()

        rows = stats["resultSets"][0]["rowSet"]
        headers = stats["resultSets"][0]["headers"]

        try:
            idx_name = headers.index("TEAM_NAME")
            idx_pace = headers.index("PACE")
            idx_3pa = headers.index("FG3A")
            idx_fga = headers.index("FGA")
            idx_ast = headers.index("AST")
        except ValueError:
            return self._fallback()

        # Trouver l'équipe
        team_row = next((r for r in rows if r[idx_name] == team_name), None)
        if not team_row:
            return self._fallback()

        pace = team_row[idx_pace]
        fga = team_row[idx_fga]
        fg3a = team_row[idx_3pa]
        ast = team_row[idx_ast]

        # -----------------------------
        # 2) Calculs Shadow Edge V∞
        # -----------------------------

        # Spot-up = volume de 3pts
        spot_up_freq = fg3a / fga if fga else 0

        # Transition = pace normalisé
        transition_freq = min(max((pace - 95) / 10, 0), 1)

        # Handoff = AST% (plus de passes = plus de mouvement)
        handoff_freq = min(ast / 30, 1)

        # Isolation = inverse du mouvement
        iso_freq = 1 - handoff_freq

        # Post-up = faible 3PA + faible pace
        post_up_freq = (1 - spot_up_freq) * (1 - transition_freq)

        # Pick & Roll = ce qui reste
        pnr_freq = max(1 - (spot_up_freq + iso_freq + handoff_freq + post_up_freq + transition_freq), 0)

        # -----------------------------
        # 3) Construction du profil
        # -----------------------------
        return {
            "pick_and_roll": {
                "frequency": round(pnr_freq, 3),
                "ppp": None,
            },
            "isolation": {
                "frequency": round(iso_freq, 3),
                "ppp": None,
            },
            "handoff": {
                "frequency": round(handoff_freq, 3),
                "ppp": None,
            },
            "spot_up": {
                "frequency": round(spot_up_freq, 3),
                "ppp": None,
            },
            "post_up": {
                "frequency": round(post_up_freq, 3),
                "ppp": None,
            },
            "transition": {
                "frequency": round(transition_freq, 3),
                "ppp": None,
            },
        }

    # ---------------------------------------------------------
    # 🔥 Fallback si NBA API down
    # ---------------------------------------------------------
    def _fallback(self):
        return {
            "pick_and_roll": {"frequency": None, "ppp": None},
            "isolation": {"frequency": None, "ppp": None},
            "handoff": {"frequency": None, "ppp": None},
            "spot_up": {"frequency": None, "ppp": None},
            "post_up": {"frequency": None, "ppp": None},
            "transition": {"frequency": None, "ppp": None},
        }
