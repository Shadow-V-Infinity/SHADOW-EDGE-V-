from live import get_live_data
from prediction_service import get_predictions
from matchup_service import get_matchup
# etc…

def get_event(event_id):
    data = {}
    data["live"] = get_live_data(event_id)
    data["matchup"] = get_matchup(event_id)
    data["predictions"] = get_predictions(event_id)
    return data
