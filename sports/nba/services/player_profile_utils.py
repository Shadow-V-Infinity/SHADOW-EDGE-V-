# sports/nba/services/player_profile_utils.py

def build_shotchart_heatmap(shots):
    """
    Génère une heatmap ECharts à partir d'une liste de tirs :
    shots = [
        {"x": -5.2, "y": 12.3, "made": 1},
        ...
    ]
    """

    return {
        "tooltip": {"show": True},
        "xAxis": {"min": -25, "max": 25, "show": False},
        "yAxis": {"min": 0, "max": 50, "show": False},
        "series": [
            {
                "type": "heatmap",
                "data": [
                    [s["x"], s["y"], 1 if s.get("made") else 0]
                    for s in shots
                ],
                "pointSize": 12,
                "blurSize": 20,
            }
        ],
        "visualMap": {
            "min": 0,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "5%",
        },
    }


def get_player_clips(pbp_service, player_id, limit=10):
    """
    Retourne les clips vidéo du joueur (via PBP + video scraper)
    pbp_service = instance de PbpAnalysisService
    """

    try:
        clips = pbp_service.get_player_clips(player_id)
        return clips[:limit]
    except Exception:
        return []
