# app/services/nba/pbp_analysis_service.py

from typing import Dict, Any, List


class PbpAnalysisService:
    """
    Shadow Edge V∞ — Play-By-Play Analysis
    Détection des runs, courbe de momentum, séquences clutch.
    Source externe optionnelle (sinon fallback propre).
    """

    def __init__(self, pbp_source=None):
        self.pbp = pbp_source

    def get_runs(self, game_id: str) -> List[Dict[str, Any]]:
        """Détecte les runs (ex: 12-0, 8-2…)."""
        if self.pbp:
            try:
                return self.pbp.get_runs(game_id)
            except Exception:
                pass
        return []

    def get_momentum_curve(self, game_id: str) -> List[Dict[str, Any]]:
        """Courbe de momentum / différentiel de score dans le temps."""
        if self.pbp:
            try:
                return self.pbp.get_momentum_curve(game_id)
            except Exception:
                pass
        return []

    def get_clutch_sequences(self, game_id: str) -> List[Dict[str, Any]]:
        """Séquences clutch du match."""
        if self.pbp:
            try:
                return self.pbp.get_clutch_sequences(game_id)
            except Exception:
                pass
        return []

    def get_player_clips(self, player_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Clips vidéo du joueur via PBP + video scraper."""
        if self.pbp:
            try:
                clips = self.pbp.get_player_clips(player_id)
                return clips[:limit]
            except Exception:
                pass
        return []
