from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import os
import math
import threading
import time
from datetime import date, datetime

app = FastAPI(title="Shadow Edge V∞", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CLÉS API
# ============================================================
BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
ODDS_API_KEY    = os.getenv("ODDS_API_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

# ============================================================
# STORE EN MÉMOIRE
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
# WHITELIST — Tournament IDs SofaScore
# ============================================================
WHITELIST = {
    "football": {
        17:  "Premier League",
        8:   "La Liga",
        35:  "Bundesliga",
        34:  "Ligue 1",
        23:  "Serie A",
        7:   "Champions League",
    },
    "basketball": {
        132: "NBA",
        551: "EuroLeague",
        552: "EuroCup",
        182: "Pro A",
    },
    "tennis": {
        2:   "ATP 250",
        3:   "ATP 500",
        6:   "ATP Masters 1000",
        22:  "Grand Chelem ATP",
        5:   "WTA 500",
        9:   "WTA 1000",
        10:  "Grand Chelem WTA",
    },
    "ice-hockey": {
        24:  "NHL",
        46:  "KHL",
    },
    "rugby": {
        180: "Top 14",
        181: "Premiership",
    },
}

SOFA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/",
}

# ============================================================
# UTILS
# ============================================================
def sofa(url, timeout=8):
    try:
        r = requests.get(url, headers=SOFA_HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  sofa erreur: {e}")
    return {}

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
    else:                      return "➡️ Stable"

def get_form(team_id):
    data = sofa(f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0")
    form = []
    for e in data.get("events", [])[:5]:
        hs  = e.get("homeScore", {}).get("current", 0) or 0
        aws = e.get("awayScore", {}).get("current", 0) or 0
        ht  = e.get("homeTeam", {}).get("id")
        if ht == team_id:
            form.append("W" if hs > aws else ("D" if hs == aws else "L"))
        else:
            form.append("W" if aws > hs else ("D" if hs == aws else "L"))
    return form

def get_h2h(event_id):
    data = sofa(f"https://api.sofascore.com/api/v1/event/{event_id}/h2h")
    d    = data.get("teamDuel", {})
    hw, aw, dr = d.get("homeWins",0), d.get("awayWins",0), d.get("draws",0)
    return {"home_wins": hw, "away_wins": aw, "draws": dr, "total": hw+aw+dr}

def get_odds(event_id):
    data    = sofa(f"https://api.sofascore.com/api/v1/event/{event_id}/odds/1/all")
    markets = data.get("markets", [])
    VALID   = ["Full time","Moneyline","1X2","Match Winner","Full Time Result","Home/Away","Winner","2Way"]
    for m in markets:
        if m.get("marketName") in VALID:
            res = {}
            for c in m.get("choices", []):
                name = c.get("name","")
                val  = c.get("decimalValue") or c.get("fractionalValue")
                try: val = float(val)
                except: val = None
                if name in ["1","Home","W1"]:   res["1"] = val
                elif name in ["2","Away","W2"]: res["2"] = val
                elif name in ["X","Draw"]:      res["X"] = val
            if res: return res
    return {}

def kelly_criterion(prob, odd):
    if not prob or not odd or odd <= 1: return 0
    b = odd - 1
    k = (b * prob - (1 - prob)) / b
    return round(max(k, 0) * 0.25, 4)

def predict(h2h, hfs, afs):
    t = h2h.get("total", 0)
    if   t >= 8: wh, wf = 0.65, 0.35
    elif t >= 4: wh, wf = 0.50, 0.50
    elif t >= 1: wh, wf = 0.30, 0.70
    else:        wh, wf = 0.10, 0.90
    ph = round((h2h["home_wins"]/t if t else 0.34)*wh + hfs*wf, 3)
    pa = round((h2h["away_wins"]/t if t else 0.33)*wh + afs*wf, 3)
    pd = round(max(1-ph-pa, 0), 3)
    return ph, pd, pa, wh, wf

def compute_score(conf, best_val, best_kelly, winner, ht, at):
    s  = conf * 0.30
    s += min((best_val or 0) * 100, 25)
    s += min(best_kelly * 100, 15)
    if "🏠" in winner:
        if "hausse" in ht: s += 20
        elif "Stable" in ht: s += 10
    elif "✈️" in winner:
        if "hausse" in at: s += 20
        elif "Stable" in at: s += 10
    return round(min(max(s, 0), 100))

def pick_label(score):
    if score >= 80: return "💎 PICK DIAMANT"
    elif score >= 65: return "🔥 PICK FORT"
    elif score >= 50: return "✅ PICK CORRECT"
    elif score >= 35: return "⚠️ PICK RISQUÉ"
    else: return "❌ ÉVITER"

# ============================================================
# BUILD MATCH — analyse complète d'un event SofaScore
# ============================================================
def build_match(event, whitelist, sport):
    home     = event.get("homeTeam", {}).get("name", "?")
    away     = event.get("awayTeam", {}).get("name", "?")
    event_id = event.get("id")
    home_id  = event.get("homeTeam", {}).get("id")
    away_id  = event.get("awayTeam", {}).get("id")
    t_id     = event.get("tournament", {}).get("uniqueTournament", {}).get("id")
    league   = whitelist.get(t_id, "?")

    odds      = get_odds(event_id)
    h2h       = get_h2h(event_id)
    hf        = get_form(home_id)
    af        = get_form(away_id)
    hfs, afs  = form_score(hf), form_score(af)
    ht, at    = get_trend(hf), get_trend(af)

    ph, pd, pa, wh, wf = predict(h2h, hfs, afs)

    o1, ox, o2 = odds.get("1"), odds.get("X"), odds.get("2")
    iph = round(1/o1, 3) if o1 else None
    ipa = round(1/o2, 3) if o2 else None
    vh  = round(ph - iph, 3) if iph else None
    va  = round(pa - ipa, 3) if ipa else None

    bv = max(vh or 0, va or 0)
    bk = max(kelly_criterion(ph, o1), kelly_criterion(pa, o2))

    if   ph > pa and ph > pd: winner = f"🏠 {home}"
    elif pa > ph and pa > pd: winner = f"✈️ {away}"
    else:                     winner = "🤝 Match Nul"

    conf = round(
        min(h2h["total"]/10*40, 40) +
        min((len(hf)+len(af))/10*40, 40) +
        (20 if o1 else 0)
    )

    goals = round((0.5+hfs*2.5)+(0.5+afs*2.5), 2)
    ou    = "⬆️ OVER 2.5" if goals > 2.5 else "⬇️ UNDER 2.5"
    score = compute_score(conf, bv, bk, winner, ht, at)
    label = pick_label(score)

    if   vh and vh > 0.05: verdict = f"🔥 VALUE HOME ({round(vh,3)})"
    elif va and va > 0.05: verdict = f"🔥 VALUE AWAY ({round(va,3)})"
    else:                  verdict = "⚪ Pas de value"

    return {
        "sport": sport, "league": league,
        "home": home, "away": away, "event_id": event_id,
        "odds": {"1": o1, "X": ox, "2": o2},
        "h2h": h2h,
        "value": {"home": vh, "away": va},
        "kelly": {"home": kelly_criterion(ph, o1), "away": kelly_criterion(pa, o2)},
        "form": {
            "home": hf, "away": af,
            "home_score": hfs, "away_score": afs,
            "home_trend": ht, "away_trend": at,
        },
        "prediction_v3": {
            "winner": winner, "home_prob": ph, "away_prob": pa, "draw_prob": pd,
            "confidence": conf,
            "conf_label": "🟢 Haute confiance" if conf >= 70 else "🟡 Confiance moyenne" if conf >= 40 else "🔴 Faible confiance",
            "goals_expected": goals, "over_under": ou,
            "home_trend": ht, "away_trend": at,
            "kelly": {"home": kelly_criterion(ph, o1), "away": kelly_criterion(pa, o2)},
        },
        "verdict": verdict, "shadow_score": score, "pick_label": label,
    }

# ============================================================
# SCRAPERS PAR SPORT
# ============================================================
def scrape_sport(sport_slug, sport_key, whitelist):
    today  = date.today().strftime("%Y-%m-%d")
    data   = sofa(f"https://api.sofascore.com/api/v1/sport/{sport_slug}/scheduled-events/{today}", timeout=15)
    events = data.get("events", [])
    print(f"{sport_key}: {len(events)} events bruts")

    results = []
    for event in events:
        t_id = event.get("tournament", {}).get("uniqueTournament", {}).get("id")
        if t_id not in whitelist:
            continue
        try:
            m = build_match(event, whitelist, sport_key)
            results.append(m)
            print(f"  ✅ [{m['league']}] {m['home']} vs {m['away']} — {m['shadow_score']}/100")
        except Exception as e:
            print(f"  ❌ {e}")
    return results

def scrape_basketball_full():
    results = scrape_sport("basketball", "basketball", WHITELIST["basketball"])

    # BallDontLie NBA en complément
    if BALLDONTLIE_KEY:
        try:
            today = date.today().strftime("%Y-%m-%d")
            r     = requests.get(
                "https://api.balldontlie.io/v1/games",
                headers={"Authorization": BALLDONTLIE_KEY},
                params={"dates[]": today},
                timeout=10
            )
            games    = r.json().get("data", [])
            existing = {f"{m['home']}_{m['away']}" for m in results}
            for g in games:
                home = g.get("home_team", {}).get("full_name", "?")
                away = g.get("visitor_team", {}).get("full_name", "?")
                if f"{home}_{away}" not in existing:
                    results.append({
                        "sport": "basketball", "league": "NBA",
                        "home": home, "away": away, "event_id": g.get("id"),
                        "odds": {}, "h2h": {}, "value": {}, "kelly": {},
                        "form": {"home":[],"away":[],"home_trend":"❓","away_trend":"❓"},
                        "prediction_v3": {
                            "winner":"❓","confidence":0,"conf_label":"❓",
                            "goals_expected":"?","over_under":"?",
                            "home_trend":"❓","away_trend":"❓",
                            "kelly":{"home":0,"away":0}
                        },
                        "verdict":"⚪ Pas de value","shadow_score":0,"pick_label":"❌ ÉVITER",
                    })
            print(f"  + BallDontLie: {len(games)} matchs NBA")
        except Exception as e:
            print(f"BallDontLie erreur: {e}")

    return results

# ============================================================
# SCRAPE GLOBAL
# ============================================================
def run_scrape():
    if scrape_status["running"]:
        return
    scrape_status["running"] = True
    scrape_status["error"]   = None
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}\n🚀 SCRAPE — {now}\n{'='*50}")

    jobs = [
        ("football",   lambda: scrape_sport("football",   "football",   WHITELIST["football"])),
        ("basketball", scrape_basketball_full),
        ("tennis",     lambda: scrape_sport("tennis",     "tennis",     WHITELIST["tennis"])),
        ("hockey",     lambda: scrape_sport("ice-hockey", "hockey",     WHITELIST["ice-hockey"])),
        ("rugby",      lambda: scrape_sport("rugby",      "rugby",      WHITELIST["rugby"])),
    ]

    for sport, fn in jobs:
        try:
            matches = fn()
            top10   = sorted(
                [m for m in matches if m.get("verdict","") != "⚪ Pas de value"],
                key=lambda x: x.get("shadow_score", 0), reverse=True
            )[:10]
            store[sport] = {
                "date": str(date.today()), "matches": matches,
                "top10": top10, "last_scrape": now,
            }
            print(f"✅ {sport}: {len(matches)} matchs, {len(top10)} picks")
        except Exception as e:
            print(f"❌ {sport}: {e}")
            scrape_status["error"] = str(e)

    scrape_status["running"]  = False
    scrape_status["last_run"] = now
    print(f"✅ SCRAPE TERMINÉ — {now}\n")

# ============================================================
# SCHEDULER — scrape au démarrage puis toutes les 6h
# ============================================================
def scheduler():
    time.sleep(5)
    run_scrape()
    while True:
        time.sleep(6 * 3600)
        run_scrape()

threading.Thread(target=scheduler, daemon=True).start()

# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/api")
def root():
    return {"status": "ok", "engine": "Shadow Edge V∞ 3.0", "scrape": scrape_status}

@app.get("/data/all/summary")
def summary():
    return {
        s: {
            "date": store[s]["date"],
            "count": len(store[s]["matches"]),
            "picks": len(store[s]["top10"]),
            "last_scrape": store[s]["last_scrape"],
            "top_pick": store[s]["top10"][0] if store[s]["top10"] else None,
        }
        for s in store
    }

@app.get("/data/{sport}")
def get_data(sport: str):
    return store.get(sport, {"error": "Sport inconnu"})

@app.get("/data/{sport}/top10")
def get_top10(sport: str):
    return store.get(sport, {}).get("top10", [])

@app.post("/scrape")
def trigger(background_tasks: BackgroundTasks):
    if scrape_status["running"]:
        return {"status": "running", "message": "Scrape déjà en cours..."}
    background_tasks.add_task(run_scrape)
    return {"status": "started", "message": "Scrape lancé !"}

@app.get("/scrape/status")
def scrape_stat():
    return scrape_status

# Ingest Termux — gardé pour compatibilité
@app.post("/ingest/{sport}")
def ingest(sport: str, data: dict):
    if sport not in store:
        return {"error": "Sport inconnu"}
    matches = data.get("matches", [])
    top10   = sorted(
        [m for m in matches if m.get("verdict","") != "⚪ Pas de value"],
        key=lambda x: x.get("shadow_score",0), reverse=True
    )[:10]
    store[sport] = {
        "date": data.get("date", str(date.today())),
        "matches": matches, "top10": top10,
        "last_scrape": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return {"status": "ok", "sport": sport, "matches": len(matches)}

# Frontend
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except Exception:
    pass
