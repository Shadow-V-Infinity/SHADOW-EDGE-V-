from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import os
import math
import threading
import time
from datetime import date, datetime

try:
    from app.routers import nba_live
    NBA_LIVE_OK = True
except Exception as e:
    print(f"⚠️  NBA Live router non chargé: {e}")
    NBA_LIVE_OK = False

_scrape_lock = threading.Lock()

app = FastAPI(title="Shadow Edge V∞", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CLÉS API
# ============================================================
ALLSPORTS_KEY       = os.getenv("ALLSPORTS_KEY", "")
BALLDONTLIE_KEY     = os.getenv("BALLDONTLIE_API_KEY", "")
ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "")
OPENWEATHER_KEY     = os.getenv("OPENWEATHER_KEY", "")
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN", os.getenv("FOOTBALL-DATA-TOKEN", ""))

ALLSPORTS_BASE = "https://apiv2.allsportsapi.com"
ODDS_API_BASE  = "https://api.odds-api.io/v3"
FD_BASE        = "https://api.football-data.org/v4"
FD_HEADERS     = lambda: {"X-Auth-Token": FOOTBALL_DATA_TOKEN} if FOOTBALL_DATA_TOKEN else {}

# Codes Football-Data pour les ligues (code → AllSports league_id)
FD_LEAGUE_CODES = {
    "PL":  "148",   # Premier League
    "PD":  "302",   # La Liga
    "SA":  "207",   # Serie A
    "FL1": "168",   # Ligue 1
    "BL1": "175",   # Bundesliga
    "CL":  "244",   # Champions League
    "EL":  "245",   # Europa League
    "ECL": "247",   # Conference League
    "PPL": "320",   # Primeira Liga
    "BSA": "73",    # Brasileirao
}
ESPN_BASE      = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_WEB       = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba"
ESPN_NHL_BASE  = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
ESPN_NHL_WEB   = "https://site.web.api.espn.com/apis/v2/sports/hockey/nhl"
ESPN_RUG_BASE  = "https://site.api.espn.com/apis/site/v2/sports/rugby"
ESPN_RUG_WEB   = "https://site.web.api.espn.com/apis/v2/sports/rugby"

# Slugs ESPN pour les ligues rugby
ESPN_RUGBY_SLUGS = {
    "67": ("urt.top_14",       "Top 14"),
    "68": ("urt.prod2",        "Pro D2"),
    "69": ("ure.european_rcc", "Champions Cup"),
    "70": ("ure.premiership",  "Premiership"),
}
BDL_BASE       = "https://api.balldontlie.io/v1"
HEADERS_BDL    = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

# ============================================================
# STORE
# ============================================================
store = {
    "football":   {"date": None, "matches": [], "top10": [], "last_scrape": None},
    "basketball": {"date": None, "matches": [], "top10": [], "last_scrape": None},
    "tennis":     {"date": None, "matches": [], "top10": [], "last_scrape": None},
    "hockey":     {"date": None, "matches": [], "top10": [], "last_scrape": None},
    "rugby":      {"date": None, "matches": [], "top10": [], "last_scrape": None},
}
scrape_status = {"running": False, "last_run": None, "error": None}

# ============================================================
# LIGUES
# ============================================================
FOOTBALL_LEAGUES = {
    "148": "Premier League", "302": "La Liga",
    "207": "Serie A", "168": "Ligue 1", "175": "Bundesliga",
    "244": "Champions League", "245": "Europa League", "247": "Conference League",
    "152": "MLS", "320": "Primeira Liga", "73": "Brasileirao",
    "203": "Süper Lig", "501": "Scottish Premiership",
}
BASKETBALL_LEAGUES = {
    "12": "NBA", "132": "EuroLeague", "133": "EuroCup",
    "134": "ACB", "139": "Lega Basket", "141": "Pro A",
}
HOCKEY_LEAGUES = {
    "57": "NHL", "59": "DEL", "60": "National League",
    "61": "SHL", "62": "Liiga", "64": "Ligue Magnus",
}
RUGBY_LEAGUES = {
    "67": "Top 14", "68": "Pro D2",
    "69": "Champions Cup", "70": "Premiership",
}
BASKET_OU = {
    "nba": 224.5, "euroleague": 162.5, "eurocup": 158.5,
    "acb": 168.5, "lega": 162.5, "pro a": 162.5,
}
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

# ============================================================
# HTTP UTILS
# ============================================================
def allsports(sport, params):
    try:
        r = requests.get(
            f"{ALLSPORTS_BASE}/{sport}/",
            params={"APIkey": ALLSPORTS_KEY, **params},
            timeout=12
        )
        if r.status_code == 200:
            return r.json().get("result", []) or []
    except Exception as e:
        print(f"  ❌ AllSports {sport} {params.get('met')}: {e}")
    return []

def odds_api_call(endpoint, params={}):
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

# ============================================================
# ALGOS COMMUNS
# ============================================================
def form_score(form):
    pts = {"W": 3, "D": 1, "L": 0}
    return sum(pts.get(r, 0) for r in form) / (len(form) * 3) if form else 0

def get_trend(form):
    if len(form) < 3: return "❓"
    pts = {"W": 3, "D": 1, "L": 0}
    recent = sum(pts.get(r, 0) for r in form[:2]) / 2
    older  = sum(pts.get(r, 0) for r in form[2:]) / max(len(form[2:]), 1)
    if   recent > older + 0.5: return "📈 En hausse"
    elif recent < older - 0.5: return "📉 En baisse"
    else: return "➡️ Stable"

def kelly(prob, odd):
    if not prob or not odd or odd <= 1: return 0
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
    else: return "❌ ÉVITER"

def poisson_matrix(home_lam, away_lam, max_goals=7):
    def p(lam, k): return (math.exp(-lam) * lam**k) / math.factorial(k)
    hw = dr = aw = 0
    scores = {}
    for h in range(max_goals):
        for a in range(max_goals):
            prob = p(home_lam, h) * p(away_lam, a)
            if h > a: hw += prob
            elif h == a: dr += prob
            else: aw += prob
            scores[f"{h}-{a}"] = round(prob, 4)
    top5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return round(hw, 3), round(dr, 3), round(aw, 3), top5

# ============================================================
# ALLSPORTS DATA
# ============================================================
def get_fixtures(sport_key, league_ids):
    today = date.today().strftime("%Y-%m-%d")
    results = []
    for lid in league_ids:
        data = allsports(sport_key, {"met": "Fixtures", "from": today, "to": today, "leagueId": lid})
        for m in data:
            if m.get("event_status") not in ("", "notstarted", None): continue
            m["_league_id"] = lid
            results.append(m)
    return results

def get_h2h(home_id, away_id):
    data = allsports("football", {"met": "H2H", "firstTeamId": home_id, "secondTeamId": away_id})
    if isinstance(data, dict):
        h2h_matches = data.get("H2H", [])
        hw = dr = 0
        for m in h2h_matches:
            res = m.get("event_final_result", "0 - 0")
            try:
                h, a = [int(x.strip()) for x in res.split(" - ")]
                if str(home_id) == str(m.get("home_team_key")):
                    if h > a: hw += 1
                    elif h == a: dr += 1
                else:
                    if a > h: hw += 1
                    elif h == a: dr += 1
            except: continue
        aw = len(h2h_matches) - hw - dr
        return {"home_wins": hw, "away_wins": aw, "draws": dr, "total": len(h2h_matches)}
    return {"home_wins": 0, "away_wins": 0, "draws": 0, "total": 0}

def get_form_from_fixtures(team_id, sport_key="football", n=5):
    today = date.today().strftime("%Y-%m-%d")
    data = allsports(sport_key, {"met": "Fixtures", "teamId": team_id, "from": "2024-07-01", "to": today})
    finished = sorted([m for m in data if m.get("event_status") == "Finished"],
                      key=lambda x: x.get("event_date", ""), reverse=True)[:n]
    form = []
    for m in finished:
        try:
            h, a = [int(x.strip()) for x in m.get("event_final_result", "0 - 0").split(" - ")]
            if str(team_id) == str(m.get("home_team_key")):
                form.append("W" if h > a else ("D" if h == a else "L"))
            else:
                form.append("W" if a > h else ("D" if h == a else "L"))
        except: continue
    return form

def get_probabilities(match_id, sport_key="football"):
    data = allsports(sport_key, {"met": "Probabilities", "matchId": match_id})
    if data and isinstance(data, list):
        p = data[0]
        return {
            "home_win": float(p.get("event_HW", 33) or 33) / 100,
            "draw":     float(p.get("event_D",  33) or 33) / 100,
            "away_win": float(p.get("event_AW", 33) or 33) / 100,
            "btts":     float(p.get("event_bts", 50) or 50) / 100,
            "over_25":  float(p.get("event_O",  50) or 50) / 100,
            "over_15":  float(p.get("event_O_1", 70) or 70) / 100,
            "over_35":  float(p.get("event_O_3", 30) or 30) / 100,
        }
    return {}

def get_odds_allsports(match_id, sport_key="football"):
    data = allsports(sport_key, {"met": "Odds", "matchId": match_id})
    if isinstance(data, dict) and str(match_id) in data:
        bk = (data[str(match_id)] or [{}])[0]
        return {
            "1": float(bk.get("odd_1", 0) or 0) or None,
            "X": float(bk.get("odd_x", 0) or 0) or None,
            "2": float(bk.get("odd_2", 0) or 0) or None,
            "o25": float(bk.get("o+2.5", 0) or 0) or None,
            "u25": float(bk.get("u+2.5", 0) or 0) or None,
            "o15": float(bk.get("o+1.5", 0) or 0) or None,
            "btts_yes": float(bk.get("bts_yes", 0) or 0) or None,
        }
    return {}

# ============================================================
# VALUE BETS
# ============================================================
_vbets_cache = {}

def get_value_bets(sport):
    if sport in _vbets_cache: return _vbets_cache[sport]
    sport_map = {"football": "football", "basketball": "basketball",
                 "tennis": "tennis", "hockey": "ice-hockey", "rugby": "rugby-union"}
    vbs = odds_api_call("value-bets", {"sport": sport_map.get(sport, sport), "includeEventDetails": "true"})
    _vbets_cache[sport] = vbs if isinstance(vbs, list) else []
    print(f"  ✅ Value bets {sport}: {len(_vbets_cache[sport])}")
    return _vbets_cache[sport]

def find_value_bet(home, away, sport):
    for vb in get_value_bets(sport):
        ev = vb.get("event", {})
        h = ev.get("homeTeam", {}).get("name", "") or ev.get("home", "")
        a = ev.get("awayTeam", {}).get("name", "") or ev.get("away", "")
        if (any(w in h for w in home.split() if len(w) > 3) and
            any(w in a for w in away.split() if len(w) > 3)):
            return {"value": round(float(vb.get("value", 0) or 0), 3),
                    "odd": round(float(vb.get("price", 0) or 0), 2),
                    "bookmaker": vb.get("bookmaker", "?"),
                    "market": vb.get("market", "?"),
                    "selection": vb.get("selection", "?")}
    return {}

# ============================================================
# MÉTÉO
# ============================================================
STADIUMS = {
    "Arsenal": (51.5549, -0.1084), "Liverpool": (53.4308, -2.9608),
    "Chelsea": (51.4816, -0.1910), "Manchester City": (53.4831, -2.2004),
    "Manchester United": (53.4631, -2.2913), "Tottenham": (51.6042, -0.0665),
    "Real Madrid": (40.4531, -3.6883), "FC Barcelona": (41.3809, 2.1228),
    "Juventus": (45.1096, 7.6413), "Milan": (45.4781, 9.1240),
    "Paris Saint-Germain": (48.8414, 2.2530), "Borussia Dortmund": (51.4926, 7.4518),
}

def get_weather(team):
    if not OPENWEATHER_KEY: return None
    coords = STADIUMS.get(team)
    if not coords: return None
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"lat": coords[0], "lon": coords[1],
                                 "appid": OPENWEATHER_KEY, "units": "metric"}, timeout=5).json()
        return {"temp": round(r.get("main", {}).get("temp", 15), 1),
                "wind": round(r.get("wind", {}).get("speed", 0) * 3.6, 1),
                "rain": round(r.get("rain", {}).get("1h", 0), 2),
                "desc": r.get("weather", [{}])[0].get("description", "")}
    except: return None

def weather_impact(w):
    if not w: return 0, "❓"
    impact, labels = 0, []
    if w["rain"] > 5:    impact -= 15; labels.append("🌧️ Forte pluie")
    elif w["rain"] > 1:  impact -= 7;  labels.append("🌦️ Pluie légère")
    if w["wind"] > 50:   impact -= 12; labels.append("💨 Vent violent")
    elif w["wind"] > 30: impact -= 5;  labels.append("💨 Vent modéré")
    if w["temp"] > 32:   impact -= 8;  labels.append("🥵 Chaleur")
    elif w["temp"] < 2:  impact -= 5;  labels.append("❄️ Froid")
    else:                impact += 5;  labels.append("☀️ Favorable")
    return impact, " | ".join(labels)

# ============================================================
# FOOTBALL-DATA.ORG
# ============================================================
_fd_matches_cache  = {}   # date → liste matchs
_fd_standing_cache = {}   # code → standings

def fd_get(endpoint, params={}):
    """Appel Football-Data v4 — retourne le JSON ou {}."""
    if not FOOTBALL_DATA_TOKEN:
        return {}
    try:
        r = requests.get(
            f"{FD_BASE}/{endpoint}",
            headers=FD_HEADERS(),
            params=params,
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        print(f"  ⚠️  Football-Data {endpoint}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ❌ Football-Data {endpoint}: {e}")
    return {}

def fd_get_today_matches():
    """Matchs du jour toutes compétitions — 1 seul appel API."""
    today = date.today().strftime("%Y-%m-%d")
    if today in _fd_matches_cache:
        return _fd_matches_cache[today]
    data = fd_get("matches", {"date": today})
    matches = data.get("matches", [])
    _fd_matches_cache[today] = matches
    print(f"  ✅ Football-Data: {len(matches)} matchs aujourd'hui")
    return matches

def fd_get_standings(competition_code):
    """Classement d'une compétition — 1 appel par ligue, mis en cache."""
    if competition_code in _fd_standing_cache:
        return _fd_standing_cache[competition_code]
    data = fd_get(f"competitions/{competition_code}/standings")
    standings_raw = data.get("standings", [])
    # On prend la table "TOTAL" (home+away combinés)
    table = next((s["table"] for s in standings_raw if s.get("type") == "TOTAL"), [])
    standings = {}
    for row in table:
        team = row.get("team", {}).get("name", "?")
        standings[team] = {
            "position": row.get("position", 99),
            "points":   row.get("points", 0),
            "played":   row.get("playedGames", 0),
            "won":      row.get("won", 0),
            "draw":     row.get("draw", 0),
            "lost":     row.get("lost", 0),
            "gf":       row.get("goalsFor", 0),
            "ga":       row.get("goalsAgainst", 0),
            "gd":       row.get("goalDifference", 0),
            "form":     row.get("form", ""),          # ex: "W,D,L,W,W"
        }
    _fd_standing_cache[competition_code] = standings
    return standings

def fd_build_index(fd_matches):
    """
    Construit un index (home_name_lower, away_name_lower) → match FD
    pour le merge rapide avec AllSports.
    """
    idx = {}
    for m in fd_matches:
        home = m.get("homeTeam", {}).get("name", "").lower()
        away = m.get("awayTeam", {}).get("name", "").lower()
        if home and away:
            idx[(home, away)] = m
    return idx

def fd_match_teams(allsports_home, allsports_away, fd_index):
    """
    Cherche le match FD correspondant au match AllSports.
    Essaie d'abord exact, puis substring sur le mot le plus long.
    """
    h = allsports_home.lower()
    a = allsports_away.lower()
    # Exact
    if (h, a) in fd_index:
        return fd_index[(h, a)]
    # Substring — on cherche la paire dont les noms se contiennent mutuellement
    for (fh, fa), m in fd_index.items():
        h_match = any(w in fh for w in h.split() if len(w) > 3) or any(w in h for w in fh.split() if len(w) > 3)
        a_match = any(w in fa for w in a.split() if len(w) > 3) or any(w in a for w in fa.split() if len(w) > 3)
        if h_match and a_match:
            return m
    return None

def fd_form_to_list(form_str):
    """Convertit 'W,D,L,W,W' → ['W','D','L','W','W']."""
    if not form_str:
        return []
    return [r.strip() for r in form_str.split(",") if r.strip() in ("W", "D", "L")]

# ============================================================
# FOOTBALL
# ============================================================
def analyze_football():
    print(f"\n⚽ Analyse Football...")
    get_value_bets("football")
    matches = get_fixtures("football", list(FOOTBALL_LEAGUES.keys()))
    print(f"  ✅ {len(matches)} matchs AllSports")

    # ── Football-Data : 1 appel pour tous les matchs du jour ──
    fd_matches = fd_get_today_matches()
    fd_index   = fd_build_index(fd_matches)

    # Classements FD par ligue (1 appel par code, mis en cache)
    fd_standings_by_league = {}
    for code in FD_LEAGUE_CODES:
        fd_standings_by_league[code] = fd_get_standings(code)

    # Map AllSports league_id → code FD pour retrouver le bon classement
    allsports_to_fd_code = {v: k for k, v in FD_LEAGUE_CODES.items()}

    results = []

    for m in matches:
        home     = m.get("event_home_team", "?")
        away     = m.get("event_away_team", "?")
        home_id  = m.get("home_team_key")
        away_id  = m.get("away_team_key")
        match_id = m.get("event_key")
        lid      = str(m.get("_league_id", ""))
        league   = FOOTBALL_LEAGUES.get(lid, m.get("league_name", "?"))
        match_time = m.get("event_time", "?")

        try:
            probas    = get_probabilities(match_id)
            odds      = get_odds_allsports(match_id)
            home_form = get_form_from_fixtures(home_id)
            away_form = get_form_from_fixtures(away_id)
            h2h       = get_h2h(home_id, away_id)
            weather   = get_weather(home)
            vbet      = find_value_bet(home, away, "football")
            home_fs   = form_score(home_form)
            away_fs   = form_score(away_form)

            # ── Merge Football-Data ──────────────────────────
            fd_match   = fd_match_teams(home, away, fd_index)
            fd_code    = allsports_to_fd_code.get(lid)
            fd_std     = fd_standings_by_league.get(fd_code, {}) if fd_code else {}
            home_std   = fd_std.get(home) or fd_std.get(next((k for k in fd_std if any(w in k.lower() for w in home.lower().split() if len(w)>3)), ""), {})
            away_std   = fd_std.get(away) or fd_std.get(next((k for k in fd_std if any(w in k.lower() for w in away.lower().split() if len(w)>3)), ""), {})

            # Forme FD (5 derniers matchs) — enrichit la forme AllSports si absente
            fd_form_home = fd_form_to_list(home_std.get("form", "")) if home_std else []
            fd_form_away = fd_form_to_list(away_std.get("form", "")) if away_std else []
            if not home_form and fd_form_home:
                home_form = fd_form_home
                home_fs   = form_score(home_form)
            if not away_form and fd_form_away:
                away_form = fd_form_away
                away_fs   = form_score(away_form)

            has_fd = bool(fd_match)

            # ── Lambdas Poisson ──────────────────────────────
            if probas.get("home_win"):
                pred_home = probas["home_win"]
                pred_draw = probas["draw"]
                pred_away = probas["away_win"]
                btts_prob = probas.get("btts", 0.5)
                over_25   = probas.get("over_25", 0.5)
                over_15   = probas.get("over_15", 0.7)
                over_35   = probas.get("over_35", 0.3)
                home_lam  = round(-math.log(max(1 - over_25, 0.01)) * 0.7, 2)
                away_lam  = round(-math.log(max(1 - over_25, 0.01)) * 0.5, 2)
                _, _, _, top5_scores = poisson_matrix(home_lam, away_lam)
                goals_exp = round(home_lam + away_lam, 2)
            else:
                # Si classement FD dispo → lambdas basés sur buts réels
                if home_std and away_std and home_std.get("played", 0) > 0:
                    home_lam = round((home_std["gf"] / home_std["played"] + away_std["ga"] / away_std["played"]) / 2, 2)
                    away_lam = round((away_std["gf"] / away_std["played"] + home_std["ga"] / home_std["played"]) / 2, 2)
                else:
                    home_lam = round(max((home_fs * 2.5 + 0.5), 0.3), 2) * 1.1
                    away_lam = round(max((away_fs * 2.5 + 0.5), 0.3), 2)
                pred_home, pred_draw, pred_away, top5_scores = poisson_matrix(home_lam, away_lam)
                goals_exp = round(home_lam + away_lam, 2)
                btts_prob = round((1 - math.exp(-home_lam)) * (1 - math.exp(-away_lam)), 3)
                over_25 = 1 - math.exp(-max(goals_exp - 2.5, 0))
                over_15 = 1 - math.exp(-max(goals_exp - 1.5, 0))
                over_35 = 1 - math.exp(-max(goals_exp - 3.5, 0))

            if pred_home > pred_away and pred_home > pred_draw: winner = f"🏠 {home}"
            elif pred_away > pred_home and pred_away > pred_draw: winner = f"✈️ {away}"
            else: winner = "🤝 Match Nul"

            odd_1 = odds.get("1"); odd_x = odds.get("X"); odd_2 = odds.get("2")
            ip_home    = round(1/odd_1, 3) if odd_1 else None
            ip_away    = round(1/odd_2, 3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

            confidence = 30
            if probas:               confidence += 20
            if h2h["total"] >= 5:   confidence += 15
            elif h2h["total"] >= 2: confidence += 7
            if home_form and away_form: confidence += 10
            if odd_1:               confidence += 10
            if has_fd:              confidence += 10   # bonus Football-Data
            if home_std and away_std: confidence += 5  # bonus classement réel

            w_impact, w_label = weather_impact(weather)
            has_lineup = bool(m.get("lineups", {}).get("home_team", {}).get("starting_lineups"))
            score = shadow_score(confidence, best_value, best_kelly, has_lineup, w_impact)

            if vbet:
                score = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')} ({vbet.get('bookmaker','?')})"
            elif value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
            else: verdict = "⚪ Pas de value"

            result = {
                "sport": "football", "league": league,
                "home": home, "away": away,
                "time": match_time, "event_id": match_id,
                "odds": {"1": odd_1, "X": odd_x, "2": odd_2,
                         "o25": odds.get("o25"), "u25": odds.get("u25"),
                         "btts_yes": odds.get("btts_yes")},
                "h2h": h2h,
                "form": {"home": home_form, "away": away_form,
                         "home_score": home_fs, "away_score": away_fs,
                         "home_trend": get_trend(home_form), "away_trend": get_trend(away_form)},
                "weather": weather, "weather_label": w_label, "value_bet_api": vbet,
                "fd_match": has_fd,
                "prediction": {
                    "home_prob": round(pred_home, 3), "draw_prob": round(pred_draw, 3),
                    "away_prob": round(pred_away, 3), "winner": winner,
                    "confidence": confidence, "goals_expected": goals_exp,
                    "over_under": "⬆️ OVER 2.5" if over_25 > 0.5 else "⬇️ UNDER 2.5",
                    "over_15": "⬆️ OVER 1.5" if over_15 > 0.5 else "⬇️ UNDER 1.5",
                    "over_35": "⬆️ OVER 3.5" if over_35 > 0.5 else "⬇️ UNDER 3.5",
                    "btts": f"⚽ BTTS {'OUI' if btts_prob > 0.5 else 'NON'} ({round(btts_prob*100)}%)",
                    "btts_prob": round(btts_prob, 3), "top5_scores": top5_scores,
                    "home_lam": home_lam, "away_lam": away_lam,
                },
                "value":  {"home": value_home, "away": value_away},
                "kelly":  {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            }

            # Ajout classement FD si dispo
            if home_std or away_std:
                result["standings"] = {"home": home_std, "away": away_std}

            results.append(result)
            fd_tag = "📊FD" if has_fd else ""
            print(f"  ✅ [{league}] {home} vs {away} — {score}/100 {fd_tag}")

        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")
    return results

# ============================================================
# ESPN — NHL
# ============================================================
def get_espn_nhl_games():
    """Matchs NHL du jour via ESPN."""
    try:
        r = requests.get(
            f"{ESPN_NHL_BASE}/scoreboard",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        ).json()
        games = []
        for e in r.get("events", []):
            if e.get("status", {}).get("type", {}).get("name") == "STATUS_FINAL":
                continue
            comp = e.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            home = next((t for t in teams if t["homeAway"] == "home"), {})
            away = next((t for t in teams if t["homeAway"] == "away"), {})
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
        print(f"  ❌ ESPN NHL games: {e}"); return []

def get_espn_nhl_standings():
    """Classement NHL via ESPN."""
    try:
        r = requests.get(
            f"{ESPN_NHL_WEB}/standings",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        ).json()
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
                    "gf":     float(stats.get("avgGoalsFor", 2.8) or 2.8),
                    "ga":     float(stats.get("avgGoalsAgainst", 2.8) or 2.8),
                }
        return standings
    except Exception as e:
        print(f"  ❌ ESPN NHL standings: {e}"); return {}

def get_espn_nhl_team_stats(team_id):
    """Stats offensives/défensives d'une équipe NHL via ESPN."""
    try:
        r = requests.get(
            f"{ESPN_NHL_BASE}/teams/{team_id}/statistics",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8
        ).json()
        stats = {}
        for cat in r.get("results", {}).get("stats", {}).get("categories", []):
            for s in cat.get("stats", []):
                stats[s["name"]] = s.get("value", 0)
        return stats
    except:
        return {}

# ============================================================
# ESPN — RUGBY
# ============================================================
def get_espn_rugby_games(league_slug):
    """Matchs du jour pour une ligue rugby via ESPN."""
    try:
        r = requests.get(
            f"{ESPN_RUG_BASE}/{league_slug}/scoreboard",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        ).json()
        games = []
        for e in r.get("events", []):
            if e.get("status", {}).get("type", {}).get("name") == "STATUS_FINAL":
                continue
            comp  = e.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            home  = next((t for t in teams if t["homeAway"] == "home"), {})
            away  = next((t for t in teams if t["homeAway"] == "away"), {})
            games.append({
                "game_id": e.get("id"),
                "home":    home.get("team", {}).get("displayName", "?"),
                "away":    away.get("team", {}).get("displayName", "?"),
                "home_id": home.get("team", {}).get("id"),
                "away_id": away.get("team", {}).get("id"),
                "time":    e.get("date", "")[:16].replace("T", " "),
            })
        return games
    except Exception as e:
        print(f"  ❌ ESPN Rugby {league_slug}: {e}"); return []

def get_espn_rugby_standings(league_slug):
    """Classement d'une ligue rugby via ESPN."""
    try:
        r = requests.get(
            f"{ESPN_RUG_WEB}/{league_slug}/standings",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        ).json()
        standings = {}
        for grp in r.get("children", [r]):
            for entry in grp.get("standings", {}).get("entries", []):
                team  = entry.get("team", {}).get("displayName", "?")
                stats = {s["name"]: s.get("displayValue") for s in entry.get("stats", [])}
                standings[team] = {
                    "wins":   stats.get("wins", "?"),
                    "losses": stats.get("losses", "?"),
                    "pct":    float(stats.get("winPercent", 0.5) or 0.5),
                    "pts":    stats.get("points", "?"),
                }
        return standings
    except Exception as e:
        print(f"  ❌ ESPN Rugby standings {league_slug}: {e}"); return {}

# ============================================================
# HOCKEY / RUGBY
# ============================================================
def analyze_team_sport(sport_name, sport_key, leagues):
    print(f"\n🏒🏉 Analyse {sport_name}...")
    get_value_bets(sport_name)
    matches = get_fixtures(sport_key, list(leagues.keys()))
    print(f"  ✅ {len(matches)} matchs AllSports")

    # ── Enrichissement ESPN ──────────────────────────────────
    if sport_key == "hockey":
        espn_games     = get_espn_nhl_games()
        espn_standings = get_espn_nhl_standings()
        print(f"  ✅ {len(espn_games)} matchs NHL ESPN")
    elif sport_key == "rugby":
        espn_games = []
        espn_standings = {}
        for lid, (slug, label) in ESPN_RUGBY_SLUGS.items():
            g = get_espn_rugby_games(slug)
            s = get_espn_rugby_standings(slug)
            for game in g:
                game["_league_label"] = label
            espn_games.extend(g)
            espn_standings.update(s)
        print(f"  ✅ {len(espn_games)} matchs Rugby ESPN")
    else:
        espn_games     = []
        espn_standings = {}

    # Index ESPN par paire home/away pour merge rapide
    espn_index = {
        (g["home"].lower(), g["away"].lower()): g
        for g in espn_games
    }

    results = []

    for m in matches:
        home     = m.get("event_home_team", "?")
        away     = m.get("event_away_team", "?")
        home_id  = m.get("home_team_key")
        away_id  = m.get("away_team_key")
        match_id = m.get("event_key")
        league   = leagues.get(str(m.get("_league_id", "")), m.get("league_name", "?"))
        match_time = m.get("event_time", "?")

        try:
            odds      = get_odds_allsports(match_id, sport_key)
            home_form = get_form_from_fixtures(home_id, sport_key)
            away_form = get_form_from_fixtures(away_id, sport_key)
            h2h       = get_h2h(home_id, away_id)
            vbet      = find_value_bet(home, away, sport_name)
            home_fs   = form_score(home_form)
            away_fs   = form_score(away_form)

            # ── Merge ESPN ───────────────────────────────────
            espn_match = espn_index.get((home.lower(), away.lower()), {})
            home_std   = espn_standings.get(home, {})
            away_std   = espn_standings.get(away, {})
            home_pct   = float(home_std.get("pct", 0.5) or 0.5)
            away_pct   = float(away_std.get("pct", 0.5) or 0.5)
            has_espn   = bool(espn_match)

            # Stats NHL spécifiques (buts/match)
            if sport_key == "hockey" and espn_match:
                home_espn_id = espn_match.get("home_id")
                away_espn_id = espn_match.get("away_id")
                home_nhl_stats = get_espn_nhl_team_stats(home_espn_id) if home_espn_id else {}
                away_nhl_stats = get_espn_nhl_team_stats(away_espn_id) if away_espn_id else {}
                home_gf = float(home_nhl_stats.get("avgGoalsFor",   home_std.get("gf", 2.8)) or 2.8)
                away_gf = float(away_nhl_stats.get("avgGoalsFor",   away_std.get("gf", 2.8)) or 2.8)
                home_ga = float(home_nhl_stats.get("avgGoalsAgainst", home_std.get("ga", 2.8)) or 2.8)
                away_ga = float(away_nhl_stats.get("avgGoalsAgainst", away_std.get("ga", 2.8)) or 2.8)
                # lambda estimé pour Over/Under NHL
                home_lam = round((home_gf + away_ga) / 2, 2)
                away_lam = round((away_gf + home_ga) / 2, 2)
                total_goals_exp = round(home_lam + away_lam, 2)
                ou_line = 5.5
                over_under_nhl = (
                    f"⬆️ OVER {ou_line} ({total_goals_exp}G)"
                    if total_goals_exp > ou_line
                    else f"⬇️ UNDER {ou_line} ({total_goals_exp}G)"
                )
            else:
                home_lam = home_gf = away_gf = None
                over_under_nhl = None
                home_nhl_stats = away_nhl_stats = {}

            # ── Prédiction H2H + forme + classement ESPN ────
            t = h2h.get("total", 0)
            if   t >= 8: wh, wf = 0.65, 0.35
            elif t >= 4: wh, wf = 0.50, 0.50
            elif t >= 1: wh, wf = 0.30, 0.70
            else:        wh, wf = 0.10, 0.90

            h2h_ph = h2h["home_wins"] / t if t else 0.34
            h2h_pa = h2h["away_wins"] / t if t else 0.33

            # Si classement ESPN dispo, on pondère
            if home_std and away_std:
                form_blend_h = home_fs * 0.5 + home_pct * 0.5
                form_blend_a = away_fs * 0.5 + away_pct * 0.5
            else:
                form_blend_h = home_fs
                form_blend_a = away_fs

            pred_home = h2h_ph * wh + form_blend_h * wf
            pred_away = h2h_pa * wh + form_blend_a * wf
            pred_draw = max(1 - pred_home - pred_away, 0)
            total_p   = pred_home + pred_draw + pred_away
            pred_home, pred_draw, pred_away = [round(p / total_p, 3) for p in [pred_home, pred_draw, pred_away]]

            if pred_home > pred_away and pred_home > pred_draw: winner = f"🏠 {home}"
            elif pred_away > pred_home and pred_away > pred_draw: winner = f"✈️ {away}"
            else: winner = "🤝 Match Nul"

            odd_1 = odds.get("1"); odd_x = odds.get("X"); odd_2 = odds.get("2")
            ip_home    = round(1/odd_1, 3) if odd_1 else None
            ip_away    = round(1/odd_2, 3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))

            confidence = round(
                min(t / 10 * 30, 30) +
                min((len(home_form) + len(away_form)) / 10 * 30, 30) +
                (20 if home_std and away_std else 0) +   # bonus classement ESPN
                (10 if has_espn else 0) +                # bonus match trouvé ESPN
                (10 if odd_1 else 0)
            )

            score = shadow_score(confidence, best_value, best_kelly)
            if vbet:
                score = min(score + 15, 100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')} ({vbet.get('bookmaker','?')})"
            elif value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
            else: verdict = "⚪ Pas de value"

            result = {
                "sport": sport_name, "league": league,
                "home": home, "away": away,
                "time": match_time, "event_id": match_id,
                "odds": {"1": odd_1, "X": odd_x, "2": odd_2},
                "h2h": h2h,
                "form": {
                    "home": home_form, "away": away_form,
                    "home_score": home_fs, "away_score": away_fs,
                    "home_trend": get_trend(home_form), "away_trend": get_trend(away_form),
                },
                "standings": {"home": home_std, "away": away_std},
                "espn_match": bool(espn_match),
                "value_bet_api": vbet,
                "prediction": {
                    "home_prob": pred_home, "draw_prob": pred_draw, "away_prob": pred_away,
                    "winner": winner, "confidence": confidence,
                },
                "value":  {"home": value_home, "away": value_away},
                "kelly":  {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            }

            # Ajout données NHL si dispo
            if sport_key == "hockey" and espn_match:
                result["nhl_stats"] = {
                    "home_gf": home_gf, "away_gf": away_gf,
                    "home_ga": home_ga, "away_ga": away_ga,
                    "total_goals_exp": total_goals_exp,
                    "over_under": over_under_nhl,
                }

            results.append(result)
            espn_tag = "🏒ESPN" if espn_match else ""
            print(f"  ✅ [{league}] {home} vs {away} — {score}/100 {espn_tag}")

        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    return results

# ============================================================
# TENNIS
# ============================================================
def elo_from_ranking(r):
    if r <= 1: return 2350
    if r <= 5: return 2250
    if r <= 10: return 2180
    if r <= 20: return 2120
    if r <= 50: return 2050
    if r <= 100: return 1980
    return 1900

def get_tennis_surface(name):
    name = (name or "").lower()
    if any(x in name for x in ["clay","terre","roland","montecarlo","madrid","rome"]): return "terre"
    if any(x in name for x in ["grass","gazon","wimbledon","queen","halle"]): return "gazon"
    if any(x in name for x in ["indoor","paris","rotterdam","vienna"]): return "indoor"
    return "dur"

def analyze_tennis():
    print(f"\n🎾 Analyse Tennis...")
    get_value_bets("tennis")
    today = date.today().strftime("%Y-%m-%d")
    matches_raw = allsports("tennis", {"met": "Fixtures", "from": today, "to": today})
    matches = [m for m in matches_raw if m.get("event_status") in ("", "notstarted", None)]
    print(f"  ✅ {len(matches)} matchs trouvés")
    results = []

    for m in matches:
        home = m.get("event_home_team", "?")
        away = m.get("event_away_team", "?")
        home_id = m.get("home_team_key")
        away_id = m.get("away_team_key")
        match_id = m.get("event_key")
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
            rank_a = max(1, int(200 * (1 - 1/cote_a)))
            rank_b = max(1, int(200 * (1 - 1/cote_b)))
            elo_a  = elo_from_ranking(rank_a)
            elo_b  = elo_from_ranking(rank_b)

            pred_home = round(1 / (1 + 10 ** (-(elo_a - elo_b) / 400)), 3)
            pred_away = round(1 - pred_home, 3)

            if home_form:
                wins = home_form.count("W")
                pred_home *= 1.05 if wins >= 3 else (0.95 if wins <= 1 else 1.0)
            if away_form:
                wins = away_form.count("W")
                pred_away *= 1.05 if wins >= 3 else (0.95 if wins <= 1 else 1.0)
            total = pred_home + pred_away
            pred_home = round(pred_home / total, 3)
            pred_away = round(1 - pred_home, 3)

            winner  = f"🎾 {home}" if pred_home > pred_away else f"🎾 {away}"
            surface = get_tennis_surface(tournament)
            edge_a  = pred_home - (1/cote_a)
            edge_b  = pred_away - (1/cote_b)

            confidence = 40
            if h2h_data["total"] >= 3: confidence += 20
            if home_form and away_form:  confidence += 20
            if odds.get("1"):            confidence += 20

            best_value = max(edge_a, edge_b, 0)
            best_kelly = max(kelly(pred_home, cote_a), kelly(pred_away, cote_b))
            score = shadow_score(confidence, best_value, best_kelly)

            if vbet:
                score = min(score+15,100)
                verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}"
            elif edge_a > 0.02: verdict = f"🎾 VALUE {home} (edge {round(edge_a,3)})"
            elif edge_b > 0.02: verdict = f"🎾 VALUE {away} (edge {round(edge_b,3)})"
            else: verdict = "⚪ Pas de value"

            results.append({
                "sport": "tennis", "league": tournament,
                "home": home, "away": away, "time": match_time, "event_id": match_id,
                "surface": surface,
                "odds": {"1": cote_a, "2": cote_b}, "h2h": h2h_data,
                "form": {"home": home_form, "away": away_form,
                         "home_score": form_score(home_form), "away_score": form_score(away_form),
                         "home_trend": get_trend(home_form), "away_trend": get_trend(away_form)},
                "value_bet_api": vbet,
                "prediction": {"home_prob": pred_home, "away_prob": pred_away,
                               "winner": winner, "confidence": confidence,
                               "surface": surface, "elo_home": elo_a, "elo_away": elo_b,
                               "edge_home": round(edge_a,3), "edge_away": round(edge_b,3)},
                "value": {"home": round(edge_a,3), "away": round(edge_b,3)},
                "kelly": {"home": kelly(pred_home, cote_a), "away": kelly(pred_away, cote_b)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            })
        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")
    return results

# ============================================================
# BASKETBALL
# ============================================================
def get_nba_games():
    try:
        r = requests.get(f"{ESPN_BASE}/scoreboard", headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        games = []
        for e in r.get("events", []):
            comp   = e.get("competitions", [{}])[0]
            teams  = comp.get("competitors", [])
            home   = next((t for t in teams if t["homeAway"] == "home"), {})
            away   = next((t for t in teams if t["homeAway"] == "away"), {})
            if e.get("status", {}).get("type", {}).get("name", "") == "STATUS_FINAL": continue
            games.append({
                "game_id": e.get("id"),
                "home": home.get("team", {}).get("displayName", "?"),
                "away": away.get("team", {}).get("displayName", "?"),
                "home_id": home.get("team", {}).get("id"),
                "away_id": away.get("team", {}).get("id"),
                "time": e.get("date", "")[:16].replace("T", " "),
            })
        return games
    except Exception as e:
        print(f"  ❌ ESPN: {e}"); return []

def get_nba_standings():
    try:
        r = requests.get(f"{ESPN_WEB}/standings", headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        standings = {}
        for conf in r.get("children", []):
            for entry in conf.get("standings", {}).get("entries", []):
                team  = entry.get("team", {}).get("displayName", "?")
                stats = {s["name"]: s.get("displayValue") for s in entry.get("stats", [])}
                standings[team] = {"wins": stats.get("wins","?"), "losses": stats.get("losses","?"),
                                   "pct": float(stats.get("winPercent", 0.5) or 0.5),
                                   "last10": stats.get("lastTen","?")}
        return standings
    except: return {}

def get_nba_team_stats(team_id):
    try:
        r    = requests.get(f"{ESPN_BASE}/teams/{team_id}/statistics", headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
        cats = r.get("results", {}).get("stats", {}).get("categories", [])
        stats = {}
        for cat in cats:
            for s in cat.get("stats", []):
                stats[s["name"]] = s.get("displayValue")
                stats[s["name"] + "_val"] = s.get("value", 0)
        return stats
    except: return {}

def get_bdl_form(team_name):
    if not BALLDONTLIE_KEY: return []
    search = NBA_TEAMS_MAP.get(team_name, team_name)
    try:
        r = requests.get(f"{BDL_BASE}/teams", headers=HEADERS_BDL,
                         params={"search": search}, timeout=10).json()
        if not r.get("data"): return []
        tid   = r["data"][0]["id"]
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
    except: return []

def analyze_basketball():
    print(f"\n🏀 Analyse Basketball...")
    get_value_bets("basketball")

    nba_results = []
    games     = get_nba_games()
    standings = get_nba_standings()
    print(f"  ✅ {len(games)} matchs NBA")

    for game in games:
        home = game["home"]; away = game["away"]
        home_id = game["home_id"]; away_id = game["away_id"]

        home_stats = get_nba_team_stats(home_id)
        away_stats = get_nba_team_stats(away_id)
        home_form  = get_bdl_form(home)
        away_form  = get_bdl_form(away)
        home_std   = standings.get(home, {})
        away_std   = standings.get(away, {})
        vbet       = find_value_bet(home, away, "basketball")

        def fs(f): return sum(1 for r in f if r == "W") / len(f) if f else 0.5
        home_fs  = fs(home_form); away_fs = fs(away_form)
        home_pct = float(home_std.get("pct", 0.5) or 0.5)
        away_pct = float(away_std.get("pct", 0.5) or 0.5)
        home_net = float(home_stats.get("netRating_val", 0) or 0)
        away_net = float(away_stats.get("netRating_val", 0) or 0)
        net_diff = (home_net - away_net) / 20

        pred_home = round(home_fs * 0.35 + home_pct * 0.45 + max(net_diff, 0) * 0.20, 3)
        pred_away = round(away_fs * 0.35 + away_pct * 0.45 + max(-net_diff, 0) * 0.20, 3)
        total_p   = pred_home + pred_away
        pred_home = round(pred_home / total_p, 3) if total_p else 0.5
        pred_away = round(1 - pred_home, 3)
        winner    = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

        try:
            home_ppg  = float(home_stats.get("avgPoints", 0) or 0)
            away_ppg  = float(away_stats.get("avgPoints", 0) or 0)
            total_pts = round(home_ppg + away_ppg, 1) or 224.5
            over_under = f"⬆️ OVER 224.5 ({total_pts}pts)" if total_pts > 224.5 else f"⬇️ UNDER 224.5 ({total_pts}pts)"
        except: total_pts = 0; over_under = "❓"

        confidence = 50
        if home_form and away_form: confidence += 15
        if home_std  and away_std:  confidence += 15
        if home_net  or away_net:   confidence += 10
        score = min(shadow_score(confidence, 0, 0) + (15 if vbet else 0), 100)
        verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}" if vbet else "⚪ Pas de value"

        nba_results.append({
            "sport": "basketball", "league": "NBA",
            "home": home, "away": away, "time": game["time"], "event_id": game["game_id"],
            "odds": {"1": round(1/pred_home,2) if pred_home else None, "2": round(1/pred_away,2) if pred_away else None},
            "standings": {"home": home_std, "away": away_std},
            "form": {"home": home_form, "away": away_form,
                     "home_trend": get_trend(home_form), "away_trend": get_trend(away_form)},
            "stats": {"home_ppg": str(home_stats.get("avgPoints","?")),
                      "away_ppg": str(away_stats.get("avgPoints","?")),
                      "total_pts_expected": str(total_pts)},
            "value_bet_api": vbet,
            "prediction": {"home_prob": pred_home, "away_prob": pred_away,
                           "winner": winner, "confidence": confidence,
                           "over_under": over_under, "total_pts": total_pts},
            "value": {}, "kelly": {},
            "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
        })

    # Autres ligues basket
    other_results = []
    nba_keys = {f"{r['home']}_{r['away']}" for r in nba_results}
    for m in get_fixtures("basketball", list(BASKETBALL_LEAGUES.keys())):
        home = m.get("event_home_team", "?"); away = m.get("event_away_team", "?")
        if f"{home}_{away}" in nba_keys: continue
        home_id = m.get("home_team_key"); away_id = m.get("away_team_key")
        match_id = m.get("event_key")
        league = BASKETBALL_LEAGUES.get(str(m.get("_league_id", "")), m.get("league_name", "Other"))
        match_time = m.get("event_time", "?")

        try:
            odds      = get_odds_allsports(match_id, "basketball")
            home_form = get_form_from_fixtures(home_id, "basketball")
            away_form = get_form_from_fixtures(away_id, "basketball")
            h2h_data  = get_h2h(home_id, away_id)
            vbet      = find_value_bet(home, away, "basketball")
            home_fs   = form_score(home_form); away_fs = form_score(away_form)
            t         = h2h_data.get("total", 0)

            pred_home = round((h2h_data["home_wins"]/t if t else 0.34)*0.4 + home_fs*0.6, 3)
            pred_away = round((h2h_data["away_wins"]/t if t else 0.33)*0.4 + away_fs*0.6, 3)
            total_p   = pred_home + pred_away
            pred_home = round(pred_home / total_p, 3) if total_p else 0.5
            pred_away = round(1 - pred_home, 3)
            winner    = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

            odd_1 = odds.get("1"); odd_2 = odds.get("2")
            ou_line = next((v for k, v in BASKET_OU.items() if k in league.lower()), 162.5)
            total_pts = round((home_fs + away_fs) * ou_line * 0.95, 1) or ou_line
            over_under = f"⬆️ OVER {ou_line} ({total_pts}pts)" if total_pts > ou_line else f"⬇️ UNDER {ou_line} ({total_pts}pts)"

            ip_home = round(1/odd_1,3) if odd_1 else None
            ip_away = round(1/odd_2,3) if odd_2 else None
            value_home = round(pred_home - ip_home, 3) if ip_home else None
            value_away = round(pred_away - ip_away, 3) if ip_away else None
            best_value = max(value_home or 0, value_away or 0)
            best_kelly = max(kelly(pred_home, odd_1), kelly(pred_away, odd_2))
            confidence = round(min(t/10*40,40) + min((len(home_form)+len(away_form))/10*40,40) + (20 if odd_1 else 0))
            score = shadow_score(confidence, best_value, best_kelly)

            if vbet: score = min(score+15,100); verdict = f"🎯 VALUE BET: {vbet.get('selection','?')} @ {vbet.get('odd','?')}"
            elif value_home and value_home > 0.05: verdict = f"🔥 VALUE HOME ({value_home})"
            elif value_away and value_away > 0.05: verdict = f"🔥 VALUE AWAY ({value_away})"
            else: verdict = "⚪ Pas de value"

            other_results.append({
                "sport": "basketball", "league": league,
                "home": home, "away": away, "time": match_time, "event_id": match_id,
                "odds": {"1": odd_1, "2": odd_2}, "h2h": h2h_data,
                "form": {"home": home_form, "away": away_form,
                         "home_score": home_fs, "away_score": away_fs,
                         "home_trend": get_trend(home_form), "away_trend": get_trend(away_form)},
                "value_bet_api": vbet,
                "prediction": {"home_prob": pred_home, "away_prob": pred_away,
                               "winner": winner, "confidence": confidence, "over_under": over_under},
                "value": {"home": value_home, "away": value_away},
                "kelly": {"home": kelly(pred_home, odd_1), "away": kelly(pred_away, odd_2)},
                "verdict": verdict, "shadow_score": score, "pick_label": pick_label(score),
            })
        except Exception as e:
            print(f"  ❌ {home} vs {away}: {e}")

    print(f"  ✅ {len(other_results)} autres matchs basket")
    return nba_results + other_results

# ============================================================
# RUN ANALYZE
# ============================================================
def run_analyze():
    if not _scrape_lock.acquire(blocking=False): return
    scrape_status["running"] = True
    scrape_status["error"]   = None
    _vbets_cache.clear()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}\n🚀 ANALYZE — {now}\n{'='*50}")
    try:
        jobs = [
            ("football",   analyze_football),
            ("basketball", analyze_basketball),
            ("tennis",     analyze_tennis),
            ("hockey",     lambda: analyze_team_sport("hockey", "hockey", HOCKEY_LEAGUES)),
            ("rugby",      lambda: analyze_team_sport("rugby", "rugby", RUGBY_LEAGUES)),
        ]
        for sport, fn in jobs:
            try:
                matches = fn()
                top10   = sorted([m for m in matches if m.get("verdict","") != "⚪ Pas de value"],
                                 key=lambda x: x.get("shadow_score", 0), reverse=True)[:10]
                store[sport] = {"date": str(date.today()), "matches": matches,
                                "top10": top10, "last_scrape": now}
                print(f"✅ {sport}: {len(matches)} matchs, {len(top10)} picks")
            except Exception as e:
                print(f"❌ {sport}: {e}")
                scrape_status["error"] = str(e)
        scrape_status["last_run"] = now
        print(f"✅ ANALYZE TERMINÉ — {now}\n")
    finally:
        scrape_status["running"] = False
        _scrape_lock.release()

def scheduler():
    time.sleep(10)
    run_analyze()
    while True:
        time.sleep(6 * 3600)
        run_analyze()

threading.Thread(target=scheduler, daemon=True).start()

if NBA_LIVE_OK:
    app.include_router(nba_live.router, prefix="/nba/live", tags=["NBA Live"])

# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/api")
def root():
    return {"status": "ok", "engine": "Shadow Edge V∞ 4.0",
            "apis": ["AllSports", "OddsAPI", "ESPN", "BallDontLie", "OpenWeather"],
            "scrape": scrape_status}

@app.get("/data/all/summary")
def summary():
    return {s: {"date": store[s]["date"], "count": len(store[s]["matches"]),
                "picks": len(store[s]["top10"]), "last_scrape": store[s]["last_scrape"],
                "top_pick": store[s]["top10"][0] if store[s]["top10"] else None}
            for s in store}

@app.get("/data/{sport}")
def get_data(sport: str):
    return store.get(sport, {"error": "Sport inconnu"})

@app.get("/data/{sport}/top10")
def get_top10(sport: str):
    return store.get(sport, {}).get("top10", [])

@app.post("/scrape")
def trigger(background_tasks: BackgroundTasks):
    if scrape_status["running"]:
        return {"status": "running", "message": "Analyse déjà en cours..."}
    background_tasks.add_task(run_analyze)
    return {"status": "started", "message": "Analyse lancée !"}

@app.get("/scrape/status")
def scrape_stat():
    return scrape_status

@app.post("/ingest/{sport}")
def ingest(sport: str, data: dict):
    if sport not in store: return {"error": "Sport inconnu"}
    matches = data.get("matches", [])
    top10   = sorted([m for m in matches if m.get("verdict","") != "⚪ Pas de value"],
                     key=lambda x: x.get("shadow_score",0), reverse=True)[:10]
    store[sport] = {"date": data.get("date", str(date.today())), "matches": matches,
                    "top10": top10, "last_scrape": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    return {"status": "ok", "sport": sport, "matches": len(matches)}

@app.on_event("startup")
async def mount_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.isdir(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
