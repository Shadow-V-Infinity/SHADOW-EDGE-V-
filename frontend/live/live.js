// Shadow Edge V∞ — LIVE HUD

// Mapping logos NBA (ID officiel cdn.nba.com)
const TEAM_LOGOS = {
    "Atlanta Hawks":        1610612737,
    "Boston Celtics":       1610612738,
    "Brooklyn Nets":        1610612751,
    "Charlotte Hornets":    1610612766,
    "Chicago Bulls":        1610612741,
    "Cleveland Cavaliers":  1610612739,
    "Dallas Mavericks":     1610612742,
    "Denver Nuggets":       1610612743,
    "Detroit Pistons":      1610612765,
    "Golden State Warriors":1610612744,
    "Houston Rockets":      1610612745,
    "Indiana Pacers":       1610612754,
    "LA Clippers":          1610612746,
    "Los Angeles Lakers":   1610612747,
    "Memphis Grizzlies":    1610612763,
    "Miami Heat":           1610612748,
    "Milwaukee Bucks":      1610612749,
    "Minnesota Timberwolves":1610612750,
    "New Orleans Pelicans": 1610612740,
    "New York Knicks":      1610612752,
    "Oklahoma City Thunder":1610612760,
    "Orlando Magic":        1610612753,
    "Philadelphia 76ers":   1610612755,
    "Phoenix Suns":         1610612756,
    "Portland Trail Blazers":1610612757,
    "Sacramento Kings":     1610612758,
    "San Antonio Spurs":    1610612759,
    "Toronto Raptors":      1610612761,
    "Utah Jazz":            1610612762,
    "Washington Wizards":   1610612764
};

// URL relative (fonctionne en local ET sur Railway)
const API_URL = "/nba/live/games";

async function loadLiveGames() {
    const container = document.getElementById("live-games");
    container.innerHTML = "<p style='color:#444;letter-spacing:3px;'>Chargement…</p>";

    try {
        const res   = await fetch("/nba/live/games");
        const games = await res.json();

        if (!games || games.length === 0) {
            container.innerHTML = "<p style='color:#333;letter-spacing:3px;margin-top:60px;'>Aucun match en cours.</p>";
            return;
        }

        container.innerHTML = games.map(g => `
            <div class="live-card pulse">

                <div class="live-card-header">
                    <div class="team-block">
                        <span style="color:#aaa;letter-spacing:2px;font-size:.85rem;">${g.home_team || "—"}</span>
                        <span class="score-home">${g.home_score ?? "—"}</span>
                    </div>

                    <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
                        <span class="vs">VS</span>
                        <span style="color:#444;font-size:.75rem;letter-spacing:2px;">${g.status || "LIVE"}</span>
                        <span style="color:#333;font-size:.7rem;">P${g.period ?? "?"} — ${g.clock || ""}</span>
                    </div>

                    <div class="team-block">
                        <span style="color:#aaa;letter-spacing:2px;font-size:.85rem;">${g.away_team || "—"}</span>
                        <span class="score-away">${g.away_score ?? "—"}</span>
                    </div>
                </div>

                <div class="big-score" style="justify-content:center;gap:20px;margin-top:8px;">
                    <span style="color:#444;font-size:.75rem;letter-spacing:2px;">LEADER DOM. →</span>
                    <span style="color:#ccc;font-size:.85rem;">${renderLeader(g.leaders?.home)}</span>
                    <span style="color:#222;">|</span>
                    <span style="color:#ccc;font-size:.85rem;">${renderLeader(g.leaders?.away)}</span>
                    <span style="color:#444;font-size:.75rem;letter-spacing:2px;">← LEADER EXT.</span>
                </div>

            </div>
        `).join("");

    } catch (e) {
        container.innerHTML = "<p style='color:#333;letter-spacing:3px;'>Erreur de connexion API.</p>";
        console.error("[Shadow Edge] live.js error:", e);
    }
}

function renderLeader(leaders) {
    if (!leaders || !leaders.points) return "—";
    const pts = leaders.points;
    return `<strong style="color:#fff;">${pts.personName || "—"}</strong>
            <span style="color:#b300ff;font-weight:bold;"> ${pts.value ?? ""} PTS</span>`;
}

// Lancement + auto-refresh 30s
loadLiveGames();
setInterval(loadLiveGames, 30000);

document.getElementById("refresh-btn")?.addEventListener("click", loadLiveGames);
