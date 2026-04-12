"""
Shadow Edge V∞ — NBA Scraper
Module NBA séparé utilisant ESPN API + BallDontLie

Usage:
    python nba_scraper.py          → analyse NBA complète
    python nba_scraper.py live     → matchs en cours seulement
"""

import cloudscraper
import requests
import os
import sys
import time
from datetime import date, datetime

# ── CONFIG ──────────────────────────────────────────────
RENDER_URL      = os.getenv("RENDER_URL", "https://shadow-edge-v.onrender.com")
BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
HEADERS_BDL     = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

scraper = cloudscraper.create_scraper()
headers = {"User-Agent": "Mozilla/5.0"}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_WEB  = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba"
BDL_BASE  = "https://api.balldontlie.io/v1"

today = date.today().strftime("%Y-%m-%d")
now   = datetime.now()

# ── MAPPING ESPN → BallDontLie ──────────────────────────
NBA_TEAMS = {
    "Boston Celtics":        "Celtics",
    "Cleveland Cavaliers":   "Cavaliers",
    "Indiana Pacers":        "Pacers",
    "Miami Heat":            "Heat",
    "New York Knicks":       "Knicks",
    "Philadelphia 76ers":    "76ers",
    "Toronto Raptors":       "Raptors",
    "Brooklyn Nets":         "Nets",
    "Charlotte Hornets":     "Hornets",
    "Atlanta Hawks":         "Hawks",
    "Chicago Bulls":         "Bulls",
    "Dallas Mavericks":      "Mavericks",
    "Houston Rockets":       "Rockets",
    "Memphis Grizzlies":     "Grizzlies",
    "Minnesota Timberwolves":"Timberwolves",
    "Oklahoma City Thunder": "Thunder",
    "Phoenix Suns":          "Suns",
    "San Antonio Spurs":     "Spurs",
    "Denver Nuggets":        "Nuggets",
    "Los Angeles Lakers":    "Lakers",
    "LA Clippers":           "Clippers",
    "Golden State Warriors": "Warriors",
    "Portland Trail Blazers":"Trail Blazers",
    "Sacramento Kings":      "Kings",
    "Utah Jazz":             "Jazz",
    "New Orleans Pelicans":  "Pelicans",
    "Washington Wizards":    "Wizards",
    "Orlando Magic":         "Magic",
    "Milwaukee Bucks":       "Bucks",
    "Detroit Pistons":       "Pistons",
}

# ════════════════════════════════════════════════════════
# ESPN API
# ════════════════════════════════════════════════════════

def get_nba_games():
    try:
        r      = scraper.get(f"{ESPN_BASE}/scoreboard", headers=headers).json()
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
                "status_detail": status.get("description", ""),
                "time":       e.get("date", "")[:16].replace("T", " "),
            })
        return games
    except Exception as e:
        print(f"❌ get_nba_games: {e}")
        return []

def get_standings():
    try:
        r = scraper.get(f"{ESPN_WEB}/standings", headers=headers).json()
        standings = {}
        for conf in r.get("children", []):
            conf_name = conf.get("name", "")
            for entry in conf.get("standings", {}).get("entries", []):
                team  = entry.get("team", {}).get("displayName", "?")
                stats = {s["name"]: s.get("displayValue") for s in entry.get("stats", [])}
                standings[team] = {
                    "conference": conf_name,
                    "wins":       stats.get("wins", "?"),
                    "losses":     stats.get("losses", "?"),
                    "pct":        stats.get("winPercent", "0.5"),
                    "streak":     stats.get("streak", "?"),
                    "home":       stats.get("home", "?"),
                    "away":       stats.get("road", "?"),
                    "last10":     stats.get("lastTen", "?"),
                }
        return standings
    except Exception as e:
        print(f"❌ get_standings: {e}")
        return {}

def get_injuries():
    try:
        r        = scraper.get(f"{ESPN_BASE}/injuries", headers=headers).json()
        injuries = {}
        for item in r.get("injuries", []):
            team    = item.get("team", {}).get("displayName", "?")
            players = []
            for inj in item.get("injuries", []):
                players.append({
                    "name":   inj.get("athlete", {}).get("displayName", "?"),
                    "status": inj.get("status", "?"),
                    "detail": inj.get("details", {}).get("detail", "?"),
                })
            injuries[team] = players
        return injuries
    except Exception as e:
        print(f"❌ get_injuries: {e}")
        return {}

def get_team_stats(team_id):
    try:
        r    = scraper.get(f"{ESPN_BASE}/teams/{team_id}/statistics", headers=headers).json()
        cats = r.get("results", {}).get("stats", {}).get("categories", [])
        stats = {}
        for cat in cats:
            for s in cat.get("stats", []):
                stats[s["name"]] = s.get("displayValue", "?")
        return stats
    except:
        return {}

# ════════════════════════════════════════════════════════
# BALLDONTLIE — Forme récente
# ════════════════════════════════════════════════════════

def get_bdl_form(team_name):
    if not BALLDONTLIE_KEY:
        return []
    search = NBA_TEAMS.get(team_name, team_name)
    try:
        r = scraper.get(
            f"{BDL_BASE}/teams",
            headers=HEADERS_BDL,
            params={"search": search}
        ).json()
        if not r.get("data"):
            return []
        team_id = r["data"][0]["id"]

        games = scraper.get(
            f"{BDL_BASE}/games",
            headers=HEADERS_BDL,
            params={"team_ids[]": team_id, "per_page": 5, "seasons[]": 2025}
        ).json()

        form = []
        for g in games.get("data", []):
            hs  = g.get("home_team_score", 0)
            aws = g.get("visitor_team_score", 0)
            ht  = g.get("home_team", {}).get("id")
            if ht == team_id:
                form.append("W" if hs > aws else "L")
            else:
                form.append("W" if aws > hs else "L")
        return form
    except:
        return []

# ════════════════════════════════════════════════════════
# PRÉDICTION NBA
# ════════════════════════════════════════════════════════

def predict_nba(home_form, away_form, home_std, away_std):
    def fs(f):
        if not f: return 0.5
        return sum(1 if r == "W" else 0 for r in f) / len(f)

    home_fs = fs(home_form)
    away_fs = fs(away_form)

    try:
        home_pct = float(home_std.get("pct", 0.5) or 0.5)
        away_pct = float(away_std.get("pct", 0.5) or 0.5)
    except:
        home_pct = away_pct = 0.5

    pred_home = round((home_fs * 0.5) + (home_pct * 0.5), 3)
    pred_away = round((away_fs * 0.5) + (away_pct * 0.5), 3)
    total = pred_home + pred_away
    pred_home = round(pred_home / total, 3) if total else 0.5
    pred_away = round(1 - pred_home, 3)
    return pred_home, pred_away

# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"🏀 Shadow Edge V∞ — NBA — {today} {now.strftime('%H:%M')}")
    print(f"📡 Render: {RENDER_URL}")
    print("=" * 50)

    # Réveiller Render
    try:
        requests.get(f"{RENDER_URL}/api", timeout=10)
        print("☀️  Render réveillé")
        time.sleep(2)
    except:
        pass

    games     = get_nba_games()
    standings = get_standings()
    injuries  = get_injuries()

    print(f"✅ {len(games)} matchs NBA")
    print(f"✅ {len(standings)} équipes standings")
    print(f"✅ {len(injuries)} équipes blessées")

    # FIX : exclure toujours les matchs terminés (STATUS_FINAL)
    # En mode "all" on garde scheduled + live, pas les finished
    if mode == "live":
        games = [g for g in games if g["status"] not in ["STATUS_FINAL", "STATUS_SCHEDULED"]]
        print(f"⚡ {len(games)} matchs en cours")
    else:
        games = [g for g in games if g["status"] != "STATUS_FINAL"]
        print(f"📋 {len(games)} matchs (terminés exclus)")

    results = []

    for game in games:
        home    = game["home"]
        away    = game["away"]
        home_id = game["home_id"]
        away_id = game["away_id"]

        # Stats ESPN
        home_stats = get_team_stats(home_id)
        away_stats = get_team_stats(away_id)

        # Forme BallDontLie
        home_form = get_bdl_form(home)
        away_form = get_bdl_form(away)

        # Standings
        home_std = standings.get(home, {})
        away_std = standings.get(away, {})

        # Injuries
        home_inj = injuries.get(home, [])
        away_inj = injuries.get(away, [])

        # Prédiction
        pred_home, pred_away = predict_nba(home_form, away_form, home_std, away_std)
        winner = f"🏀 {home}" if pred_home > pred_away else f"🏀 {away}"

        # Over/Under
        home_ppg = home_stats.get("avgPoints", "0")
        away_ppg = away_stats.get("avgPoints", "0")
        try:
            total_pts  = float(home_ppg) + float(away_ppg)
            over_under = "⬆️ OVER 220" if total_pts > 220 else "⬇️ UNDER 220"
            total_str  = str(round(total_pts, 1))
        except:
            over_under = "❓"
            total_str  = "?"

        # Score confiance
        confidence = 60
        if home_form and away_form: confidence += 20
        if home_std and away_std:   confidence += 20
        shadow_score = min(confidence, 100)

        result = {
            "sport":      "basketball",
            "home":       home,
            "away":       away,
            "game_id":    game["game_id"],
            "time":       game["time"],
            "status":     game["status"],
            "home_score": game["home_score"],
            "away_score": game["away_score"],
            "standings": {"home": home_std, "away": away_std},
            "form":      {"home": home_form, "away": away_form},
            "injuries":  {"home": home_inj, "away": away_inj},
            "stats": {
                "home_ppg":           home_ppg,
                "away_ppg":           away_ppg,
                "total_pts_expected": total_str,
            },
            "prediction": {
                "home_prob":  pred_home,
                "away_prob":  pred_away,
                "winner":     winner,
                "over_under": over_under,
                "confidence": confidence,
            },
            "verdict":      "⚪ Pas de value",
            "shadow_score": shadow_score,
        }
        results.append(result)

        print(f"\n🏀 {home} vs {away} [{game['time']}]")
        print(f"   → {winner}")
        print(f"   {home_std.get('wins','?')}W-{home_std.get('losses','?')}L vs {away_std.get('wins','?')}W-{away_std.get('losses','?')}L")
        print(f"   Forme: {''.join(home_form) or '?'} vs {''.join(away_form) or '?'}")
        print(f"   PPG: {home_ppg} vs {away_ppg} → {over_under}")
        if home_inj:
            print(f"   🚑 DOM: {', '.join([p['name'] for p in home_inj[:2]])}")
        if away_inj:
            print(f"   🚑 EXT: {', '.join([p['name'] for p in away_inj[:2]])}")

    # TOP 5
    print("\n" + "=" * 50)
    print("🏆 TOP 5 NBA")
    print("=" * 50)
    top5 = sorted(results, key=lambda x: x["shadow_score"], reverse=True)[:5]
    for i, r in enumerate(top5, 1):
        pred = r["prediction"]
        print(f"#{i} 🏀 ({r['shadow_score']}/100) [{r['time']}]")
        print(f"   {r['home']} vs {r['away']}")
        print(f"   → {pred['winner']} | {pred['over_under']}")

    # Envoi Render
    print(f"\n📡 Envoi vers Render...")
    try:
        resp = requests.post(
            f"{RENDER_URL}/ingest/basketball",
            json={"date": today, "matches": results},
            timeout=20
        )
        print(f"✅ /ingest/basketball → {resp.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

    print(f"\n✅ {len(results)} matchs NBA analysés !")
