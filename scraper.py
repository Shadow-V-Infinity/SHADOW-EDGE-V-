"""
Shadow Edge V∞ — Scraper Termux
Lance ce script depuis Termux pour analyser tous les sports
et envoyer les résultats vers Railway.

Usage:
    python scraper.py              → tous les sports
    python scraper.py football     → foot seulement
    python scraper.py basketball   → basket seulement
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
RAILWAY_URL       = os.getenv("RAILWAY_URL", "https://shadow-edge-v.onrender.com")
OPENWEATHER_KEY   = os.getenv("OPENWEATHER_KEY", "")
BALLDONTLIE_KEY   = os.getenv("BALLDONTLIE_API_KEY", "")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")
HEADERS_BDL       = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_WEB  = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba"
BDL_BASE  = "https://api.balldontlie.io/v1"

scraper = cloudscraper.create_scraper()
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer":    "https://www.sofascore.com/"
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

# ── MAPPING ESPN → BallDontLie ──────────────────────────
NBA_TEAMS = {
    "Boston Celtics":         "Celtics",
    "Cleveland Cavaliers":    "Cavaliers",
    "Indiana Pacers":         "Pacers",
    "Miami Heat":             "Heat",
    "New York Knicks":        "Knicks",
    "Philadelphia 76ers":     "76ers",
    "Toronto Raptors":        "Raptors",
    "Brooklyn Nets":          "Nets",
    "Charlotte Hornets":      "Hornets",
    "Atlanta Hawks":          "Hawks",
    "Chicago Bulls":          "Bulls",
    "Dallas Mavericks":       "Mavericks",
    "Houston Rockets":        "Rockets",
    "Memphis Grizzlies":      "Grizzlies",
    "Minnesota Timberwolves": "Timberwolves",
    "Oklahoma City Thunder":  "Thunder",
    "Phoenix Suns":           "Suns",
    "San Antonio Spurs":      "Spurs",
    "Denver Nuggets":         "Nuggets",
    "Los Angeles Lakers":     "Lakers",
    "LA Clippers":            "Clippers",
    "Golden State Warriors":  "Warriors",
    "Portland Trail Blazers": "Trail Blazers",
    "Sacramento Kings":       "Kings",
    "Utah Jazz":              "Jazz",
    "New Orleans Pelicans":   "Pelicans",
    "Washington Wizards":     "Wizards",
    "Orlando Magic":          "Magic",
    "Milwaukee Bucks":        "Bucks",
    "Detroit Pistons":        "Pistons",
}


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
    "VfL Wolfsburg":           (52.4340,  10.8032),
    "FC St. Pauli":            (53.5547,   9.9682),
    "Inter Miami CF":          (25.9580, -80.2389),
    "Austin FC":               (30.3878, -97.7191),
    "CF Montréal":             (45.4626, -73.6749),
    "Portland Timbers":        (45.5215,-122.6917),
    "Vitória":                 (-12.978, -38.5044),
    "Santos":                  (-23.999, -46.2985),
    "Internacional":           (-30.065, -51.2324),
}

# ════════════════════════════════════════════════════════
# FONCTIONS COMMUNES
# ════════════════════════════════════════════════════════

def get_events(sport_key):
    """Récupère uniquement les matchs à venir aujourd'hui."""
    try:
        url    = f"https://api.sofascore.com/api/v1/sport/{sport_key}/scheduled-events/{today}"
        data   = scraper.get(url, headers=headers, timeout=10).json()
        events = data.get("events", [])

        # Filtrer uniquement les matchs pas encore commencés
        filtered = [
            e for e in events
            if e.get("status", {}).get("type", {}).get("name", "") == "notStarted"
        ]

        print(f"  ✅ {len(filtered)} matchs à venir (sur {len(events)} total)")
        return filtered
    except Exception as e:
        print(f"  ❌ get_events({sport_key}): {e}")
        return []

def get_h2h(event_id):
    try:
        url  = f"https://api.sofascore.com/api/v1/event/{event_id}/h2h"
        data = scraper.get(url, headers=headers, timeout=5).json()
        duel = data.get("teamDuel", {})
        hw   = duel.get("homeWins", 0)
        aw   = duel.get("awayWins", 0)
        d    = duel.get("draws",    0)
        return {"home_wins": hw, "away_wins": aw, "draws": d, "total": hw+aw+d}
    except:
        return {"home_wins": 0, "away_wins": 0, "draws": 0, "total": 0}

def get_form(team_id):
    try:
        url  = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"
        data = scraper.get(url, headers=headers, timeout=5).json()
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
    if not form:
        return 0
    return sum(pts.get(r, 0) for r in form) / (len(form) * 3)

def get_odds(event_id):
    try:
        url  = f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all"
        data = scraper.get(url, headers=headers, timeout=5).json()
        markets = data.get("markets", [])
        ft = next((m for m in markets if m.get("marketName") in ["Full time", "Home/Away"]), None)
        if ft:
            choices = ft.get("choices", [])
            result  = {}
            for c in choices:
                frac = c.get("fractionalValue", "")
                try:
                    num, den = frac.split("/")
                    dec = round(1 + int(num)/int(den), 2)
                except:
                    dec = None
                result[c["name"]] = dec
            return result
    except:
        pass
    return {}

def get_lineups(event_id):
    try:
        url  = f"https://api.sofascore.com/api/v1/event/{event_id}/lineups"
        data = scraper.get(url, headers=headers, timeout=5).json()
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
        r   = scraper.get(url, timeout=5).json()
        return {
            "temp": round(r.get("main", {}).get("temp", 15), 1),
            "wind": round(r.get("wind", {}).get("speed", 0) * 3.6, 1),
            "rain": round(r.get("rain", {}).get("1h", 0), 2),
            "desc": r.get("weather", [{}])[0].get("description", ""),
        }
    except:
        return None

def weather_impact(w):
    if not w:
        return 0, "❓"
    impact, labels = 0, []
    if w["rain"] > 5:      impact -= 15; labels.append("🌧️ Forte pluie")
    elif w["rain"] > 1:    impact -= 7;  labels.append("🌦️ Pluie légère")
    if w["wind"] > 50:     impact -= 12; labels.append("💨 Vent violent")
    elif w["wind"] > 30:   impact -= 5;  labels.append("💨 Vent modéré")
    if w["temp"] > 32:     impact -= 8;  labels.append("🥵 Chaleur")
    elif w["temp"] < 2:    impact -= 5;  labels.append("❄️ Froid")
    else:                  impact += 5;  labels.append("☀️ Conditions favorables")
    return impact, " | ".join(labels)

def predict(h2h, home_fs, away_fs):
    total = h2h.get("total", 0)
    if   total >= 8: w_h2h, w_form = 0.65, 0.35
    elif total >= 4: w_h2h, w_form = 0.50, 0.50
    elif total >= 1: w_h2h, w_form = 0.30, 0.70
    else:            w_h2h, w_form = 0.10, 0.90

    h2h_home = h2h["home_wins"] / total if total else 0.34
    h2h_away = h2h["away_wins"] / total if total else 0.33
    h2h_draw = h2h["draws"]     / total if total else 0.33

    pred_home = round((h2h_home * w_h2h) + (home_fs * w_form), 3)
    pred_away = round((h2h_away * w_h2h) + (away_fs * w_form), 3)
    pred_draw = round(max(1 - pred_home - pred_away, 0), 3)

    return pred_home, pred_draw, pred_away, w_h2h, w_form

def kelly(prob, odd):
    if not prob or not odd or odd <= 1:
        return 0
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
    top3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    return top3

def compute_shadow_score(confidence, best_value, best_kelly, has_lineup, w_impact):
    score  = confidence * 0.30
    score += min((best_value or 0) * 100, 25)
    score += min(best_kelly * 100, 15)
    if has_lineup: score += 10
    score += w_impact
    return round(min(max(score, 0), 100))

def get_trend(form_list):
    if len(form_list) < 3:
        return "❓"
    pts = {"W": 3, "D": 1, "L": 0}
    recent = sum(pts.get(r, 0) for r in form_list[:2]) / 2
    older  = sum(pts.get(r, 0) for r in form_list[2:]) / max(len(form_list[2:]), 1)
    if   recent > older + 0.5: return "📈 En hausse"
    elif recent < older - 0.5: return "📉 En baisse"
    else:                      return "➡️  Stable"

# ════════════════════════════════════════════════════════
# ANALYSE FOOT / RUGBY / HOCKEY (équipes)
# ════════════════════════════════════════════════════════

def analyze_team_sport(sport_name, sport_key):
    print(f"\n⚽🏒🏉 Analyse {sport_name}...")
    events = get_events(sport_key)
    print(f"  ✅ {len(events)} matchs trouvés")

    results = []

    for event in events:
        home     = event.get("homeTeam", {}).get("name", "?")
        away     = event.get("awayTeam", {}).get("name", "?")
        event_id = event.get("id")
        home_id  = event.get("homeTeam", {}).get("id")
        away_id  = event.get("awayTeam", {}).get("id")

        odds      = get_odds(event_id)
        lineups   = get_lineups(event_id)
        h2h       = get_h2h(event_id)
        home_form = get_form(home_id)
        away_form = get_form(away_id)
        weather   = get_weather(home)

        home_fs   = form_score(home_form)
        away_fs   = form_score(away_form)

        pred_home, pred_draw, pred_away, w_h2h, w_form = predict(h2h, home_fs, away_fs)

        odd_1 = odds.get("1") or odds.get("1X2_1")
        odd_x = odds.get("X") or odds.get("1X2_X")
        odd_2 = odds.get("2") or odds.get("1X2_2")

        ip_home     = round(1/odd_1, 3) if odd_1 else None
        ip_away     = round(1/odd_2, 3) if odd_2 else None
        value_home  = round(pred_home - ip_home, 3) if ip_home else None
        value_away  = round(pred_away - ip_away, 3) if ip_away else None
        best_value  = max(value_home or 0, value_away or 0)
        best_kelly  = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

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

        goals_exp  = round((0.5 + home_fs * 2.5) + (0.5 + away_fs * 2.5), 2)
        over_under = "⬆️ OVER 2.5" if goals_exp > 2.5 else "⬇️ UNDER 2.5"
        top3_scores = predict_score(home_fs, away_fs)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        results.append({
            "sport":    sport_name,
            "home":     home,
            "away":     away,
            "event_id": event_id,
            "odds":     {"1": odd_1, "X": odd_x, "2": odd_2},
            "lineups":  lineups,
            "h2h":      h2h,
            "form": {
                "home":       home_form,
                "away":       away_form,
                "home_score": home_fs,
                "away_score": away_fs,
                "home_trend": get_trend(home_form),
                "away_trend": get_trend(away_form),
            },
            "weather":        weather,
            "weather_label":  w_label,
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
# ANALYSE TENNIS (joueurs — pas d'équipes)
# ════════════════════════════════════════════════════════

def analyze_tennis():
    print(f"\n🎾 Analyse Tennis...")
    events = get_events("tennis")
    print(f"  ✅ {len(events)} matchs trouvés")

    results = []

    for event in events:
        home     = event.get("homeTeam", {}).get("name", "?")
        away     = event.get("awayTeam", {}).get("name", "?")
        event_id = event.get("id")
        home_id  = event.get("homeTeam", {}).get("id")
        away_id  = event.get("awayTeam", {}).get("id")

        odds      = get_odds(event_id)
        h2h       = get_h2h(event_id)
        home_form = get_form(home_id)
        away_form = get_form(away_id)

        home_fs = form_score(home_form)
        away_fs = form_score(away_form)

        pred_home, pred_draw, pred_away, w_h2h, w_form = predict(h2h, home_fs, away_fs)

        # Tennis → pas de nul
        if pred_home > pred_away: winner = f"🎾 {home}"
        else:                     winner = f"🎾 {away}"

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

        score = compute_shadow_score(confidence, best_value, best_kelly, False, 0)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE {home} ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE {away} ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        results.append({
            "sport":    "tennis",
            "home":     home,
            "away":     away,
            "event_id": event_id,
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
# ANALYSE BASKETBALL
# ════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════
# NBA — ESPN + BallDontLie
# ════════════════════════════════════════════════════════

def get_nba_games():
    try:
        r      = scraper.get(f"{ESPN_BASE}/scoreboard", headers={"User-Agent": "Mozilla/5.0"}).json()
        events = r.get("events", [])
        games  = []
        for e in events:
            comp  = e.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            home  = next((t for t in teams if t["homeAway"] == "home"), {})
            away  = next((t for t in teams if t["homeAway"] == "away"), {})
            status = e.get("status", {}).get("type", {})
            games.append({
                "game_id":    e.get("id"),
                "home":       home.get("team", {}).get("displayName", "?"),
                "away":       away.get("team", {}).get("displayName", "?"),
                "home_id":    home.get("team", {}).get("id"),
                "away_id":    away.get("team", {}).get("id"),
                "home_score": home.get("score", "0"),
                "away_score": away.get("score", "0"),
                "status":     status.get("name", ""),
                "time":       e.get("date", "")[:16].replace("T", " "),
            })
        return games
    except Exception as e:
        print(f"  ❌ get_nba_games: {e}")
        return []

def get_nba_standings():
    try:
        r = scraper.get(f"{ESPN_WEB}/standings", headers={"User-Agent": "Mozilla/5.0"}).json()
        standings = {}
        for conf in r.get("children", []):
            for entry in conf.get("standings", {}).get("entries", []):
                team  = entry.get("team", {}).get("displayName", "?")
                stats = {s["name"]: s.get("displayValue") for s in entry.get("stats", [])}
                standings[team] = {
                    "wins":   stats.get("wins", "?"),
                    "losses": stats.get("losses", "?"),
                    "pct":    stats.get("winPercent", "0.5"),
                    "last10": stats.get("lastTen", "?"),
                    "home":   stats.get("home", "?"),
                    "away":   stats.get("road", "?"),
                }
        return standings
    except Exception as e:
        print(f"  ❌ get_nba_standings: {e}")
        return {}

def get_nba_injuries():
    try:
        r = scraper.get(f"{ESPN_BASE}/injuries", headers={"User-Agent": "Mozilla/5.0"}).json()
        injuries = {}
        for item in r.get("injuries", []):
            team    = item.get("team", {}).get("displayName", "?")
            players = []
            for inj in item.get("injuries", []):
                players.append({
                    "name":   inj.get("athlete", {}).get("displayName", "?"),
                    "status": inj.get("status", "?"),
                })
            injuries[team] = players
        return injuries
    except Exception as e:
        print(f"  ❌ get_nba_injuries: {e}")
        return {}

def get_nba_team_stats(team_id):
    try:
        r    = scraper.get(f"{ESPN_BASE}/teams/{team_id}/statistics", headers={"User-Agent": "Mozilla/5.0"}).json()
        cats = r.get("results", {}).get("stats", {}).get("categories", [])
        stats = {}
        for cat in cats:
            for s in cat.get("stats", []):
                stats[s["name"]] = s.get("displayValue", "?")
        return stats
    except:
        return {}

def get_bdl_form(team_name):
    if not BALLDONTLIE_KEY:
        return []
    search = NBA_TEAMS.get(team_name, team_name)
    try:
        r = requests.get(
            f"{BDL_BASE}/teams",
            headers=HEADERS_BDL,
            params={"search": search},
            timeout=10
        ).json()
        if not r.get("data"):
            return []
        team_id = r["data"][0]["id"]
        games = requests.get(
            f"{BDL_BASE}/games",
            headers=HEADERS_BDL,
            params={"team_ids[]": team_id, "per_page": 5, "seasons[]": 2025},
            timeout=10
        ).json()
        form = []
        for g in games.get("data", []):
            hs  = g.get("home_team_score", 0)
            aws = g.get("visitor_team_score", 0)
            ht  = g.get("home_team", {}).get("id")
            form.append("W" if (hs > aws and ht == team_id) or (aws > hs and ht != team_id) else "L")
        return form
    except:
        return []

# ── BallDontLie : stats avancées équipe (avg pts/reb/ast) ──
_bdl_team_id_cache = {}

def get_bdl_team_id(team_name):
    if team_name in _bdl_team_id_cache:
        return _bdl_team_id_cache[team_name]
    if not BALLDONTLIE_KEY:
        return None
    search = NBA_TEAMS.get(team_name, team_name)
    try:
        r = requests.get(f"{BDL_BASE}/teams", headers=HEADERS_BDL,
                         params={"search": search}, timeout=10).json()
        if r.get("data"):
            tid = r["data"][0]["id"]
            _bdl_team_id_cache[team_name] = tid
            return tid
    except:
        pass
    return None

def get_bdl_team_avg(team_name):
    """Moyennes pts/reb/ast sur les 5 derniers matchs via BallDontLie."""
    tid = get_bdl_team_id(team_name)
    if not tid:
        return {}
    try:
        games = requests.get(
            f"{BDL_BASE}/games", headers=HEADERS_BDL,
            params={"team_ids[]": tid, "per_page": 5, "seasons[]": 2025},
            timeout=10
        ).json().get("data", [])
        pts_list, margins = [], []
        for g in games:
            hs  = g.get("home_team_score") or 0
            aws = g.get("visitor_team_score") or 0
            ht  = g.get("home_team", {}).get("id")
            if ht == tid:
                pts_list.append(hs)
                margins.append(hs - aws)
            else:
                pts_list.append(aws)
                margins.append(aws - hs)
        if not pts_list:
            return {}
        return {
            "avg_pts":    round(sum(pts_list) / len(pts_list), 1),
            "avg_margin": round(sum(margins) / len(margins), 1),
            "last5_pts":  pts_list,
        }
    except:
        return {}

def get_bdl_player_props(team_name):
    """Stats top joueurs pour player props via BallDontLie season averages."""
    tid = get_bdl_team_id(team_name)
    if not tid:
        return []
    try:
        # Récupère les joueurs de l'équipe
        players_r = requests.get(
            f"{BDL_BASE}/players", headers=HEADERS_BDL,
            params={"team_ids[]": tid, "per_page": 10},
            timeout=10
        ).json().get("data", [])
        props = []
        for p in players_r[:5]:
            pid  = p.get("id")
            name = f"{p.get('first_name','')} {p.get('last_name','')}".strip()
            try:
                avg = requests.get(
                    f"{BDL_BASE}/season_averages", headers=HEADERS_BDL,
                    params={"season": 2025, "player_ids[]": pid},
                    timeout=8
                ).json().get("data", [{}])[0]
                pts = avg.get("pts", 0) or 0
                reb = avg.get("reb", 0) or 0
                ast = avg.get("ast", 0) or 0
                if pts > 8:  # Seulement les joueurs significatifs
                    props.append({
                        "name": name,
                        "pts":  round(float(pts), 1),
                        "reb":  round(float(reb), 1),
                        "ast":  round(float(ast), 1),
                        "pts_line":  round(float(pts) * 0.95, 1),  # Ligne O/U légèrement sous la moyenne
                        "pts_value": round(min((float(pts) / 25) * 100, 95), 0),
                    })
            except:
                continue
        return sorted(props, key=lambda x: x["pts"], reverse=True)[:3]
    except:
        return []

# ── Basketball-Reference : advanced stats ──────────────
_bbref_cache = {}

def get_bbref_advanced_stats():
    """Récupère OffRtg, DefRtg, Pace, eFG% depuis Basketball-Reference."""
    if _bbref_cache:
        return _bbref_cache
    try:
        import pandas as pd
        url    = "https://www.basketball-reference.com/leagues/NBA_2025.html"
        tables = pd.read_html(url, attrs={"id": "advanced-team"})
        if not tables:
            return {}
        df = tables[0]
        # Flatten multi-index columns si besoin
        if hasattr(df.columns, 'levels'):
            df.columns = [' '.join(c).strip() for c in df.columns]
        for _, row in df.iterrows():
            team = str(row.get("Team", row.get("Unnamed: 1_level_1", ""))).strip()
            if not team or team == "Team" or "League" in team:
                continue
            try:
                _bbref_cache[team] = {
                    "off_rtg": float(str(row.get("ORtg", row.get("Offense ORtg", 0))).replace("*","")),
                    "def_rtg": float(str(row.get("DRtg", row.get("Defense DRtg", 0))).replace("*","")),
                    "pace":    float(str(row.get("Pace", 0)).replace("*","")),
                    "efg_pct": float(str(row.get("eFG%", 0)).replace("*","")),
                    "net_rtg": float(str(row.get("NRtg", 0)).replace("*","")),
                }
            except:
                continue
        print(f"  ✅ Basketball-Reference: {len(_bbref_cache)} équipes")
    except Exception as e:
        print(f"  ⚠️  Basketball-Reference: {e}")
    return _bbref_cache

def find_bbref_team(team_name, bbref_data):
    """Matching approximatif entre nom ESPN et nom Basketball-Reference."""
    if not bbref_data:
        return {}
    # Cherche par mot clé (ex: "Lakers" dans "Los Angeles Lakers")
    for key in bbref_data:
        if any(word in key for word in team_name.split() if len(word) > 3):
            return bbref_data[key]
    return {}

# ── ESPN : analyse expert ───────────────────────────────
def get_espn_game_analysis(game_id):
    """Récupère le résumé/analyse ESPN pour un match."""
    try:
        r = scraper.get(
            f"{ESPN_BASE}/summary",
            headers={"User-Agent": "Mozilla/5.0"},
            params={"event": game_id},
            timeout=8
        ).json()
        # Récupère le headline ou gameNote
        note = r.get("gameInfo", {}).get("venue", {}).get("fullName", "")
        headlines = r.get("news", {}).get("headline", "")
        return headlines or note or ""
    except:
        return ""

# ── Calcul spread/handicap ──────────────────────────────
def compute_spread(pred_home, pred_away, avg_margin_home, avg_margin_away):
    """Calcule le spread estimé basé sur les probabilités et moyennes."""
    try:
        # Spread basé sur la différence de proba × facteur de conversion NBA
        prob_diff  = pred_home - pred_away  # entre -1 et +1
        margin_avg = (avg_margin_home - avg_margin_away) / 2
        spread     = round((prob_diff * 12) + (margin_avg * 0.3), 1)
        return spread  # positif = favori home, négatif = favori away
    except:
        return 0.0

def analyze_basketball(slot=None):
    print(f"\n🏀 Analyse Basketball (NBA + autres)...")

    # ── Données globales NBA ─────────────────────────────
    nba_results = []
    games     = get_nba_games()
    standings = get_nba_standings()
    injuries  = get_nba_injuries()
    bbref     = get_bbref_advanced_stats()
    games     = [g for g in games if g["status"] != "STATUS_FINAL"]
    print(f"  ✅ {len(games)} matchs NBA")

    for game in games:
        home    = game["home"]
        away    = game["away"]
        home_id = game["home_id"]
        away_id = game["away_id"]

        # Stats ESPN
        home_stats = get_nba_team_stats(home_id)
        away_stats = get_nba_team_stats(away_id)

        # Forme + moyennes BallDontLie
        home_form = get_bdl_form(home)
        away_form = get_bdl_form(away)
        home_avg  = get_bdl_team_avg(home)
        away_avg  = get_bdl_team_avg(away)

        # Player props top joueurs
        home_props = get_bdl_player_props(home)
        away_props = get_bdl_player_props(away)

        # Advanced stats Basketball-Reference
        home_adv = find_bbref_team(home, bbref)
        away_adv = find_bbref_team(away, bbref)

        # Standings + blessures
        home_std = standings.get(home, {})
        away_std = standings.get(away, {})
        home_inj = injuries.get(home, [])
        away_inj = injuries.get(away, [])

        # ESPN game analysis
        analysis = get_espn_game_analysis(game["game_id"])

        # ── Prédiction enrichie ──────────────────────────
        def fs(f): return sum(1 if r == "W" else 0 for r in f) / len(f) if f else 0.5
        home_fs = fs(home_form)
        away_fs = fs(away_form)

        try:
            home_pct = float(home_std.get("pct", 0.5) or 0.5)
            away_pct = float(away_std.get("pct", 0.5) or 0.5)
        except:
            home_pct = away_pct = 0.5

        # Intégrer NetRtg si dispo
        home_net = home_adv.get("net_rtg", 0) or 0
        away_net = away_adv.get("net_rtg", 0) or 0
        net_diff = (home_net - away_net) / 20  # normalise ≈ [-0.5, 0.5]

        pred_home = round((home_fs * 0.35 + home_pct * 0.45 + max(net_diff, 0) * 0.20), 3)
        pred_away = round((away_fs * 0.35 + away_pct * 0.45 + max(-net_diff, 0) * 0.20), 3)
        total_p   = pred_home + pred_away
        pred_home = round(pred_home / total_p, 3) if total_p else 0.5
        pred_away = round(1 - pred_home, 3)

        winner = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

        # ── Over/Under ───────────────────────────────────
        try:
            home_ppg = float(home_stats.get("avgPoints", 0) or 0)
            away_ppg = float(away_stats.get("avgPoints", 0) or 0)
            # Ajuster avec le Pace si dispo
            home_pace = home_adv.get("pace", 100) or 100
            away_pace = away_adv.get("pace", 100) or 100
            pace_adj  = ((home_pace + away_pace) / 2 - 100) * 0.5
            total_pts = round(home_ppg + away_ppg + pace_adj, 1)
            ou_line   = 220.5
            over_under = f"⬆️ OVER {ou_line} ({total_pts}pts)" if total_pts > ou_line else f"⬇️ UNDER {ou_line} ({total_pts}pts)"
        except:
            total_pts  = 0
            over_under = "❓"

        # ── Spread estimé ────────────────────────────────
        h_margin = home_avg.get("avg_margin", 0) or 0
        a_margin = away_avg.get("avg_margin", 0) or 0
        spread   = compute_spread(pred_home, pred_away, h_margin, a_margin)
        if spread > 0:
            spread_label = f"🏠 {home} -{abs(spread)} / {away} +{abs(spread)}"
        elif spread < 0:
            spread_label = f"✈️ {away} -{abs(spread)} / {home} +{abs(spread)}"
        else:
            spread_label = "Pick'em"

        # ── Confiance & score ────────────────────────────
        confidence = 50
        if home_form and away_form: confidence += 15
        if home_std  and away_std:  confidence += 15
        if home_adv  and away_adv:  confidence += 10
        if home_props:              confidence += 10
        shadow_score = min(confidence, 100)

        # ── Value bet si cotes dispo ─────────────────────
        # Cotes implicites depuis proba (pour affichage même sans bookmaker)
        impl_odd_home = round(1 / pred_home, 2) if pred_home > 0 else None
        impl_odd_away = round(1 / pred_away, 2) if pred_away > 0 else None

        nba_results.append({
            "sport":      "basketball",
            "league":     "NBA",
            "home":       home,
            "away":       away,
            "game_id":    game["game_id"],
            "time":       game["time"],
            "standings":  {"home": home_std, "away": away_std},
            "form": {
                "home":       home_form,
                "away":       away_form,
                "home_trend": get_trend(home_form),
                "away_trend": get_trend(away_form),
                "home_avg":   home_avg,
                "away_avg":   away_avg,
            },
            "injuries":  {"home": home_inj, "away": away_inj},
            "advanced":  {"home": home_adv, "away": away_adv},
            "props":     {"home": home_props, "away": away_props},
            "analysis":  analysis,
            "stats": {
                "home_ppg":           str(home_stats.get("avgPoints", "?")),
                "away_ppg":           str(away_stats.get("avgPoints", "?")),
                "total_pts_expected": str(total_pts),
                "home_off_rtg":       str(home_adv.get("off_rtg", "?")),
                "home_def_rtg":       str(home_adv.get("def_rtg", "?")),
                "away_off_rtg":       str(away_adv.get("off_rtg", "?")),
                "away_def_rtg":       str(away_adv.get("def_rtg", "?")),
                "home_pace":          str(home_adv.get("pace", "?")),
                "away_pace":          str(away_adv.get("pace", "?")),
            },
            "odds":  {"1": impl_odd_home, "2": impl_odd_away},
            "value": {},
            "kelly": {},
            "spread": {
                "value": spread,
                "label": spread_label,
            },
            "prediction": {
                "home_prob":  pred_home,
                "away_prob":  pred_away,
                "winner":     winner,
                "over_under": over_under,
                "ou_line":    total_pts,
                "confidence": confidence,
            },
            "verdict":      "⚪ Pas de value",
            "shadow_score": shadow_score,
        })

    # ── Autres ligues basket via SofaScore ──────────────
    sofa_results = []
    events = get_events("basketball")
    # Exclure les matchs NBA déjà traités
    nba_names = {f"{r['home']}_{r['away']}" for r in nba_results}
    for event in events:
        home     = event.get("homeTeam", {}).get("name", "?")
        away     = event.get("awayTeam", {}).get("name", "?")
        if f"{home}_{away}" in nba_names:
            continue
        event_id = event.get("id")
        home_id  = event.get("homeTeam", {}).get("id")
        away_id  = event.get("awayTeam", {}).get("id")
        ts       = event.get("startTimestamp", 0)
        match_time = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?"

        odds      = get_odds(event_id, home, away)
        h2h       = get_h2h(event_id)
        home_form = get_form(home_id)
        away_form = get_form(away_id)
        home_fs   = form_score(home_form)
        away_fs   = form_score(away_form)

        pred_home, pred_draw, pred_away, w_h2h, w_form = predict(h2h, home_fs, away_fs)
        winner    = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

        odd_1      = odds.get("1")
        odd_2      = odds.get("2")
        ip_home    = round(1/odd_1, 3) if odd_1 else None
        ip_away    = round(1/odd_2, 3) if odd_2 else None
        value_home = round(pred_home - ip_home, 3) if ip_home else None
        value_away = round(pred_away - ip_away, 3) if ip_away else None
        best_value = max(value_home or 0, value_away or 0)
        best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))
        confidence = round(
            min(h2h["total"] / 10 * 40, 40) +
            min((len(home_form) + len(away_form)) / 10 * 40, 40) +
            (20 if odd_1 else 0)
        )
        total_pts  = round((home_fs * 120) + (away_fs * 120), 1)
        over_under = f"⬆️ OVER 220 ({total_pts}pts)" if total_pts > 220 else f"⬇️ UNDER 220 ({total_pts}pts)"
        score      = compute_shadow_score(confidence, best_value, best_kelly, False, 0)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        sofa_results.append({
            "sport": "basketball", "league": "Other",
            "home": home, "away": away, "event_id": event_id, "time": match_time,
            "odds": {"1": odd_1, "2": odd_2}, "h2h": h2h,
            "form": {
                "home": home_form, "away": away_form,
                "home_score": home_fs, "away_score": away_fs,
                "home_trend": get_trend(home_form), "away_trend": get_trend(away_form),
            },
            "prediction": {
                "home_prob": pred_home, "away_prob": pred_away,
                "winner": winner, "confidence": confidence, "over_under": over_under,
            },
            "value": {"home": value_home, "away": value_away},
            "kelly": {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
            "verdict": verdict, "shadow_score": score,
        })

    print(f"  ✅ {len(sofa_results)} autres matchs basket (SofaScore)")
    return nba_results + sofa_results

# ════════════════════════════════════════════════════════
# ENVOI VERS RAILWAY
# ════════════════════════════════════════════════════════

def send_to_railway(sport, results):
    try:
        r = requests.post(
            f"{RAILWAY_URL}/ingest/{sport}",
            json={"date": today, "matches": results},
            timeout=15
        )
        print(f"  📡 Railway /ingest/{sport} → {r.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ Erreur Railway {sport}: {e}")
        return False

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
        print(f"  #{i} 😈 ({score}/100) {r['home']} vs {r['away']}")
        print(f"     → {pred.get('winner', '?')}")
        print(f"     Cotes: 1:{odds.get('1')} 2:{odds.get('2')}")
        print(f"     {r.get('verdict', '')}")

# ════════════════════════════════════════════════════════
# MAIN
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

send_to_railway = send_to_server  # alias compatibilité

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
        results = analyze_team_sport("football", "football", slot)
        print_top5(results, "football")
        send_to_server("football", results)

    if target in ("all", "basketball"):
        results = analyze_basketball(slot)
        print_top5(results, "basketball")
        send_to_server("basketball", results)

    if target in ("all", "tennis"):
        results = analyze_tennis()
        print_top5(results, "tennis")
        send_to_server("tennis", results)

    if target in ("all", "hockey"):
        results = analyze_team_sport("hockey", "ice-hockey", slot)
        print_top5(results, "hockey")
        send_to_server("hockey", results)

    if target in ("all", "rugby"):
        results = analyze_team_sport("rugby", "rugby", slot)
        print_top5(results, "rugby")
        send_to_server("rugby", results)

    print(f"\n✅ Shadow Edge V∞ terminé — {now.strftime('%H:%M')} !")
