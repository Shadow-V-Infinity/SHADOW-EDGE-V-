# app/services/nba/playtype_service.py

import time
from typing import Dict, Any
from nba_api.stats.endpoints import leaguedashteamstats


class PlayTypeService:
    """
    Shadow Edge V∞ — PlayType Service
    Profil offensif équipe : PnR, Iso, Handoff, Spot-Up, Post-Up, Transition.
    """

    def __init__(self, playtype_source=None):
        self.source = playtype_source

    # ───────────────────────────────────────────────────────────
    # Safe NBA API wrapper
    # ───────────────────────────────────────────────────────────
    def _safe_team_stats(self, retries: int = 3, delay: float = 1.0):
        for _ in range(retries):
            try:
                return leaguedashteamstats.LeagueDashTeamStats().get_dict()
            except Exception:
                time.sleep(delay)
        return None

    # ───────────────────────────────────────────────────────────
    # Playtypes joueur (plug-in externe requis)
    # ───────────────────────────────────────────────────────────
    def get_player_playtypes(self, player_id: str, season: str) -> Dict[str, Any]:
        if self.source:
            try:
                return self.source.get_player_playtypes(player_id, season)
            except Exception:
                pass
        return {}

    def get_playtype_efficiency(self, player_id: str, season: str) -> Dict[str, Any]:
        if self.source:
            try:
                return self.source.get_playtype_efficiency(player_id, season)
            except Exception:
                pass
        return {}

    # ───────────────────────────────────────────────────────────
    # Playtypes équipe — calcul Shadow Edge V∞
    # ───────────────────────────────────────────────────────────
    def get_team_playtypes(self, team_name: str) -> Dict[str, Any]:
        if self.source:
            try:
                return self.source.get_team_playtypes(team_name)
            except Exception:
                pass

        stats = self._safe_team_stats()
        if not stats:
            return self._fallback()

        rows    = stats["resultSets"][0]["rowSet"]
        headers = stats["resultSets"][0]["headers"]

        try:
            idx_name = headers.index("TEAM_NAME")
            idx_pace = headers.index("PACE")
            idx_3pa  = headers.index("FG3A")
            idx_fga  = headers.index("FGA")
            idx_ast  = headers.index("AST")
        except ValueError:
            return self._fallback()

        team_row = next((r for r in rows if r[idx_name] == team_name), None)
        if not team_row:
            return self._fallback()

        pace = team_row[idx_pace]
        fga  = team_row[idx_fga]
        fg3a = team_row[idx_3pa]
        ast  = team_row[idx_ast]

        spot_up_freq    = fg3a / fga if fga else 0
        transition_freq = min(max((pace - 95) / 10, 0), 1)
        handoff_freq    = min(ast / 30, 1)
        iso_freq        = 1 - handoff_freq
        post_up_freq    = (1 - spot_up_freq) * (1 - transition_freq)
        pnr_freq        = max(1 - (spot_up_freq + iso_freq + handoff_freq + post_up_freq + transition_freq), 0)

        return {
            "pick_and_roll": {"frequency": round(pnr_freq,        3), "ppp": None},
            "isolation":     {"frequency": round(iso_freq,         3), "ppp": None},
            "handoff":       {"frequency": round(handoff_freq,     3), "ppp": None},
            "spot_up":       {"frequency": round(spot_up_freq,     3), "ppp": None},
            "post_up":       {"frequency": round(post_up_freq,     3), "ppp": None},
            "transition":    {"frequency": round(transition_freq,  3), "ppp": None},
        }

    def _fallback(self) -> Dict[str, Any]:
        keys = ["pick_and_roll", "isolation", "handoff", "spot_up", "post_up", "transition"]
        return {k: {"frequency": None, "ppp": None} for k in keys}
