from fastapi import APIRouter, Query
from app.services.nba.pre_match_service import ShadowEdgePreMatchService

router = APIRouter()
service = ShadowEdgePreMatchService()

# ---------------------------------------------------------
# 1. Liste des matchs du jour (utilisé par ton frontend)
# ---------------------------------------------------------
@router.get("/games")
def games():
    """
    Retourne la liste des matchs du jour.
    Format attendu par le frontend :
    [
        {
            "game_id": "...",
            "homeTeam": "...",
            "awayTeam": "...",
            "pace": ...,
            "off_rating": ...,
            "def_rating": ...,
            "form": ...
        }
    ]
    """
    return service.get_today_games()


# ---------------------------------------------------------
# 2. Package complet pour un match précis
#    (stats avancées, matchups, tendances, etc.)
# ---------------------------------------------------------
@router.get("/package")
def pre_match_package(
    game_id: str = Query(..., description="ID du match"),
    home: str = Query(..., description="Nom de l'équipe à domicile"),
    away: str = Query(..., description="Nom de l'équipe à l'extérieur"),
):
    """
    Retourne le package complet avant-match pour un match donné.
    """
    return service.get_pre_match_package(game_id, home, away)


# ---------------------------------------------------------
# 3. (OPTIONNEL) Endpoint debug
# ---------------------------------------------------------
@router.get("/debug")
def debug():
    """
    Permet de vérifier que le service fonctionne.
    """
    return {"status": "pre_match_router_ok"}
