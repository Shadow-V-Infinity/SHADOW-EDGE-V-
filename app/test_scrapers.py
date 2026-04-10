import time
import json
import requests
import importlib

EVENT_ID = 12835540  # ID réel

# -----------------------------
# 1) Test the-93 (via URL)
# -----------------------------
def test_the93(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}"
    start = time.time()
    r = requests.get(url)
    return {
        "name": "the-93 (API direct)",
        "success": r.status_code == 200,
        "time": round(time.time() - start, 3),
        "keys": list(r.json().keys()) if r.status_code == 200 else None
    }

# -----------------------------
# 2) Test B-S-M (via URL)
# -----------------------------
def test_bsm(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/statistics"
    start = time.time()
    r = requests.get(url)
    return {
        "name": "B-S-M (stats direct)",
        "success": r.status_code == 200,
        "time": round(time.time() - start, 3),
        "keys": list(r.json().keys()) if r.status_code == 200 else None
    }

# -----------------------------
# 3) Test ScraperFC (via URL)
# -----------------------------
def test_scraperfc(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/graph"
    start = time.time()
    r = requests.get(url)
    return {
        "name": "ScraperFC (graph direct)",
        "success": r.status_code == 200,
        "time": round(time.time() - start, 3),
        "keys": list(r.json().keys()) if r.status_code == 200 else None
    }

# -----------------------------
# 4) Test TON moteur Shadow-Edge
# -----------------------------
def test_shadowedge(event_id):
    try:
        engine = importlib.import_module("engine")  # ton fichier engine.py
        start = time.time()
        data = engine.get_full_event(event_id)
        return {
            "name": "Shadow-Edge V∞",
            "success": True,
            "time": round(time.time() - start, 3),
            "keys": list(data.keys()),
            "depth": len(json.dumps(data))
        }
    except Exception as e:
        return {"name": "Shadow-Edge V∞", "success": False, "error": str(e)}

# -----------------------------
# RUN ALL TESTS
# -----------------------------
if __name__ == "__main__":
    tests = [
        test_the93(EVENT_ID),
        test_bsm(EVENT_ID),
        test_scraperfc(EVENT_ID),
        test_shadowedge(EVENT_ID)
    ]

    print("\n===== COMPARAISON DES 4 SCRAPERS + TON MOTEUR =====\n")
    for t in tests:
        print(json.dumps(t, indent=4))
