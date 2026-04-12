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
from datetime import date

# ── CONFIG ──────────────────────────────────────────────
RAILWAY_URL     = os.getenv("RAILWAY_URL", "https://ton-app.up.railway.app")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

scraper = cloudscraper.create_scraper()
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer":    "https://www.sofascore.com/"
}

today = date.today().strftime("%Y-%m-%d")

# ── SPORTS SOFASCORE ────────────────────────────────────
SPORTS = {
    "football":   "football",
    "basketball": "basketball",
    "tennis":     "tennis",
    "hockey":     "ice-hockey",
    "rugby":      "rugby",
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
    """Récupère tous les matchs du jour pour un sport."""
    try:
        url  = f"https://api.sofascore.com/api/v1/sport/{sport_key}/scheduled-events/{today}"
        data = scraper.get(url, headers=headers, timeout=10).json()
        return data.get("events", [])
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

def analyze_basketball():
    print(f"\n🏀 Analyse Basketball...")
    events = get_events("basketball")
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

        if pred_home > pred_away: winner = f"🏀 {home}"
        else:                     winner = f"🏀 {away}"

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

        # Basket → Over/Under sur 200 pts
        total_pts = round((home_fs * 120) + (away_fs * 120), 1)
        over_under = "⬆️ OVER 220" if total_pts > 220 else "⬇️ UNDER 220"

        score = compute_shadow_score(confidence, best_value, best_kelly, False, 0)

        if   value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
        elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
        else:                                   verdict = "⚪ Pas de value"

        results.append({
            "sport":    "basketball",
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
                "over_under": over_under,
            },
            "value":        {"home": value_home, "away": value_away},
            "kelly":        {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
            "verdict":      verdict,
            "shadow_score": score,
        })

    return results

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

if __name__ == "__main__":

    # Sport spécifique ou tous
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"🚀 Shadow Edge V∞ — {today}")
    print(f"🎯 Sport cible: {target}")
    print(f"📡 Railway: {RAILWAY_URL}")
    print("=" * 50)

    if target in ("all", "football"):
        results = analyze_team_sport("football", "football")
        print_top5(results, "football")
        send_to_railway("football", results)

    if target in ("all", "basketball"):
        results = analyze_basketball()
        print_top5(results, "basketball")
        send_to_railway("basketball", results)

    if target in ("all", "tennis"):
        results = analyze_tennis()
        print_top5(results, "tennis")
        send_to_railway("tennis", results)

    if target in ("all", "hockey"):
        results = analyze_team_sport("hockey", "ice-hockey")
        print_top5(results, "hockey")
        send_to_railway("hockey", results)

    if target in ("all", "rugby"):
        results = analyze_team_sport("rugby", "rugby")
        print_top5(results, "rugby")
        send_to_railway("rugby", results)

    print("\n✅ Shadow Edge V∞ terminé !")
