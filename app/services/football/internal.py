from ..analytics.core_service import CoreService

core = CoreService()

def health():
    return core.health_check()
