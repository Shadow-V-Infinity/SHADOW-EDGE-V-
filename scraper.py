"""
Shadow Edge V∞ — Scraper Termux v3
Lance ce script depuis Termux pour analyser tous les sports
et envoyer les résultats vers Render.

Usage:
    python scraper.py              → tous les sports (jour complet)
    python scraper.py football     → foot seulement
    python scraper.py basketball   → basket seulement
    python scraper.py tennis       → tennis seulement
    python scraper.py hockey       → hockey seulement
    python scraper.py rugby        → rugby seulement
    python scraper.py matin        → matchs 8h-14h (tous sports)
    python scraper.py aprem        → matchs 14h-21h (tous sports)
    python scraper.py soir         → matchs 21h-1h30 (tous sports)
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
BALLDONTLIE_KEY  = os.getenv("BALLDONTLIE_API_KEY", "")
HEADERS_BDL      = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")  # X-Auth-Token

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
    "West Ham United":         (51.5386,  -0.0165),
    "Arsenal":                 (51.5549,  -0.1084),
    "Brentford":               (51.4882,  -0.2886),
    "Burnley":                 (53.7892,  -2.2300),
    "Liverpool":               (53.4308,  -2.9608),
    "Brighton & Hove Albion":  (50.8618,  -0.0834),
    "Wolverhampton":           (52.5900,  -2.1302),
    "Bournemouth":             (50.7352,  -1.8383),
    "Everton":                 (53.4388,  -2.9662),
    "Fulham":                  (51.4749,  -0.2217),
    "Roma":                    (41.9340,  12.4547),
    "Milan":                   (45.4781,   9.1240),
    "Atalanta":                (45.7090,   9.6800),
    "Juventus":                (45.1096,   7.6413),
    "Real Madrid":             (40.4531,  -3.6883),
    "FC Barcelona":            (41.3809,   2.1228),
    "Sevilla":                 (37.3840,  -5.9705),
    "Atletico Madrid":         (40.4361,  -3.5995),
    "Paris FC":                (48.8414,   2.2530),
    "Olympique de Marseille":  (43.2697,   5.3958),
    "RC Lens":                 (50.4328,   2.8242),
    "Borussia Dortmund":       (51.4926,   7.4518),
    "RB Leipzig":              (51.3456,  12.3484),
    "Inter Miami CF":          (25.9580, -80.2389),
    "Austin FC":               (30.3878, -97.7191),
    "Vitória":                 (-12.978, -38.5044),
    "Santos":                  (-23.999, -46.2985),
    "Internacional":           (-30.065, -51.2324),
}

# ════════════════════════════════════════════════════════
# FONCTIONS COMMUNES
# ════════════════════════════════════════════════════════

def safe_get(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            r  = scraper.get(url, headers=headers, timeout=10)
            ct = r.headers.get("Content-Type", "")
            if "json" not in ct:
                if attempt < retries - 1:
                    print(f"  ⚠️  Pas du JSON (CT={ct}) — retry {attempt+1}...")
                    time.sleep(delay)
                    continue
                return {}
            data = r.json()
            # SofaScore renvoie parfois une string ou liste au lieu d'un dict
            if not isinstance(data, dict):
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return {}
            return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"  ⚠️  safe_get échec ({url[-40:]}): {e}")
    return {}

def get_events(sport_key, slot=None):
    try:
        url    = f"https://api.sofascore.com/api/v1/sport/{sport_key}/scheduled-events/{today}"
        data   = safe_get(url)
        events = data.get("events", [])

        # FIX : filtre strict sur la date du jour + status notStarted uniquement
        today_start = int(datetime.strptime(today, "%Y-%m-%d").timestamp())
        today_end   = today_start + 86400  # +24h

        upcoming = [
            e for e in events
            if e.get("status", {}).get("type", {}).get("name", "") == "notStarted"
            and today_start <= (e.get("startTimestamp") or 0) < today_end
        ]

        if slot and slot in SLOTS:
            upcoming = [e for e in upcoming if match_in_slot(e.get("startTimestamp"), slot)]
            print(f"  ✅ {len(upcoming)} matchs [{slot}] (sur {len(events)} total)")
        else:
            print(f"  ✅ {len(upcoming)} matchs à venir aujourd'hui (sur {len(events)} total)")

        return upcoming
    except Exception as e:
        print(f"  ❌ get_events({sport_key}): {e}")
        return []

def get_h2h(event_id):
    try:
        data = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/h2h")
        duel = data.get("teamDuel", {})
        hw   = duel.get("homeWins", 0)
        aw   = duel.get("awayWins", 0)
        d    = duel.get("draws",    0)
        return {"home_wins": hw, "away_wins": aw, "draws": d, "total": hw+aw+d}
    except:
        return {"home_wins": 0, "away_wins": 0, "draws": 0, "total": 0}

def get_form(team_id):
    try:
        data = safe_get(f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0")
        form = []
        for e in data.get("events", [])[:5]:
            hs  = e.get("homeScore", {}).get("current", 0)
            aws = e.get("awayScore", {}).get("current", 0)
            ht  = e.get("homeTeam", {}).get("id")
            if ht == team_id:
                form.append("W" if hs > aws else ("D" if hs == aws else "L"))
            else:
                form.append("W" if aws > hs else ("D" if hs == aws else "L"))
        return form
    except:
        return []

def form_score(form):
    pts = {"W": 3, "D": 1, "L": 0}
    if not form: return 0
    return sum(pts.get(r, 0) for r in form) / (len(form) * 3)


# ════════════════════════════════════════════════════════
# FOOTBALL DATA — Cotes officielles (X-Auth-Token)
# ════════════════════════════════════════════════════════

# Mapping ligue → competition ID Football Data
FOOTBALL_DATA_LEAGUES = {
    "Premier League":    "PL",
    "La Liga":           "PD",
    "Bundesliga":        "BL1",
    "Ligue 1":           "FL1",
    "Serie A":           "SA",
    "Champions League":  "CL",
}

# Cache pour éviter de dépasser 10 appels/min
_fd_cache = {}

def get_football_data_matches():
    """Récupère tous les matchs du jour via Football Data API."""
    if not FOOTBALL_DATA_KEY:
        return {}
    if _fd_cache.get("matches"):
        return _fd_cache["matches"]

    fd_headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matches_by_teams = {}

    for league_name, comp_id in FOOTBALL_DATA_LEAGUES.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_id}/matches"
            r   = requests.get(url, headers=fd_headers, params={"dateFrom": today, "dateTo": today}, timeout=10)
            if r.status_code != 200:
                print(f"  ⚠️  Football Data {league_name}: {r.status_code}")
                continue
            data    = r.json()
            matchs  = data.get("matches", [])
            for m in matchs:
                home = m.get("homeTeam", {}).get("name", "")
                away = m.get("awayTeam", {}).get("name", "")
                odds = m.get("odds", {})
                if home and away and odds:
                    key = f"{home}_{away}"
                    matches_by_teams[key] = {
                        "league":  league_name,
                        "home":    home,
                        "away":    away,
                        "odds_fd": {
                            "1": odds.get("homeWin"),
                            "X": odds.get("draw"),
                            "2": odds.get("awayWin"),
                        }
                    }
            print(f"  ✅ Football Data {league_name}: {len(matchs)} matchs")
            time.sleep(6)  # Respecter 10 appels/min
        except Exception as e:
            print(f"  ❌ Football Data {league_name}: {e}")

    _fd_cache["matches"] = matches_by_teams
    return matches_by_teams

def get_odds_football_data(home, away):
    """Récupère les cotes Football Data pour un match donné."""
    fd_matches = get_football_data_matches()
    # Cherche exact d'abord
    key = f"{home}_{away}"
    if key in fd_matches:
        return fd_matches[key]["odds_fd"]
    # Cherche partiel (noms légèrement différents)
    for k, v in fd_matches.items():
        if home[:6].lower() in k.lower() and away[:6].lower() in k.lower():
            return v["odds_fd"]
    return {}

def get_odds(event_id, home=None, away=None):
    """Cotes SofaScore en priorité, Football Data en fallback."""
    # 1. SofaScore
    try:
        data    = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all")
        markets = data.get("markets", [])
        VALID   = ["Full time", "Home/Away", "1X2", "Match Winner", "Full Time Result"]
        ft = next((m for m in markets if m.get("marketName") in VALID), None)
        if ft:
            result = {}
            for c in ft.get("choices", []):
                name = c.get("name", "")
                # Essayer decimalValue d'abord, puis fractionalValue
                dec = c.get("decimalValue")
                if not dec:
                    frac = c.get("fractionalValue", "")
                    try:
                        num, den = frac.split("/")
                        dec = round(1 + int(num)/int(den), 2)
                    except:
                        dec = None
                if name in ["1", "Home", "W1"]:   result["1"] = dec
                elif name in ["2", "Away", "W2"]: result["2"] = dec
                elif name in ["X", "Draw"]:       result["X"] = dec
            if result.get("1") or result.get("2"):
                return result
    except:
        pass

    # 2. Fallback Football Data si on a les noms des équipes
    if home and away and FOOTBALL_DATA_KEY:
        fd_odds = get_odds_football_data(home, away)
        if fd_odds.get("1") or fd_odds.get("2"):
            print(f"    💡 Cotes Football Data utilisées ({home} vs {away})")
            return fd_odds

    return {}

def get_lineups(event_id):
    try:
        data = safe_get(f"https://api.sofascore.com/api/v1/event/{event_id}/lineups")
        return {
            "home": [p.get("player", {}).get("name") for p in data.get("home", {}).get("players", [])],
            "away": [p.get("player", {}).get("name") for p in data.get("away", {}).get("players", [])]
        }
    except:
        return {"home": [], "away": []}

def get_weather(home_team):
    if not OPENWEATHER_KEY:
        return None
    coords = STADIUMS.get(home_team)
    if not coords:
        return None
    try:
        url = (f"https://api.openweathermap.org/data/2.5/weather"
               f"?lat={coords[0]}&lon={coords[1]}"
               f"&appid={OPENWEATHER_KEY}&units=metric")
        r = scraper.get(url, timeout=5).json()
        return {
            "temp": round(r.get("main", {}).get("temp", 15), 1),
            "wind": round(r.get("wind", {}).get("speed", 0) * 3.6, 1),
            "rain": round(r.get("rain", {}).get("1h", 0), 2),
            "desc": r.get("weather", [{}])[0].get("description", ""),
        }
    except:
        return None

def weather_impact(w):
    if not w: return 0, "❓"
    impact, labels = 0, []
    if w["rain"] > 5:    impact -= 15; labels.append("🌧️ Forte pluie")
    elif w["rain"] > 1:  impact -= 7;  labels.append("🌦️ Pluie légère")
    if w["wind"] > 50:   impact -= 12; labels.append("💨 Vent violent")
    elif w["wind"] > 30: impact -= 5;  labels.append("💨 Vent modéré")
    if w["temp"] > 32:   impact -= 8;  labels.append("🥵 Chaleur")
    elif w["temp"] < 2:  impact -= 5;  labels.append("❄️ Froid")
    else:                impact += 5;  labels.append("☀️ Conditions favorables")
    return impact, " | ".join(labels)

def predict(h2h, home_fs, away_fs):
    total = h2h.get("total", 0)
    if   total >= 8: w_h2h, w_form = 0.65, 0.35
    elif total >= 4: w_h2h, w_form = 0.50, 0.50
    elif total >= 1: w_h2h, w_form = 0.30, 0.70
    else:            w_h2h, w_form = 0.10, 0.90

    h2h_home = h2h["home_wins"] / total if total else 0.34
    h2h_away = h2h["away_wins"] / total if total else 0.33

    pred_home = round((h2h_home * w_h2h) + (home_fs * w_form), 3)
    pred_away = round((h2h_away * w_h2h) + (away_fs * w_form), 3)
    pred_draw = round(max(1 - pred_home - pred_away, 0), 3)
    return pred_home, pred_draw, pred_away, w_h2h, w_form

def kelly(prob, odd):
    if not prob or not odd or odd <= 1: return 0
    b = odd - 1
    q = 1 - prob
    k = (b * prob - q) / b
    return round(max(k, 0) * 0.25, 4)

def poisson_prob(lam, k):
    return (math.exp(-lam) * lam**k) / math.factorial(k)

def predict_score(home_fs, away_fs):
    home_lam = round(0.5 + home_fs * 2.5, 2)
    away_lam = round(0.5 + away_fs * 2.5, 2)
    scores   = {}
    for h in range(6):
        for a in range(6):
            p = poisson_prob(home_lam, h) * poisson_prob(away_lam, a)
            scores[f"{h}-{a}"] = round(p, 4)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

def compute_shadow_score(confidence, best_value, best_kelly, has_lineup, w_impact):
    score  = confidence * 0.30
    score += min((best_value or 0) * 100, 25)
    score += min(best_kelly * 100, 15)
    if has_lineup: score += 10
    score += w_impact
    return round(min(max(score, 0), 100))

def get_trend(form_list):
    if len(form_list) < 3: return "❓"
    pts = {"W": 3, "D": 1, "L": 0}
    recent = sum(pts.get(r, 0) for r in form_list[:2]) / 2
    older  = sum(pts.get(r, 0) for r in form_list[2:]) / max(len(form_list[2:]), 1)
    if   recent > older + 0.5: return "📈 En hausse"
    elif recent < older - 0.5: return "📉 En baisse"
    else:                      return "➡️  Stable"

# ════════════════════════════════════════════════════════
# ANALYSE SPORTS D'ÉQUIPES
# ════════════════════════════════════════════════════════

def analyze_team_sport(sport_name, sport_key, slot=None):
    print(f"\n⚽🏒🏉 Analyse {sport_name}...")
    events  = get_events(sport_key, slot)
    results = []

    for event in events[:50]:
        home     = event.get("homeTeam", {}).get("name", "?")
        away     = event.get("awayTeam", {}).get("name", "?")
        event_id = event.get("id")
        home_id  = event.get("homeTeam", {}).get("id")
        away_id  = event.get("awayTeam", {}).get("id")
        ts       = event.get("startTimestamp", 0)
        match_time = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?"

        odds      = get_odds(event_id, home, away)
        lineups   = get_lineups(event_id)
        h2h       = get_h2h(event_id)
        home_form = get_form(home_id)
        away_form = get_form(away_id)
        weather   = get_weather(home)

        home_fs = form_score(home_form)
        away_fs = form_score(away_form)

        pred_home, pred_draw, pred_away, w_h2h, w_form = predict(h2h, home_fs, away_fs)

        odd_1 = odds.get("1")
        odd_x = odds.get("X")
        odd_2 = odds.get("2")

        ip_home    = round(1/odd_1, 3) if odd_1 else None
        ip_away    = round(1/odd_2, 3) if odd_2 else None
        value_home = round(pred_home - ip_home, 3) if ip_home else None
        value_away = round(pred_away - ip_away, 3) if ip_away else None
        best_value = max(value_home or 0, value_away or 0)
        best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

        if   pred_home > pred_away and pred_home > pred_draw: winner = f"🏠 {home}"
        elif pred_away > pred_home and pred_away > pred_draw: winner = f"✈️  {away}"
        else:                                                  winner = "🤝 Match Nul"

        h2h_conf   = min(h2h["total"] / 10 * 40, 40)
        form_conf  = min((len(home_form) + len(away_form)) / 10 * 40, 40)
        odds_conf  = 20 if odd_1 else 0
        confidence = round(h2h_conf + form_conf + odds_conf)

        w_impact, w_label = weather_impact(weather)
        has_lineup = bool(lineups["home"] and lineups["away"])
        score      = compute_shadow_score(confidence, best_value, best_kelly, has_lineup, w_impact)

        goals_exp   = round((0.5 + home_fs * 2.5) + (0.5 + away_fs * 2.5), 2)
        over_under  = "⬆️ OVER 2.5" if goals_exp > 2.5 else "⬇️ UNDER 2.5"
        top3_scores = predict_score(home_fs, away_fs)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        results.append({
            "sport":      sport_name,
            "home":       home,
            "away":       away,
            "event_id":   event_id,
            "time":       match_time,
            "odds":       {"1": odd_1, "X": odd_x, "2": odd_2},
            "lineups":    lineups,
            "h2h":        h2h,
            "form": {
                "home":       home_form,
                "away":       away_form,
                "home_score": home_fs,
                "away_score": away_fs,
                "home_trend": get_trend(home_form),
                "away_trend": get_trend(away_form),
            },
            "weather":       weather,
            "weather_label": w_label,
            "prediction": {
                "home_prob":      pred_home,
                "draw_prob":      pred_draw,
                "away_prob":      pred_away,
                "winner":         winner,
                "weights":        {"h2h": w_h2h, "form": w_form},
                "confidence":     confidence,
                "goals_expected": goals_exp,
                "over_under":     over_under,
                "top3_scores":    top3_scores,
            },
            "value":        {"home": value_home, "away": value_away},
            "kelly":        {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
            "verdict":      verdict,
            "shadow_score": score,
        })

    return results

# ════════════════════════════════════════════════════════
# ANALYSE TENNIS
# ════════════════════════════════════════════════════════

def analyze_tennis(slot=None):
    print(f"\n🎾 Analyse Tennis...")
    events  = get_events("tennis", slot)
    results = []

    for event in events[:50]:
        home     = event.get("homeTeam", {}).get("name", "?")
        away     = event.get("awayTeam", {}).get("name", "?")
        event_id = event.get("id")
        home_id  = event.get("homeTeam", {}).get("id")
        away_id  = event.get("awayTeam", {}).get("id")
        ts       = event.get("startTimestamp", 0)
        match_time = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?"

        odds      = get_odds(event_id, home, away)
        h2h       = get_h2h(event_id)
        home_form = get_form(home_id)
        away_form = get_form(away_id)

        home_fs = form_score(home_form)
        away_fs = form_score(away_form)

        pred_home, _, pred_away, w_h2h, w_form = predict(h2h, home_fs, away_fs)

        winner = f"🎾 {home}" if pred_home > pred_away else f"🎾 {away}"

        odd_1 = odds.get("1")
        odd_2 = odds.get("2")

        ip_home    = round(1/odd_1, 3) if odd_1 else None
        ip_away    = round(1/odd_2, 3) if odd_2 else None
        value_home = round(pred_home - ip_home, 3) if ip_home else None
        value_away = round(pred_away - ip_away, 3) if ip_away else None
        best_value = max(value_home or 0, value_away or 0)
        best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

        h2h_conf   = min(h2h["total"] / 10 * 40, 40)
        form_conf  = min((len(home_form) + len(away_form)) / 10 * 40, 40)
        odds_conf  = 20 if odd_1 else 0
        confidence = round(h2h_conf + form_conf + odds_conf)
        score      = compute_shadow_score(confidence, best_value, best_kelly, False, 0)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE {home} ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE {away} ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        results.append({
            "sport":    "tennis",
            "home":     home,
            "away":     away,
            "event_id": event_id,
            "time":     match_time,
            "odds":     {"1": odd_1, "2": odd_2},
            "h2h":      h2h,
            "form": {
                "home":       home_form,
                "away":       away_form,
                "home_score": home_fs,
                "away_score": away_fs,
                "home_trend": get_trend(home_form),
                "away_trend": get_trend(away_form),
            },
            "prediction": {
                "home_prob":  pred_home,
                "away_prob":  pred_away,
                "winner":     winner,
                "confidence": confidence,
            },
            "value":        {"home": value_home, "away": value_away},
            "kelly":        {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
            "verdict":      verdict,
            "shadow_score": score,
        })

    return results

# ════════════════════════════════════════════════════════
# ENVOI + AFFICHAGE
# ════════════════════════════════════════════════════════

def wake_server():
    try:
        r = requests.get(f"{RAILWAY_URL}/api", timeout=10)
        print(f"☀️  Render réveillé → {r.status_code}")
        time.sleep(2)
    except:
        pass

def send_to_server(sport, results):
    try:
        r = requests.post(
            f"{RAILWAY_URL}/ingest/{sport}",
            json={"date": today, "matches": results},
            timeout=20
        )
        print(f"  📡 /ingest/{sport} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ Erreur {sport}: {e}")

def print_top5(results, sport):
    top5 = sorted(
        [r for r in results if r.get("verdict", "") != "⚪ Pas de value"],
        key=lambda x: x.get("shadow_score", 0),
        reverse=True
    )[:5]

    if not top5:
        print(f"  Aucun value bet détecté")
        return

    print(f"\n  🏆 TOP 5 {sport.upper()} :")
    for i, r in enumerate(top5, 1):
        pred  = r.get("prediction", {})
        odds  = r.get("odds", {})
        score = r.get("shadow_score", 0)
        t     = r.get("time", "?")
        print(f"  #{i} 😈 ({score}/100) [{t}] {r['home']} vs {r['away']}")
        print(f"     → {pred.get('winner', '?')}")
        print(f"     Cotes: 1:{odds.get('1')} 2:{odds.get('2')}")
        print(f"     {r.get('verdict', '')}")

# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

if __name__ == "__main__":

    arg    = sys.argv[1] if len(sys.argv) > 1 else "all"
    slot   = arg if arg in SLOTS else None
    target = "all" if arg in SLOTS else arg

    print(f"🚀 Shadow Edge V∞ — {today} {now.strftime('%H:%M')}")
    print(f"🎯 Sport: {target} | Tranche: {slot or 'toute la journée'}")
    print(f"📡 Render: {RAILWAY_URL}")
    print("=" * 50)

    wake_server()

    if target in ("all", "football"):
        r = analyze_team_sport("football", "football", slot)
        print_top5(r, "football")
        send_to_server("football", r)

    if target in ("all", "basketball"):
        r = analyze_team_sport("basketball", "basketball", slot)
        print_top5(r, "basketball")
        send_to_server("basketball", r)

    if target in ("all", "tennis"):
        r = analyze_tennis(slot)
        print_top5(r, "tennis")
        send_to_server("tennis", r)

    if target in ("all", "hockey"):
        r = analyze_team_sport("hockey", "ice-hockey", slot)
        print_top5(r, "hockey")
        send_to_server("hockey", r)

    if target in ("all", "rugby"):
        r = analyze_team_sport("rugby", "rugby", slot)
        print_top5(r, "rugby")
        send_to_server("rugby", r)

    print(f"\n✅ Shadow Edge V∞ terminé — {now.strftime('%H:%M')} !")
