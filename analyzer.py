"""
Shadow Edge V∞ — Analyzer
Moteur analytique multi-sport basé sur AllSportsAPI + odds-api.io + ESPN + BallDontLie

Usage:
    python analyzer.py              → tous les sports
    python analyzer.py football     → foot seulement
    python analyzer.py basketball   → basket seulement
    python analyzer.py tennis       → tennis seulement
    python analyzer.py hockey       → hockey seulement
    python analyzer.py rugby        → rugby seulement

Variables d'environnement requises:
    RENDER_URL          → URL de votre instance Render
    ALLSPORTS_KEY       → Clé AllSportsAPI
    ODDS_API_KEY        → Clé odds-api.io
    BALLDONTLIE_API_KEY → Clé BallDontLie (NBA)
    OPENWEATHER_KEY     → Clé OpenWeather (météo, optionnel)
"""

import requests
import math
import os
import sys
import time
from datetime import datetime, date

# ════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════

RENDER_URL       = os.getenv("RAILWAY_URL", "https://shadow-edge-v-5mdf.onrender.com")
ALLSPORTS_KEY    = os.getenv("ALLSPORTS_KEY", "")
ODDS_API_KEY     = os.getenv("ODDS_API_KEY", "")
BALLDONTLIE_KEY  = os.getenv("BALLDONTLIE_API_KEY", "")
OPENWEATHER_KEY  = os.getenv("OPENWEATHER_KEY", "")

ALLSPORTS_BASE   = "https://apiv2.allsportsapi.com"
ODDS_API_BASE    = "https://api.odds-api.io/v3"
ESPN_BASE        = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_WEB         = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba"
BDL_BASE         = "https://api.balldontlie.io/v1"

HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

today = date.today().strftime("%Y-%m-%d")
now   = datetime.now()

# ════════════════════════════════════════════════════════
# WHITELIST LIGUES AllSportsAPI (league_key)
# ════════════════════════════════════════════════════════

FOOTBALL_LEAGUES = {
    # England
    "148": "Premier League", "149": "Championship",
    # Spain
    "302": "La Liga", "303": "La Liga 2",
    # Italy
    "207": "Serie A", "206": "Serie B", "205": "Coppa Italia",
    # France
    "168": "Ligue 1", "169": "Ligue 2", "170": "Coupe de France",
    # Germany
    "175": "Bundesliga", "176": "2. Bundesliga", "177": "DFB-Pokal",
    # UEFA
    "244": "Champions League", "245": "Europa League", "247": "Conference League",
    "256": "Nations League",
    # Other
    "152": "MLS", "244": "Eredivisie",
    "320": "Primeira Liga",
    "73":  "Brasileirao",
    "480": "Libertadores",
    "312": "Liga Profesional",
    "409": "Pro League",
    "264": "Chinese Super League",
    "271": "K League 1",
    "119": "Danish Superliga",
    "501": "Scottish Premiership",
    "203": "Süper Lig",
    "98":  "J1 League",
}

BASKETBALL_LEAGUES = {
    "12": "NBA", "19": "WNBA", "120": "NCAA",
    "132": "EuroLeague", "133": "EuroCup",
    "134": "ACB", "139": "Lega Basket",
    "140": "BBL", "141": "Pro A",
    "142": "BSL", "143": "VTB",
    "144": "KBL", "145": "NBL",
    "146": "NBB", "147": "GBL",
}

HOCKEY_LEAGUES = {
    "57": "NHL", "58": "AHL",
    "59": "DEL", "60": "National League",
    "61": "SHL", "62": "Liiga",
    "63": "Extraliga", "64": "Ligue Magnus",
}

RUGBY_LEAGUES = {
    "67": "Top 14", "68": "Pro D2",
    "69": "Champions Cup", "70": "Premiership",
    "71": "Super Rugby", "72": "Six Nations",
}

# ════════════════════════════════════════════════════════
# UTILS HTTP
# ════════════════════════════════════════════════════════

def allsports(sport, params):
    """Appel AllSportsAPI."""
    try:
        base = f"{ALLSPORTS_BASE}/{sport}/"
        p    = {"APIkey": ALLSPORTS_KEY, **params}
        r    = requests.get(base, params=p, timeout=10)
        if r.status_code == 200:
            return r.json().get("result", []) or []
    except Exception as e:
        print(f"  ❌ AllSports {sport} {params.get('met')}: {e}")
    return []

def odds_api(endpoint, params={}):
    """Appel odds-api.io."""
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/{endpoint}",
            params={"apiKey": ODDS_API_KEY, **params},
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        print(f"  ❌ OddsAPI {endpoint}: {e}")
    return []

# ════════════════════════════════════════════════════════
# ALLSPORTS — FONCTIONS COMMUNES
# ════════════════════════════════════════════════════════

def get_fixtures(sport_key, league_ids):
    """Récupère les matchs du jour pour une liste de ligues."""
    results = []
    for lid in league_ids:
        data = allsports(sport_key, {
            "met": "Fixtures",
            "from": today,
            "to": today,
            "leagueId": lid,
        })
        for m in data:
            if m.get("event_status") not in ("", "notstarted", None):
                continue  # Ignore matchs terminés ou en cours
            m["_league_id"] = lid
            results.append(m)
    return results

def get_h2h(home_id, away_id):
    """H2H entre deux équipes."""
    data = allsports("football", {
        "met": "H2H",
        "firstTeamId": home_id,
        "secondTeamId": away_id,
    })
    if isinstance(data, dict):
        h2h_matches = data.get("H2H", [])
        hw = sum(1 for m in h2h_matches if m.get("home_team_key") == str(home_id) and
                 m.get("event_final_result", "").split(" - ")[0] >
                 m.get("event_final_result", "").split(" - ")[-1])
        aw = sum(1 for m in h2h_matches if m.get("away_team_key") == str(away_id) and
                 m.get("event_final_result", "").split(" - ")[-1] >
                 m.get("event_final_result", "").split(" - ")[0])
        dr = len(h2h_matches) - hw - aw
        return {"home_wins": hw, "away_wins": aw, "draws": dr, "total": len(h2h_matches)}
    return {"home_wins": 0, "away_wins": 0, "draws": 0, "total": 0}

def get_standings(sport_key, league_id):
    """Classement d'une ligue."""
    data = allsports(sport_key, {"met": "Standings", "leagueId": league_id})
    if isinstance(data, dict):
        return data.get("total", [])
    return data or []

def get_team_standing(standings, team_name):
    """Trouve la position d'une équipe dans le classement."""
    for row in standings:
        if row.get("standing_team", "").lower() in team_name.lower() or \
           team_name.lower() in row.get("standing_team", "").lower():
            return {
                "position": int(row.get("standing_place", 99)),
                "points":   int(row.get("standing_PTS", 0)),
                "played":   int(row.get("standing_P", 0)),
                "wins":     int(row.get("standing_W", 0)),
                "draws":    int(row.get("standing_D", 0)),
                "losses":   int(row.get("standing_L", 0)),
                "gf":       int(row.get("standing_F", 0)),
                "ga":       int(row.get("standing_A", 0)),
            }
    return {}

def get_probabilities(match_id, sport_key="football"):
    """Probas 1X2, BTTS, Over/Under depuis AllSportsAPI."""
    data = allsports(sport_key, {"met": "Probabilities", "matchId": match_id})
    if data and isinstance(data, list):
        p = data[0]
        return {
            "home_win":  float(p.get("event_HW", 33) or 33) / 100,
            "draw":      float(p.get("event_D",  33) or 33) / 100,
            "away_win":  float(p.get("event_AW", 33) or 33) / 100,
            "btts":      float(p.get("event_bts", 50) or 50) / 100,
            "over_25":   float(p.get("event_O",  50) or 50) / 100,
            "under_25":  float(p.get("event_U",  50) or 50) / 100,
            "over_15":   float(p.get("event_O_1", 70) or 70) / 100,
            "over_35":   float(p.get("event_O_3", 30) or 30) / 100,
        }
    return {}

def get_odds_allsports(match_id, sport_key="football"):
    """Cotes 1X2 + Over/Under depuis AllSportsAPI."""
    data = allsports(sport_key, {"met": "Odds", "matchId": match_id})
    if isinstance(data, dict) and str(match_id) in data:
        bookmakers = data[str(match_id)]
        if bookmakers:
            bk = bookmakers[0]
            return {
                "1":    float(bk.get("odd_1", 0) or 0) or None,
                "X":    float(bk.get("odd_x", 0) or 0) or None,
                "2":    float(bk.get("odd_2", 0) or 0) or None,
                "o25":  float(bk.get("o+2.5", 0) or 0) or None,
                "u25":  float(bk.get("u+2.5", 0) or 0) or None,
                "o15":  float(bk.get("o+1.5", 0) or 0) or None,
                "btts_yes": float(bk.get("bts_yes", 0) or 0) or None,
                "btts_no":  float(bk.get("bts_no", 0) or 0) or None,
            }
    return {}

def get_form_from_fixtures(team_id, sport_key="football", n=5):
    """Forme récente d'une équipe via AllSportsAPI."""
    data = allsports(sport_key, {
        "met": "Fixtures",
        "teamId": team_id,
        "from": "2024-07-01",
        "to": today,
    })
    finished = [m for m in data if m.get("event_status") == "Finished"]
    finished = sorted(finished, key=lambda x: x.get("event_date", ""), reverse=True)[:n]
    form = []
    for m in finished:
        result = m.get("event_final_result", "0 - 0")
        try:
            h, a = [int(x.strip()) for x in result.split(" - ")]
        except:
            continue
        if str(team_id) == str(m.get("home_team_key")):
            form.append("W" if h > a else ("D" if h == a else "L"))
        else:
            form.append("W" if a > h else ("D" if h == a else "L"))
    return form

# ════════════════════════════════════════════════════════
# ODDS-API.IO
# ════════════════════════════════════════════════════════

_vbets_cache = {}

def get_value_bets(sport):
    """Value bets pré-calculés par odds-api.io."""
    if sport in _vbets_cache:
        return _vbets_cache[sport]
    sport_map = {
        "football": "football", "basketball": "basketball",
        "tennis": "tennis", "hockey": "ice-hockey", "rugby": "rugby-union",
    }
    vbs = odds_api("value-bets", {
        "sport": sport_map.get(sport, sport),
        "includeEventDetails": "true"
    })
    _vbets_cache[sport] = vbs if isinstance(vbs, list) else []
    print(f"  ✅ Value bets {sport}: {len(_vbets_cache[sport])} opportunités")
    return _vbets_cache[sport]

def find_value_bet(home, away, sport):
    """Cherche un value bet pour un match."""
    vbs = get_value_bets(sport)
    for vb in vbs:
        ev = vb.get("event", {})
        h  = ev.get("homeTeam", {}).get("name", "") or ev.get("home", "")
        a  = ev.get("awayTeam", {}).get("name", "") or ev.get("away", "")
        if (any(w in h for w in home.split() if len(w) > 3) and
            any(w in a for w in away.split() if len(w) > 3)):
            return {
                "value":     round(float(vb.get("value", 0) or 0), 3),
                "odd":       round(float(vb.get("price", 0) or 0), 2),
                "bookmaker": vb.get("bookmaker", "?"),
                "market":    vb.get("market", "?"),
                "selection": vb.get("selection", "?"),
            }
    return {}

# ════════════════════════════════════════════════════════
# MÉTÉO
# ════════════════════════════════════════════════════════

STADIUMS = {
    "Arsenal": (51.5549, -0.1084), "Liverpool": (53.4308, -2.9608),
    "Chelsea": (51.4816, -0.1910), "Manchester City": (53.4831, -2.2004),
    "Manchester United": (53.4631, -2.2913), "Tottenham": (51.6042, -0.0665),
    "Real Madrid": (40.4531, -3.6883), "FC Barcelona": (41.3809, 2.1228),
    "Juventus": (45.1096, 7.6413), "Milan": (45.4781, 9.1240),
    "Paris Saint-Germain": (48.8414, 2.2530), "Borussia Dortmund": (51.4926, 7.4518),
}

def get_weather(team):
    if not OPENWEATHER_KEY:
        return None
    coords = STADIUMS.get(team)
    if not coords:
        return None
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": coords[0], "lon": coords[1], "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=5
        ).json()
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
    if w["rain"] > 5:    impact -= 15; labels.append("🌧️ Forte pluie")
    elif w["rain"] > 1:  impact -= 7;  labels.append("🌦️ Pluie légère")
    if w["wind"] > 50:   impact -= 12; labels.append("💨 Vent violent")
    elif w["wind"] > 30: impact -= 5;  labels.append("💨 Vent modéré")
    if w["temp"] > 32:   impact -= 8;  labels.append("🥵 Chaleur")
    elif w["temp"] < 2:  impact -= 5;  labels.append("❄️ Froid")
    else:                impact += 5;  labels.append("☀️ Favorable")
    return impact, " | ".join(labels)

# ════════════════════════════════════════════════════════
# ALGOS COMMUNS
# ════════════════════════════════════════════════════════

def form_score(form):
    pts = {"W": 3, "D": 1, "L": 0}
    return sum(pts.get(r, 0) for r in form) / (len(form) * 3) if form else 0

def get_trend(form):
    if len(form) < 3:
        return "❓"
    pts = {"W": 3, "D": 1, "L": 0}
    recent = sum(pts.get(r, 0) for r in form[:2]) / 2
    older  = sum(pts.get(r, 0) for r in form[2:]) / max(len(form[2:]), 1)
    if   recent > older + 0.5: return "📈 En hausse"
    elif recent < older - 0.5: return "📉 En baisse"
    else:                       return "➡️ Stable"

def kelly(prob, odd):
    if not prob or not odd or odd <= 1:
        return 0
    b = odd - 1
    k = (b * prob - (1 - prob)) / b
    return round(max(k, 0) * 0.25, 4)

def shadow_score(confidence, best_value, best_kelly, has_lineup=False, w_impact=0):
    s  = confidence * 0.30
    s += min((best_value or 0) * 100, 25)
    s += min(best_kelly * 100, 15)
    if has_lineup: s += 10
    s += w_impact
    return round(min(max(s, 0), 100))

def pick_label(score):
    if score >= 80:   return "💎 PICK DIAMANT"
    elif score >= 65: return "🔥 PICK FORT"
    elif score >= 50: return "✅ PICK CORRECT"
    elif score >= 35: return "⚠️ PICK RISQUÉ"
    else:             return "❌ ÉVITER"

# ════════════════════════════════════════════════════════
# POISSON (FOOT)
# ════════════════════════════════════════════════════════

def poisson_matrix(home_lam, away_lam, max_goals=6):
    def p(lam, k): return (math.exp(-lam) * lam**k) / math.factorial(k)
    home_win = draw = away_win = 0
    scores = {}
    for h in range(max_goals):
        for a in range(max_goals):
            prob = p(home_lam, h) * p(away_lam, a)
            if h > a:    home_win += prob
            elif h == a: draw += prob
            else:        away_win += prob
            scores[f"{h}-{a}"] = round(prob, 4)
    top5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return round(home_win, 3), round(draw, 3), round(away_win, 3), top5

# ════════════════════════════════════════════════════════
# ANALYSE FOOTBALL
# ════════════════════════════════════════════════════════

def analyze_football():
    print(f"\n⚽ Analyse Football...")

    # Charge value bets une seule fois
    get_value_bets("football")

    # Fixtures du jour pour toutes les ligues
    matches = get_fixtures("football", list(FOOTBALL_LEAGUES.keys()))
    print(f"  ✅ {len(matches)} matchs trouvés")

    results = []

    for m in matches:
        home       = m.get("event_home_team", "?")
        away       = m.get("event_away_team", "?")
        home_id    = m.get("home_team_key")
        away_id    = m.get("away_team_key")
        match_id   = m.get("event_key")
        league     = FOOTBALL_LEAGUES.get(str(m.get("_league_id", "")), m.get("league_name", "?"))
        match_time = m.get("event_time", "?")

        try:
            # ── Données AllSportsAPI ─────────────────────
            probas    = get_probabilities(match_id)
            odds      = get_odds_allsports(match_id)
            home_form = get_form_from_fixtures(home_id)
            away_form = get_form_from_fixtures(away_id)
            h2h       = get_h2h(home_id, away_id)
            weather   = get_weather(home)
            vbet      = find_value_bet(home, away, "football")

            home_fs = form_score(home_form)
            away_fs = form_score(away_form)

            # ── Proba AllSports ou Poisson si absent ─────
            if probas.get("home_win"):
                pred_home = probas["home_win"]
                pred_draw = probas["draw"]
                pred_away = probas["away_win"]
                btts_prob = probas.get("btts", 0.5)
                over_25   = probas.get("over_25", 0.5)
                over_15   = probas.get("over_15", 0.7)
                over_35   = probas.get("over_35", 0.3)
                # Lambda estimé depuis les probas
                home_lam = round(-math.log(1 - over_25) * 0.7, 2) if over_25 < 1 else 1.3
                away_lam = round(-math.log(1 - over_25) * 0.5, 2) if over_25 < 1 else 1.1
                _, _, _, top5_scores = poisson_matrix(home_lam, away_lam)
                goals_exp = round(home_lam + away_lam, 2)
            else:
                # Fallback Poisson
                league_avg = 1.35
                home_lam = round(max((home_fs * 2.5 + 0.5), 0.3), 2) * 1.1
                away_lam = round(max((away_fs * 2.5 + 0.5), 0.3), 2)
                pred_home, pred_draw, pred_away, top5_scores = poisson_matrix(home_lam, away_lam)
                goals_exp = round(home_lam + away_lam, 2)
                btts_prob = round((1 - math.exp(-home_lam)) * (1 - math.exp(-away_lam)), 3)
                over_25 = 1 - math.exp(-max(goals_exp - 2.5, 0))
                over_15 = 1 - math.exp(-max(goals_exp - 1.5, 0))
                over_35 = 1 - math.exp(-max(goals_exp - 3.5, 0))

            # ── Winner ───────────────────────────────────
            if pred_home > pred_away and pred_home > pred_draw:
                winner = f"🏠 {home}"
            elif pred_away > pred_home and pred_away > pred_draw:
                winner = f"✈️ {away}"
            else:
                winner = "🤝 Match Nul"

            # ── Cotes et value ───────────────────────────
            odd_1 = odds.get("1")
            odd_x = odds.get("X")
            odd_2 = odds.get("2")

            ip_home    = round(1/odd_1, 3) if odd_1 else None
            ip_away    = round(1/odd_2, 3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

            # ── Confiance ────────────────────────────────
            confidence = 30
            if probas:          confidence += 25
            if h2h["total"] >= 5: confidence += 20
            elif h2h["total"] >= 2: confidence += 10
            if home_form and away_form: confidence += 15
            if odd_1:           confidence += 10

            # ── Météo ─────────────────────────────────────
            w_impact, w_label = weather_impact(weather)

            # ── Lineups (via AllSports fixtures) ─────────
            lineups = m.get("lineups", {})
            has_lineup = bool(
                lineups.get("home_team", {}).get("starting_lineups") and
                lineups.get("away_team", {}).get("starting_lineups")
            )

            score = shadow_score(confidence, best_value, best_kelly, has_lineup, w_impact)

            # ── Boost si value bet API ────────────────────
            if vbet:
                score = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')} ({vbet.get('bookmaker','?')})"
            elif value_home and value_home > 0.05:
                verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05:
                verdict = f"🔥 VALUE AWAY ({value_away})"
            else:
                verdict = "⚪ Pas de value"

            label = pick_label(score)

            results.append({
                "sport":   "football",
                "league":  league,
                "home":    home,
                "away":    away,
                "time":    match_time,
                "event_id": match_id,
                "odds": {"1": odd_1, "X": odd_x, "2": odd_2,
                         "o25": odds.get("o25"), "u25": odds.get("u25"),
                         "btts_yes": odds.get("btts_yes")},
                "h2h": h2h,
                "form": {
                    "home": home_form, "away": away_form,
                    "home_score": home_fs, "away_score": away_fs,
                    "home_trend": get_trend(home_form),
                    "away_trend": get_trend(away_form),
                },
                "weather": weather,
                "weather_label": w_label,
                "value_bet_api": vbet,
                "prediction": {
                    "home_prob":      round(pred_home, 3),
                    "draw_prob":      round(pred_draw, 3),
                    "away_prob":      round(pred_away, 3),
                    "winner":         winner,
                    "confidence":     confidence,
                    "goals_expected": goals_exp,
                    "over_under":     f"⬆️ OVER 2.5" if over_25 > 0.5 else "⬇️ UNDER 2.5",
                    "over_15":        f"⬆️ OVER 1.5" if over_15 > 0.5 else "⬇️ UNDER 1.5",
                    "over_35":        f"⬆️ OVER 3.5" if over_35 > 0.5 else "⬇️ UNDER 3.5",
                    "btts":           f"⚽ BTTS {'OUI' if btts_prob > 0.5 else 'NON'} ({round(btts_prob*100)}%)",
                    "btts_prob":      round(btts_prob, 3),
                    "top5_scores":    top5_scores,
                    "home_lam":       home_lam,
                    "away_lam":       away_lam,
                },
                "value":        {"home": value_home, "away": value_away},
                "kelly":        {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict":      verdict,
                "shadow_score": score,
                "pick_label":   label,
            })
            print(f"  ✅ [{league}] {home} vs {away} — {score}/100 {verdict[:30]}")

        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    return results

# ════════════════════════════════════════════════════════
# ANALYSE HOCKEY / RUGBY (équipes — logique commune)
# ════════════════════════════════════════════════════════

def analyze_team_sport(sport_name, sport_key, leagues):
    print(f"\n🏒🏉 Analyse {sport_name}...")

    get_value_bets(sport_name)
    matches = get_fixtures(sport_key, list(leagues.keys()))
    print(f"  ✅ {len(matches)} matchs trouvés")

    results = []

    for m in matches:
        home       = m.get("event_home_team", "?")
        away       = m.get("event_away_team", "?")
        home_id    = m.get("home_team_key")
        away_id    = m.get("away_team_key")
        match_id   = m.get("event_key")
        league     = leagues.get(str(m.get("_league_id", "")), m.get("league_name", "?"))
        match_time = m.get("event_time", "?")

        try:
            odds      = get_odds_allsports(match_id, sport_key)
            home_form = get_form_from_fixtures(home_id, sport_key)
            away_form = get_form_from_fixtures(away_id, sport_key)
            h2h       = get_h2h(home_id, away_id)
            vbet      = find_value_bet(home, away, sport_name)

            home_fs = form_score(home_form)
            away_fs = form_score(away_form)

            # Prédiction H2H + forme
            t = h2h.get("total", 0)
            if t >= 8:   wh, wf = 0.65, 0.35
            elif t >= 4: wh, wf = 0.50, 0.50
            elif t >= 1: wh, wf = 0.30, 0.70
            else:        wh, wf = 0.10, 0.90

            h2h_ph = h2h["home_wins"] / t if t else 0.34
            h2h_pa = h2h["away_wins"] / t if t else 0.33
            h2h_pd = h2h["draws"]     / t if t else 0.33

            pred_home = round(h2h_ph * wh + home_fs * wf, 3)
            pred_away = round(h2h_pa * wh + away_fs * wf, 3)
            pred_draw = round(max(1 - pred_home - pred_away, 0), 3)

            if pred_home > pred_away and pred_home > pred_draw:
                winner = f"🏠 {home}"
            elif pred_away > pred_home and pred_away > pred_draw:
                winner = f"✈️ {away}"
            else:
                winner = "🤝 Match Nul"

            odd_1 = odds.get("1")
            odd_x = odds.get("X")
            odd_2 = odds.get("2")

            ip_home    = round(1/odd_1, 3) if odd_1 else None
            ip_away    = round(1/odd_2, 3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

            confidence = round(
                min(t / 10 * 40, 40) +
                min((len(home_form) + len(away_form)) / 10 * 40, 40) +
                (20 if odd_1 else 0)
            )

            score = shadow_score(confidence, best_value, best_kelly)

            if vbet:
                score = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')} ({vbet.get('bookmaker','?')})"
            elif value_home and value_home > 0.05:
                verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05:
                verdict = f"🔥 VALUE AWAY ({value_away})"
            else:
                verdict = "⚪ Pas de value"

            results.append({
                "sport": sport_name, "league": league,
                "home": home, "away": away,
                "time": match_time, "event_id": match_id,
                "odds": {"1": odd_1, "X": odd_x, "2": odd_2},
                "h2h": h2h,
                "form": {
                    "home": home_form, "away": away_form,
                    "home_score": home_fs, "away_score": away_fs,
                    "home_trend": get_trend(home_form),
                    "away_trend": get_trend(away_form),
                },
                "value_bet_api": vbet,
                "prediction": {
                    "home_prob": pred_home, "draw_prob": pred_draw, "away_prob": pred_away,
                    "winner": winner, "confidence": confidence,
                },
                "value": {"home": value_home, "away": value_away},
                "kelly": {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            })
            print(f"  ✅ [{league}] {home} vs {away} — {score}/100")

        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    return results

# ════════════════════════════════════════════════════════
# ANALYSE TENNIS — UTR/Elo SNIPER
# ════════════════════════════════════════════════════════

SURFACES_TENNIS = {
    "terre":  {"jeux_set": {"serré": 12, "équilibré": 10, "déséquilibré": 8}, "vol": "medium", "clutch": 1.1, "pressure": 0.9},
    "dur":    {"jeux_set": {"serré": 11, "équilibré": 9,  "déséquilibré": 7}, "vol": "medium", "clutch": 1.0, "pressure": 1.0},
    "gazon":  {"jeux_set": {"serré": 10, "équilibré": 8,  "déséquilibré": 6}, "vol": "high",   "clutch": 0.9, "pressure": 1.1},
    "indoor": {"jeux_set": {"serré": 11, "équilibré": 9,  "déséquilibré": 7}, "vol": "medium", "clutch": 1.0, "pressure": 1.0},
}

TOURNOIS_TENNIS = {
    "Grand Chelem": "high", "Grand Slam": "high",
    "Masters 1000": "medium", "ATP Masters": "medium",
    "ATP 500": "low", "ATP 250": "low",
    "WTA 1000": "medium", "WTA 500": "low",
}

def get_tennis_surface(tournament_name):
    name = (tournament_name or "").lower()
    if "clay" in name or "terre" in name or "roland" in name or "montecarlo" in name or "madrid" in name or "rome" in name:
        return "terre"
    if "grass" in name or "gazon" in name or "wimbledon" in name or "queen" in name or "halle" in name:
        return "gazon"
    if "indoor" in name or "paris" in name or "rotterdam" in name or "vienna" in name:
        return "indoor"
    return "dur"

def get_tennis_tournament_type(tournament_name):
    name = (tournament_name or "").lower()
    if any(x in name for x in ["grand slam", "grand chelem", "australian", "roland", "wimbledon", "us open"]):
        return "Grand Chelem"
    if any(x in name for x in ["masters 1000", "1000", "indian wells", "miami", "madrid", "rome", "montreal", "cincinnati", "shanghai", "paris", "toronto"]):
        return "Masters 1000"
    if "500" in name:
        return "ATP 500"
    return "ATP 250"

def elo_from_ranking(ranking):
    """Estime un Elo approximatif depuis le classement ATP/WTA."""
    if ranking <= 1:   return 2350
    if ranking <= 5:   return 2250
    if ranking <= 10:  return 2180
    if ranking <= 20:  return 2120
    if ranking <= 50:  return 2050
    if ranking <= 100: return 1980
    if ranking <= 200: return 1900
    return 1800

def utr_from_ranking(ranking):
    """Estime un UTR approximatif depuis le classement ATP/WTA."""
    if ranking <= 5:   return 16.0
    if ranking <= 20:  return 15.0
    if ranking <= 50:  return 14.0
    if ranking <= 100: return 13.0
    if ranking <= 200: return 12.0
    return 11.0

def tennis_sniper(
    utr_a, utr_b, elo_a, elo_b, cote_a, cote_b,
    sets, surface, tournament_type,
    forme_a=None, forme_b=None,
    ranking_a=100, ranking_b=100,
    h2h_wins_a=0, h2h_total=0,
):
    """Algo UTR/Elo Sniper complet."""
    surf = SURFACES_TENNIS.get(surface, SURFACES_TENNIS["dur"])

    # Proba de base
    proba_utr = 1 / (1 + 10 ** ((utr_b - utr_a) / 1.5))
    proba_elo = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    proba_a   = (proba_utr * 0.6) + (proba_elo * 0.4)
    proba_b   = 1 - proba_a

    # Profils
    def profil(elo):
        if elo > 2150: return "clutch"
        if elo < 2000: return "pressure"
        return "solide"

    prof_a = profil(elo_a)
    prof_b = profil(elo_b)

    # Ajustements surface
    proba_a *= surf.get(prof_a, 1.0)
    proba_b *= surf.get(prof_b, 1.0)

    # Forme
    if forme_a:
        wins_a = forme_a.count("W")
        proba_a *= 1.05 if wins_a >= 3 else (0.95 if wins_a <= 1 else 1.0)
    if forme_b:
        wins_b = forme_b.count("W")
        proba_b *= 1.05 if wins_b >= 3 else (0.95 if wins_b <= 1 else 1.0)

    # Classement
    if ranking_a <= 10:   proba_a *= 1.05
    elif ranking_a <= 20: proba_a *= 1.02
    if ranking_b <= 10:   proba_b *= 1.05
    elif ranking_b <= 20: proba_b *= 1.02

    # H2H
    if h2h_total > 0 and h2h_wins_a >= 3:
        proba_a *= 1.05

    # Normalisation
    total = proba_a + proba_b
    proba_a /= total
    proba_b  = 1 - proba_a

    # Volatilité
    diff_utr  = abs(utr_a - utr_b)
    diff_prob = abs(proba_a - proba_b)

    if prof_a == "pressure" and prof_b == "pressure":
        volatility = "high"
    elif diff_prob < 0.05:
        volatility = surf["vol"]
    else:
        volatility = "low"

    # Override tournoi
    t_vol = TOURNOIS_TENNIS.get(tournament_type)
    if t_vol:
        volatility = t_vol

    # Zone de jeux
    if diff_utr < 0.1:    jeux_key = "serré"
    elif diff_utr < 0.3:  jeux_key = "équilibré"
    else:                  jeux_key = "déséquilibré"

    jps  = surf["jeux_set"][jeux_key]
    n_sets = 3 if sets == 3 else 5
    low  = jps * (n_sets - 1)
    high = jps * n_sets
    mid  = (low + high) / 2
    line = round(mid) + 0.5

    prob_over  = (high - line) / max(high - low, 1)
    prob_under = 1 - prob_over

    # Edge bookmaker
    book_a = 1 / cote_a if cote_a else None
    book_b = 1 / cote_b if cote_b else None
    edge_a = proba_a - book_a if book_a else 0
    edge_b = proba_b - book_b if book_b else 0

    # Stratégie
    threshold = {"high": 0.55, "medium": 0.57, "low": 0.59}.get(volatility, 0.57)
    bet_type = bet_side = None
    stake = 0

    if edge_a > 0.02:
        bet_type, bet_side = "winner", "home"
        edge = edge_a
        stake = 1.2 if edge < 0.03 else (1.8 if edge < 0.05 else (2.5 if edge < 0.08 else 3.5))
    elif edge_b > 0.02:
        bet_type, bet_side = "winner", "away"
        edge = edge_b
        stake = 1.2 if edge < 0.03 else (1.8 if edge < 0.05 else (2.5 if edge < 0.08 else 3.5))
    elif volatility == "high":
        if prob_over > threshold:
            bet_type, bet_side = "games", "over"
            eg = prob_over - 0.5
            stake = 1.0 if eg < 0.05 else (1.5 if eg < 0.08 else (2.0 if eg < 0.12 else 2.5))
        elif prob_under > threshold:
            bet_type, bet_side = "games", "under"
            eg = prob_under - 0.5
            stake = 1.0 if eg < 0.05 else (1.5 if eg < 0.08 else (2.0 if eg < 0.12 else 2.5))

    if volatility == "high" and stake > 0:
        stake *= 0.75
    stake = round(max(0.8, min(stake, 3)), 2) if stake > 0 else 0

    return {
        "proba_home": round(proba_a, 3),
        "proba_away": round(proba_b, 3),
        "edge_home":  round(edge_a, 3),
        "edge_away":  round(edge_b, 3),
        "volatility": volatility,
        "surface":    surface,
        "zone":       (low, high),
        "line":       line,
        "prob_over":  round(prob_over, 3),
        "prob_under": round(prob_under, 3),
        "bet_type":   bet_type,
        "bet_side":   bet_side,
        "stake_pct":  stake,
        "profil_a":   prof_a,
        "profil_b":   prof_b,
        "utr_a":      utr_a,
        "utr_b":      utr_b,
        "elo_a":      elo_a,
        "elo_b":      elo_b,
    }

def analyze_tennis():
    print(f"\n🎾 Analyse Tennis...")

    get_value_bets("tennis")

    # AllSportsAPI a une API tennis
    matches_raw = allsports("tennis", {
        "met": "Fixtures",
        "from": today,
        "to": today,
    })
    matches = [m for m in matches_raw if m.get("event_status") in ("", "notstarted", None)]
    print(f"  ✅ {len(matches)} matchs trouvés")

    results = []

    for m in matches:
        home       = m.get("event_home_team", "?")
        away       = m.get("event_away_team", "?")
        home_id    = m.get("home_team_key")
        away_id    = m.get("away_team_key")
        match_id   = m.get("event_key")
        tournament = m.get("league_name", "ATP 250")
        match_time = m.get("event_time", "?")

        try:
            odds      = get_odds_allsports(match_id, "tennis")
            home_form = get_form_from_fixtures(home_id, "tennis")
            away_form = get_form_from_fixtures(away_id, "tennis")
            h2h_data  = get_h2h(home_id, away_id)
            vbet      = find_value_bet(home, away, "tennis")

            cote_a = odds.get("1") or 2.0
            cote_b = odds.get("2") or 2.0

            # Estime UTR/Elo depuis cotes (si pas de classement dispo)
            # La cote reflète le classement implicite
            impl_a = 1 / cote_a
            impl_b = 1 / cote_b
            # Ranking estimé depuis la cote implicite
            rank_a = max(1, int(200 * (1 - impl_a)))
            rank_b = max(1, int(200 * (1 - impl_b)))

            utr_a = utr_from_ranking(rank_a)
            utr_b = utr_from_ranking(rank_b)
            elo_a = elo_from_ranking(rank_a)
            elo_b = elo_from_ranking(rank_b)

            surface  = get_tennis_surface(tournament)
            tour_type = get_tennis_tournament_type(tournament)
            sets     = 5 if "Grand" in tour_type else 3

            sniper = tennis_sniper(
                utr_a=utr_a, utr_b=utr_b,
                elo_a=elo_a, elo_b=elo_b,
                cote_a=cote_a, cote_b=cote_b,
                sets=sets, surface=surface,
                tournament_type=tour_type,
                forme_a=home_form, forme_b=away_form,
                h2h_wins_a=h2h_data.get("home_wins", 0),
                h2h_total=h2h_data.get("total", 0),
            )

            pred_home = sniper["proba_home"]
            pred_away = sniper["proba_away"]
            winner    = f"🎾 {home}" if pred_home > pred_away else f"🎾 {away}"

            confidence = 40
            if h2h_data["total"] >= 3: confidence += 20
            if home_form and away_form: confidence += 20
            if odds.get("1"):           confidence += 20

            best_value = max(sniper["edge_home"], sniper["edge_away"])
            best_kelly = max(kelly(pred_home, cote_a), kelly(pred_away, cote_b))
            score      = shadow_score(confidence, best_value, best_kelly)

            if vbet:
                score   = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}"
            elif sniper["bet_type"]:
                if sniper["bet_type"] == "winner":
                    p = home if sniper["bet_side"] == "home" else away
                    verdict = f"🎾 BET {p} @ {cote_a if sniper['bet_side']=='home' else cote_b} (stake {sniper['stake_pct']}%)"
                else:
                    verdict = f"📊 BET {sniper['bet_side'].upper()} {sniper['line']} jeux (stake {sniper['stake_pct']}%)"
            else:
                verdict = "⚪ Pas de value"

            results.append({
                "sport": "tennis", "league": tournament,
                "home": home, "away": away,
                "time": match_time, "event_id": match_id,
                "odds": {"1": cote_a, "2": cote_b},
                "h2h": h2h_data,
                "form": {
                    "home": home_form, "away": away_form,
                    "home_score": form_score(home_form),
                    "away_score": form_score(away_form),
                    "home_trend": get_trend(home_form),
                    "away_trend": get_trend(away_form),
                },
                "value_bet_api": vbet,
                "prediction": {
                    "home_prob":   pred_home,
                    "away_prob":   pred_away,
                    "winner":      winner,
                    "confidence":  confidence,
                    "surface":     surface,
                    "tournament":  tour_type,
                    "volatility":  sniper["volatility"],
                    "zone":        sniper["zone"],
                    "line_jeux":   sniper["line"],
                    "bet_type":    sniper["bet_type"],
                    "bet_side":    sniper["bet_side"],
                    "stake_pct":   sniper["stake_pct"],
                    "profil_home": sniper["profil_a"],
                    "profil_away": sniper["profil_b"],
                    "edge_home":   sniper["edge_home"],
                    "edge_away":   sniper["edge_away"],
                },
                "value": {"home": sniper["edge_home"], "away": sniper["edge_away"]},
                "kelly": {"home": kelly(pred_home, cote_a), "away": kelly(pred_away, cote_b)},
                "verdict": verdict,
                "shadow_score": score,
                "pick_label": pick_label(score),
            })
            print(f"  ✅ [{tournament}] {home} vs {away} — {score}/100 {verdict[:30]}")

        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    return results

# ════════════════════════════════════════════════════════
# ANALYSE BASKETBALL — ESPN + BallDontLie + AllSports
# ════════════════════════════════════════════════════════

NBA_TEAMS_MAP = {
    "Boston Celtics": "Celtics", "Cleveland Cavaliers": "Cavaliers",
    "Indiana Pacers": "Pacers", "Miami Heat": "Heat",
    "New York Knicks": "Knicks", "Philadelphia 76ers": "76ers",
    "Toronto Raptors": "Raptors", "Brooklyn Nets": "Nets",
    "Charlotte Hornets": "Hornets", "Atlanta Hawks": "Hawks",
    "Chicago Bulls": "Bulls", "Dallas Mavericks": "Mavericks",
    "Houston Rockets": "Rockets", "Memphis Grizzlies": "Grizzlies",
    "Minnesota Timberwolves": "Timberwolves", "Oklahoma City Thunder": "Thunder",
    "Phoenix Suns": "Suns", "San Antonio Spurs": "Spurs",
    "Denver Nuggets": "Nuggets", "Los Angeles Lakers": "Lakers",
    "LA Clippers": "Clippers", "Golden State Warriors": "Warriors",
    "Portland Trail Blazers": "Trail Blazers", "Sacramento Kings": "Kings",
    "Utah Jazz": "Jazz", "New Orleans Pelicans": "Pelicans",
    "Washington Wizards": "Wizards", "Orlando Magic": "Magic",
    "Milwaukee Bucks": "Bucks", "Detroit Pistons": "Pistons",
}

BASKET_OU = {
    "nba": 224.5, "wnba": 168.5, "ncaa": 145.5,
    "euroleague": 162.5, "eurocup": 158.5,
    "acb": 168.5, "lega": 162.5,
    "bbl": 158.5, "pro a": 162.5,
    "turkish": 165.5, "bsl": 165.5,
    "vtb": 158.5, "nbb": 162.5,
    "kbl": 158.5, "nbl": 168.5,
}

def get_nba_games():
    try:
        r = requests.get(f"{ESPN_BASE}/scoreboard", headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        games = []
        for e in r.get("events", []):
            comp  = e.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            home  = next((t for t in teams if t["homeAway"] == "home"), {})
            away  = next((t for t in teams if t["homeAway"] == "away"), {})
            status = e.get("status", {}).get("type", {}).get("name", "")
            if status == "STATUS_FINAL":
                continue
            games.append({
                "game_id":  e.get("id"),
                "home":     home.get("team", {}).get("displayName", "?"),
                "away":     away.get("team", {}).get("displayName", "?"),
                "home_id":  home.get("team", {}).get("id"),
                "away_id":  away.get("team", {}).get("id"),
                "time":     e.get("date", "")[:16].replace("T", " "),
            })
        return games
    except Exception as e:
        print(f"  ❌ ESPN NBA: {e}")
        return []

def get_nba_standings():
    try:
        r = requests.get(f"{ESPN_WEB}/standings", headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        standings = {}
        for conf in r.get("children", []):
            for entry in conf.get("standings", {}).get("entries", []):
                team  = entry.get("team", {}).get("displayName", "?")
                stats = {s["name"]: s.get("displayValue") for s in entry.get("stats", [])}
                standings[team] = {
                    "wins":   stats.get("wins", "?"),
                    "losses": stats.get("losses", "?"),
                    "pct":    float(stats.get("winPercent", 0.5) or 0.5),
                    "last10": stats.get("lastTen", "?"),
                }
        return standings
    except:
        return {}

def get_nba_team_stats(team_id):
    try:
        r    = requests.get(f"{ESPN_BASE}/teams/{team_id}/statistics", headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
        cats = r.get("results", {}).get("stats", {}).get("categories", [])
        stats = {}
        for cat in cats:
            for s in cat.get("stats", []):
                stats[s["name"]] = s.get("displayValue", "?")
        return stats
    except:
        return {}

def get_espn_advanced(team_id):
    try:
        r    = requests.get(f"{ESPN_BASE}/teams/{team_id}/statistics", headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
        cats = r.get("results", {}).get("stats", {}).get("categories", [])
        stats = {}
        for cat in cats:
            for s in cat.get("stats", []):
                stats[s.get("name", "")] = s.get("value", 0)
        return {
            "off_rtg": float(stats.get("offensiveRating", 0)),
            "def_rtg": float(stats.get("defensiveRating", 0)),
            "pace":    float(stats.get("pace", 100)),
            "net_rtg": float(stats.get("netRating", 0)),
        }
    except:
        return {}

def get_bdl_form(team_name):
    if not BALLDONTLIE_KEY:
        return []
    search = NBA_TEAMS_MAP.get(team_name, team_name)
    try:
        r = requests.get(f"{BDL_BASE}/teams", headers=HEADERS_BDL,
                         params={"search": search}, timeout=10).json()
        if not r.get("data"):
            return []
        tid = r["data"][0]["id"]
        games = requests.get(f"{BDL_BASE}/games", headers=HEADERS_BDL,
                             params={"team_ids[]": tid, "per_page": 5, "seasons[]": 2025},
                             timeout=10).json()
        form = []
        for g in games.get("data", []):
            hs  = g.get("home_team_score", 0)
            aws = g.get("visitor_team_score", 0)
            ht  = g.get("home_team", {}).get("id")
            form.append("W" if (hs > aws and ht == tid) or (aws > hs and ht != tid) else "L")
        return form
    except:
        return []

def analyze_basketball():
    print(f"\n🏀 Analyse Basketball...")

    get_value_bets("basketball")

    # ── NBA via ESPN ──────────────────────────────────────
    nba_results = []
    games     = get_nba_games()
    standings = get_nba_standings()
    print(f"  ✅ {len(games)} matchs NBA")

    for game in games:
        home    = game["home"]
        away    = game["away"]
        home_id = game["home_id"]
        away_id = game["away_id"]

        home_stats = get_nba_team_stats(home_id)
        away_stats = get_nba_team_stats(away_id)
        home_adv   = get_espn_advanced(home_id)
        away_adv   = get_espn_advanced(away_id)
        home_form  = get_bdl_form(home)
        away_form  = get_bdl_form(away)
        home_std   = standings.get(home, {})
        away_std   = standings.get(away, {})
        vbet       = find_value_bet(home, away, "basketball")

        def fs(f): return sum(1 for r in f if r == "W") / len(f) if f else 0.5
        home_fs  = fs(home_form)
        away_fs  = fs(away_form)
        home_pct = home_std.get("pct", 0.5)
        away_pct = away_std.get("pct", 0.5)

        home_net = home_adv.get("net_rtg", 0)
        away_net = away_adv.get("net_rtg", 0)
        net_diff = (home_net - away_net) / 20

        pred_home = round(home_fs * 0.35 + home_pct * 0.45 + max(net_diff, 0) * 0.20, 3)
        pred_away = round(away_fs * 0.35 + away_pct * 0.45 + max(-net_diff, 0) * 0.20, 3)
        total_p   = pred_home + pred_away
        pred_home = round(pred_home / total_p, 3) if total_p else 0.5
        pred_away = round(1 - pred_home, 3)

        winner = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

        # O/U NBA avec Pace
        try:
            home_ppg  = float(home_stats.get("avgPoints", 0) or 0)
            away_ppg  = float(away_stats.get("avgPoints", 0) or 0)
            home_pace = home_adv.get("pace", 100)
            away_pace = away_adv.get("pace", 100)
            pace_adj  = ((home_pace + away_pace) / 2 - 100) * 0.5
            total_pts = round(home_ppg + away_ppg + pace_adj, 1)
            ou_line   = 224.5
            if total_pts == 0: total_pts = ou_line
            over_under = f"⬆️ OVER {ou_line} ({total_pts}pts)" if total_pts > ou_line else f"⬇️ UNDER {ou_line} ({total_pts}pts)"
        except:
            total_pts = 0; over_under = "❓"

        confidence = 50
        if home_form and away_form: confidence += 15
        if home_std and away_std:   confidence += 15
        if home_adv and away_adv:   confidence += 10
        score = min(confidence + (15 if vbet else 0), 100)

        if vbet:
            verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}"
        else:
            verdict = "⚪ Pas de value"

        nba_results.append({
            "sport": "basketball", "league": "NBA",
            "home": home, "away": away,
            "time": game["time"], "event_id": game["game_id"],
            "odds": {"1": round(1/pred_home, 2) if pred_home else None,
                     "2": round(1/pred_away, 2) if pred_away else None},
            "standings": {"home": home_std, "away": away_std},
            "form": {
                "home": home_form, "away": away_form,
                "home_trend": get_trend(home_form),
                "away_trend": get_trend(away_form),
            },
            "advanced": {"home": home_adv, "away": away_adv},
            "value_bet_api": vbet,
            "prediction": {
                "home_prob": pred_home, "away_prob": pred_away,
                "winner": winner, "confidence": confidence,
                "over_under": over_under, "total_pts": total_pts,
            },
            "value": {}, "kelly": {},
            "verdict": verdict,
            "shadow_score": score,
            "pick_label": pick_label(score),
        })

    # ── Autres ligues basket via AllSports ────────────────
    other_results = []
    other_matches = get_fixtures("basketball", list(BASKETBALL_LEAGUES.keys()))
    nba_keys = {f"{r['home']}_{r['away']}" for r in nba_results}

    for m in other_matches:
        home    = m.get("event_home_team", "?")
        away    = m.get("event_away_team", "?")
        if f"{home}_{away}" in nba_keys:
            continue
        home_id  = m.get("home_team_key")
        away_id  = m.get("away_team_key")
        match_id = m.get("event_key")
        league   = BASKETBALL_LEAGUES.get(str(m.get("_league_id", "")), m.get("league_name", "Other"))
        match_time = m.get("event_time", "?")

        try:
            odds      = get_odds_allsports(match_id, "basketball")
            home_form = get_form_from_fixtures(home_id, "basketball")
            away_form = get_form_from_fixtures(away_id, "basketball")
            h2h_data  = get_h2h(home_id, away_id)
            vbet      = find_value_bet(home, away, "basketball")

            home_fs = form_score(home_form)
            away_fs = form_score(away_form)
            t = h2h_data.get("total", 0)

            pred_home = round((h2h_data["home_wins"]/t if t else 0.34) * 0.4 + home_fs * 0.6, 3)
            pred_away = round((h2h_data["away_wins"]/t if t else 0.33) * 0.4 + away_fs * 0.6, 3)
            total_p   = pred_home + pred_away
            pred_home = round(pred_home / total_p, 3) if total_p else 0.5
            pred_away = round(1 - pred_home, 3)
            winner    = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

            odd_1 = odds.get("1")
            odd_2 = odds.get("2")

            # O/U dynamique
            ou_line = 162.5
            lg_lower = league.lower()
            for k, v in BASKET_OU.items():
                if k in lg_lower:
                    ou_line = v
                    break
            total_pts  = round((home_fs + away_fs) * ou_line * 0.95, 1)
            if total_pts == 0: total_pts = ou_line
            over_under = f"⬆️ OVER {ou_line} ({total_pts}pts)" if total_pts > ou_line else f"⬇️ UNDER {ou_line} ({total_pts}pts)"

            confidence = round(min(t/10*40, 40) + min((len(home_form)+len(away_form))/10*40, 40) + (20 if odd_1 else 0))
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))
            ip_home    = round(1/odd_1, 3) if odd_1 else None
            ip_away    = round(1/odd_2, 3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            score      = shadow_score(confidence, best_value, best_kelly)

            if vbet:
                score = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}"
            elif value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
            else: verdict = "⚪ Pas de value"

            other_results.append({
                "sport": "basketball", "league": league,
                "home": home, "away": away,
                "time": match_time, "event_id": match_id,
                "odds": {"1": odd_1, "2": odd_2},
                "h2h": h2h_data,
                "form": {
                    "home": home_form, "away": away_form,
                    "home_score": home_fs, "away_score": away_fs,
                    "home_trend": get_trend(home_form),
                    "away_trend": get_trend(away_form),
                },
                "value_bet_api": vbet,
                "prediction": {
                    "home_prob": pred_home, "away_prob": pred_away,
                    "winner": winner, "confidence": confidence,
                    "over_under": over_under,
                },
                "value": {"home": value_home, "away": value_away},
                "kelly": {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            })
        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    print(f"  ✅ {len(other_results)} autres matchs basket")
    return nba_results + other_results

# ════════════════════════════════════════════════════════
# ENVOI VERS RENDER
# ════════════════════════════════════════════════════════

def wake_server():
    try:
        r = requests.get(f"{RENDER_URL}/api", timeout=10)
        print(f"☀️  Render réveillé → {r.status_code}")
        time.sleep(2)
    except:
        pass

def send_to_server(sport, results):
    try:
        r = requests.post(
            f"{RENDER_URL}/ingest/{sport}",
            json={"date": today, "matches": results},
            timeout=20
        )
        print(f"  📡 /ingest/{sport} → {r.status_code} ({len(results)} matchs)")
    except Exception as e:
        print(f"  ❌ Erreur {sport}: {e}")

def print_top5(results, sport):
    top5 = sorted(
        [r for r in results if r.get("verdict", "") != "⚪ Pas de value"],
        key=lambda x: x.get("shadow_score", 0), reverse=True
    )[:5]
    if not top5:
        print(f"  Aucun value bet détecté pour {sport}")
        return
    print(f"\n  🏆 TOP 5 {sport.upper()} :")
    for i, r in enumerate(top5, 1):
        pred  = r.get("prediction", {})
        score = r.get("shadow_score", 0)
        print(f"  #{i} ({score}/100) {r['home']} vs {r['away']} [{r.get('league','?')}]")
        print(f"     → {pred.get('winner','?')} | {r.get('verdict','')}")

# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

if __name__ == "__main__":

    if not ALLSPORTS_KEY:
        print("❌ ALLSPORTS_KEY manquante ! export ALLSPORTS_KEY='ta_clé'")
        sys.exit(1)

    arg    = sys.argv[1] if len(sys.argv) > 1 else "all"
    target = arg if arg in ("all","football","basketball","tennis","hockey","rugby") else "all"

    print(f"🚀 Shadow Edge V∞ — {today} {now.strftime('%H:%M')}")
    print(f"🎯 Sport: {target}")
    print(f"📡 Render: {RENDER_URL}")
    print("=" * 50)

    wake_server()

    if target in ("all", "football"):
        results = analyze_football()
        print_top5(results, "football")
        send_to_server("football", results)

    if target in ("all", "basketball"):
        results = analyze_basketball()
        print_top5(results, "basketball")
        send_to_server("basketball", results)

    if target in ("all", "tennis"):
        results = analyze_tennis()
        print_top5(results, "tennis")
        send_to_server("tennis", results)

    if target in ("all", "hockey"):
        results = analyze_team_sport("hockey", "hockey", HOCKEY_LEAGUES)
        print_top5(results, "hockey")
        send_to_server("hockey", results)

    if target in ("all", "rugby"):
        results = analyze_team_sport("rugby", "rugby", RUGBY_LEAGUES)
        print_top5(results, "rugby")
        send_to_server("rugby", results)

    print(f"\n✅ Shadow Edge V∞ terminé — {now.strftime('%H:%M')} !")
