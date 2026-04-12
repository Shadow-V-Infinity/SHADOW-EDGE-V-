"""
Shadow Edge V∞ — Scraper Termux v3 (Corrected)
Optimisé pour le Radar V6 - Gestion robuste des erreurs JSON
"""

import cloudscraper
import requests
import json
import math
import os
import sys
import time
from datetime import datetime, date

# ── CONFIG ──────────────────────────────────────────────
RAILWAY_URL     = os.getenv("RAILWAY_URL", "https://shadow-edge-v.onrender.com")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
HEADERS_BDL     = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

scraper = cloudscraper.create_scraper()
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
    "Referer":    "https://www.sofascore.com/",
    "Accept":     "application/json",
}

today = date.today().strftime("%Y-%m-%d")
now   = datetime.now()

# ── TRANCHES HORAIRES ───────────────────────────────────
SLOTS = {
    "matin": (8,  14),
    "aprem": (14, 21),
    "soir":  (21, 26),
}

def match_in_slot(timestamp, slot):
    if not timestamp or slot not in SLOTS:
        return True
    h = datetime.fromtimestamp(timestamp).hour
    start, end = SLOTS[slot]
    if end > 24:
        return h >= start or h < (end - 24)
    return start <= h < end

# ── STADES (météo) ──────────────────────────────────────
STADIUMS = {
    "West Ham United": (51.5386, -0.0165), "Arsenal": (51.5549, -0.1084),
    "Brentford": (51.4882, -0.2886), "Burnley": (53.7892, -2.2300),
    "Liverpool": (53.4308, -2.9608), "Brighton & Hove Albion": (50.8618, -0.0834),
    "Wolverhampton": (52.5900, -2.1302), "Bournemouth": (50.7352, -1.8383),
    "Everton": (53.4388, -2.9662), "Fulham": (51.4749, -0.2217),
    "Roma": (41.9340, 12.4547), "Milan": (45.4781, 9.1240),
    "Atalanta": (45.7090, 9.6800), "Juventus": (45.1096, 7.6413),
    "Real Madrid": (40.4531, -3.6883), "FC Barcelona": (41.3809, 2.1228),
    "Sevilla": (37.3840, -5.9705), "Atletico Madrid": (40.4361, -3.5995),
    "Paris FC": (48.8414, 2.2530), "Olympique de Marseille": (43.2697, 5.3958),
    "RC Lens": (50.4328, 2.8242), "Borussia Dortmund": (51.4926, 7.4518),
    "RB Leipzig": (51.3456, 12.3484), "Inter Miami CF": (25.9580, -80.2389),
    "Austin FC": (30.3878, -97.7191), "Vitória": (-12.978, -38.5044),
    "Santos": (-23.999, -46.2985), "Internacional": (-30.065, -51.2324),
}

# ════════════════════════════════════════════════════════
# FONCTIONS COMMUNES (CORRIGÉES)
# ════════════════════════════════════════════════════════

def safe_get(url, retries=3, delay=2):
    """Récupère les données et force le format dictionnaire Python."""
    for attempt in range(retries):
        try:
            r = scraper.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                time.sleep(delay)
                continue
            
            # Tentative de décodage JSON robuste
            try:
                data = r.json()
            except:
                data = json.loads(r.text)
            
            # Si le résultat est encore une string (bug Sofa), on re-parse
            if isinstance(data, str):
                data = json.loads(data)
                
            return data if isinstance(data, dict) else {}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return {}
    return {}

def get_events(sport_key, slot=None):
    try:
        url = f"https://api.sofascore.com/api/v1/sport/{sport_key}/scheduled-events/{today}"
        data = safe_get(url)
        # Sécurisation : si data n'est pas un dictionnaire, .get ne crashera pas
        events = data.get("events", []) if isinstance(data, dict) else []

        upcoming = [
            e for e in events
            if e.get("status", {}).get("type", {}).get("name", "") == "notStarted"
        ]

        if slot and slot in SLOTS:
            upcoming = [e for e in upcoming if match_in_slot(e.get("startTimestamp"), slot)]
            print(f"  ✅ {len(upcoming)} matchs [{slot}] (sur {len(events)} total)")
        else:
            print(f"  ✅ {len(upcoming)} matchs à venir (sur {len(events)} total)")

        return upcoming
    except Exception as e:
        print(f"  ❌ get_events({sport_key}): {e}")
        return []

def get_h2h(event_id):
    data = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/h2h")
    duel = data.get("teamDuel", {})
    hw, aw, d = duel.get("homeWins", 0), duel.get("awayWins", 0), duel.get("draws", 0)
    return {"home_wins": hw, "away_wins": aw, "draws": d, "total": hw+aw+d}

def get_form(team_id):
    try:
        data = safe_get(f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0")
        form = []
        for e in data.get("events", [])[:5]:
            hs = e.get("homeScore", {}).get("current", 0)
            aws = e.get("awayScore", {}).get("current", 0)
            if e.get("homeTeam", {}).get("id") == team_id:
                form.append("W" if hs > aws else ("D" if hs == aws else "L"))
            else:
                form.append("W" if aws > hs else ("D" if hs == aws else "L"))
        return form
    except: return []

def form_score(form):
    pts = {"W": 3, "D": 1, "L": 0}
    return sum(pts.get(r, 0) for r in form) / (len(form) * 3) if form else 0

def get_odds(event_id):
    try:
        data = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all")
        markets = data.get("markets", [])
        ft = next((m for m in markets if m.get("marketName") in ["Full time", "Home/Away"]), None)
        if ft:
            res = {}
            for c in ft.get("choices", []):
                try:
                    num, den = c.get("fractionalValue", "0/1").split("/")
                    res[c["name"]] = round(1 + int(num)/int(den), 2)
                except: res[c["name"]] = None
            return res
    except: pass
    return {}

def get_lineups(event_id):
    data = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/lineups")
    return {
        "home": [p.get("player", {}).get("name") for p in data.get("home", {}).get("players", [])],
        "away": [p.get("player", {}).get("name") for p in data.get("away", {}).get("players", [])]
    }

def get_weather(home_team):
    if not OPENWEATHER_KEY or home_team not in STADIUMS: return None
    coords = STADIUMS[home_team]
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={OPENWEATHER_KEY}&units=metric"
        r = scraper.get(url, timeout=5).json()
        return {"temp": round(r["main"]["temp"], 1), "wind": round(r["wind"]["speed"]*3.6, 1), 
                "rain": r.get("rain", {}).get("1h", 0), "desc": r["weather"][0]["description"]}
    except: return None

def weather_impact(w):
    if not w: return 0, "❓"
    impact, labels = 0, []
    if w["rain"] > 5: impact -= 15; labels.append("🌧️ Forte pluie")
    elif w["rain"] > 1: impact -= 7; labels.append("🌦️ Pluie")
    if w["wind"] > 40: impact -= 10; labels.append("💨 Vent")
    if not labels: impact = 5; labels.append("☀️ OK")
    return impact, " | ".join(labels)

def predict(h2h, home_fs, away_fs):
    total = h2h.get("total", 0)
    w_h2h = 0.5 if total >= 4 else (0.3 if total >= 1 else 0.1)
    w_form = 1 - w_h2h
    h_p = (h2h["home_wins"]/total if total else 0.34) * w_h2h + home_fs * w_form
    a_p = (h2h["away_wins"]/total if total else 0.33) * w_h2h + away_fs * w_form
    d_p = max(1 - h_p - a_p, 0)
    return round(h_p, 3), round(d_p, 3), round(a_p, 3), w_h2h, w_form

def kelly(prob, odd):
    if not prob or not odd or odd <= 1: return 0
    k = ((odd - 1) * prob - (1 - prob)) / (odd - 1)
    return round(max(k, 0) * 0.25, 4)

def predict_score(home_fs, away_fs):
    h_lam, a_lam = 0.5 + home_fs * 2.5, 0.5 + away_fs * 2.5
    scores = {}
    for h in range(5):
        for a in range(5):
            p = ((math.exp(-h_lam)*h_lam**h)/math.factorial(h)) * ((math.exp(-a_lam)*a_lam**a)/math.factorial(a))
            scores[f"{h}-{a}"] = round(p, 3)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

def compute_shadow_score(conf, val, kel, line, w_imp):
    s = conf * 0.3 + min((val or 0)*100, 25) + min(kel*100, 15) + (10 if line else 0) + w_imp
    return round(min(max(s, 0), 100))

# ════════════════════════════════════════════════════════
# ANALYSE PAR SPORT
# ════════════════════════════════════════════════════════

def analyze_team_sport(sport_name, sport_key, slot=None):
    print(f"\n⚽🏒 Analyse {sport_name}...")
    events = get_events(sport_key, slot)
    results = []
    for e in events[:40]:
        eid = e["id"]
        h_name, a_name = e["homeTeam"]["name"], e["awayTeam"]["name"]
        odds = get_odds(eid)
        h2h = get_h2h(eid)
        h_f, a_f = get_form(e["homeTeam"]["id"]), get_form(e["awayTeam"]["id"])
        h_fs, a_fs = form_score(h_f), form_score(a_f)
        
        p_h, p_d, p_a, _, _ = predict(h2h, h_fs, a_fs)
        o1, o2 = odds.get("1"), odds.get("2")
        
        val_h = round(p_h - (1/o1 if o1 else 1), 3)
        val_a = round(p_a - (1/o2 if o2 else 1), 3)
        
        conf = round(min(h2h["total"]*5 + len(h_f)*4 + (20 if o1 else 0), 100))
        w_imp, w_lbl = weather_impact(get_weather(h_name))
        score = compute_shadow_score(conf, max(val_h, val_a), max(kelly(p_h, o1), kelly(p_a, o2)), False, w_imp)
        
        verdict = "⚪ Pas de value"
        if val_h > 0.05: verdict = f"🔥 VALUE {h_name}"
        elif val_a > 0.05: verdict = f"🔥 VALUE {a_name}"

        results.append({
            "sport": sport_name, "home": h_name, "away": a_name, "time": datetime.fromtimestamp(e.get("startTimestamp", 0)).strftime("%H:%M"),
            "odds": odds, "prediction": {"winner": h_name if p_h > p_a else a_name, "shadow_score": score},
            "verdict": verdict, "shadow_score": score
        })
    return results

# ════════════════════════════════════════════════════════
# SYNC & MAIN
# ════════════════════════════════════════════════════════

def send_to_server(sport, results):
    try:
        requests.post(f"{RAILWAY_URL}/ingest/{sport}", json={"date": today, "matches": results}, timeout=15)
        print(f"  📡 /ingest/{sport} → 200")
    except: print(f"  ❌ Serveur injoignable")

def print_top5(results, sport):
    top = sorted([r for r in results if "VALUE" in r["verdict"]], key=lambda x: x["shadow_score"], reverse=True)[:5]
    if not top: print("  Aucun value bet détecté"); return
    print(f"\n  🏆 TOP 5 {sport.upper()} :")
    for i, r in enumerate(top, 1):
        print(f"  #{i} ({r['shadow_score']}/100) {r['home']} vs {r['away']} -> {r['verdict']}")

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    slot = arg if arg in SLOTS else None
    print(f"🚀 Shadow Edge V∞ — {today} | Slot: {slot or 'All'}")
    
    # Ingestion Foot
    if arg in ("all", "football"):
        res = analyze_team_sport("football", "football", slot)
        print_top5(res, "football")
        send_to_server("football", res)

    print(f"\n✅ Terminé à {datetime.now().strftime('%H:%M')} !")
    
