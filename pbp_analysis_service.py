# sports/nba/services/pbp_analysis_service.py

from typing import Dict, Any, List

class PbpAnalysisService:
    def __init__(self, pbp_source=None):
        self.pbp = pbp_source  # accès aux données PBP

    def get_runs(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Détecte les runs (12-0, 8-2, etc.).
        """
        raise NotImplementedError

    def get_momentum_curve(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Courbe de momentum / différentiel de score.
        """
        raise NotImplementedError

    def get_clutch_sequences(self, game_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
