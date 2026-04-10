def hud_status(health_data: dict):
    status = health_data.get("status", "unknown")
    message = health_data.get("data", {})
    
    return f"""
    === SHADOW-EDGE FOOT V∞ — HUD ===
    Status : {status}
    Data   : {message}
    =================================
    """

def hud_status(health_data: dict):
    status = health_data.get("status", "unknown")
    message = health_data.get("data", {})

    return f"""
    === SHADOW-EDGE FOOT V∞ — HUD ===
    Status : {status}
    Data   : {message}
    =================================
    """
