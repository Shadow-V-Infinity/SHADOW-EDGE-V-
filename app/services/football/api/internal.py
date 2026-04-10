from analytics.core_service import CoreService
from visuals.hud import hud_status

core = CoreService()

def health():
    raw = core.health_check()
    return hud_status(raw)
