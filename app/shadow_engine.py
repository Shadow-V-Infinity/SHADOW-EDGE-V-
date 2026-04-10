# shadow_engine.py

import json

# === IMPORT DE TES MODULES EXISTANTS ===
# (on importe seulement ceux qui existent dans ton dossier)
try:
    import live
except:
    live = None

try:
    import prediction_service
except:
    prediction_service = None

try:
    import matchup_service
except:
    matchup_service = None

try:
    import injury_service
except:
    injury_service = None

try:
    import pbp_analysis_service
except:
    pbp_analysis_service = None


# === FONCTION PRINCIPALE ===
def get_event(event_id):
    data = {}

    # LIVE
    if live and hasattr(live, "get_live_data"):
        try:
            data["live"] = live.get_live_data(event_id)
        except Exception as e:
            data["live_error"] = str(e)

    # MATCHUP
    if matchup_service and hasattr(matchup_service, "get_matchup"):
        try:
            data["matchup"] = matchup_service.get_matchup(event_id)
        except Exception as e:
            data["matchup_error"] = str(e)

    # PREDICTIONS
    if prediction_service and hasattr(prediction_service, "get_predictions"):
        try:
            data["predictions"] = prediction_service.get_predictions(event_id)
        except Exception as e:
            data["predictions_error"] = str(e)

    # INJURIES
    if injury_service and hasattr(injury_service, "get_injuries"):
        try:
            data["injuries"] = injury_service.get_injuries(event_id)
        except Exception as e:
            data["injuries_error"] = str(e)

    # PLAY-BY-PLAY ANALYSIS
    if pbp_analysis_service and hasattr(pbp_analysis_service, "analyze_pbp"):
        try:
            data["pbp_analysis"] = pbp_analysis_service.analyze_pbp(event_id)
        except Exception as e:
            data["pbp_error"] = str(e)

    return data
