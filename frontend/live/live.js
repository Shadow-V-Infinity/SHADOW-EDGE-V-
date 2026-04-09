// Mapping des logos NBA
const TEAM_LOGOS = {
    "Atlanta Hawks": 1610612737,
    "Boston Celtics": 1610612738,
    "Brooklyn Nets": 1610612751,
    "Charlotte Hornets": 1610612766,
    "Chicago Bulls": 1610612741,
    "Cleveland Cavaliers": 1610612739,
    "Dallas Mavericks": 1610612742,
    "Denver Nuggets": 1610612743,
    "Detroit Pistons": 1610612765,
    "Golden State Warriors": 1610612744,
    "Houston Rockets": 1610612745,
    "Indiana Pacers": 1610612754,
    "LA Clippers": 1610612746,
    "Los Angeles Lakers": 1610612747,
    "Memphis Grizzlies": 1610612763,
    "Miami Heat": 1610612748,
    "Milwaukee Bucks": 1610612749,
    "Minnesota Timberwolves": 1610612750,
    "New Orleans Pelicans": 1610612740,
    "New York Knicks": 1610612752,
    "Oklahoma City Thunder": 1610612760,
    "Orlando Magic": 1610612753,
    "Philadelphia 76ers": 1610612755,
    "Phoenix Suns": 1610612756,
    "Portland Trail Blazers": 1610612757,
    "Sacramento Kings": 1610612758,
    "San Antonio Spurs": 1610612759,
    "Toronto Raptors": 1610612761,
    "Utah Jazz": 1610612762,
    "Washington Wizards": 1610612764
};

// Endpoint LIVE
const API_URL = "https://shadow-edge-v-production.up.railway.app/nba/live/games";


// Chargement des matchs LIVE
async function loadLiveGames() {
    const container = document.getElementById("live-games");
    container.innerHTML = "<p>Chargement...</p>";

    try {
        const response = await fetch(API_URL);
        const games = await response.json();

        container.innerHTML = "";

        if (games.length === 0) {
            container.innerHTML = "<p>Aucun match en direct pour le moment.</p>";
            return;
        }

        games.forEach(game => {
            const card = document.createElement("div");
            card.className = "live-card";

            // Logos
            const homeLogo = TEAM_LOGOS[game.homeTeam];
            const awayLogo = TEAM_LOGOS[game.awayTeam];

            // Contenu de la carte
            card.innerHTML = `
                <div class="live-card-header">
                    <div class="team-block">
                        <img src="https://cdn.nba.com/logos/nba/${homeLogo}/global/L/logo.svg" class="team-logo">
                        <span>${game.homeTeam}</span>
                    </div>

                    <div class="vs">VS</div>

                    <div class="team-block">
                        <img src="https://cdn.nba.com/logos/nba/${awayLogo}/global/L/logo.svg" class="team-logo">
                        <span>${game.awayTeam}</span>
                    </div>
                </div>

                <p>Status : ${game.status}</p>
                <p>Score : ${game.homeScore} - ${game.awayScore}</p>
            `;

            // Effet pulse si match en cours
            if (game.status !== "Final") {
                card.classList.add("pulse");
            }

            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = "<p>Erreur lors du chargement des matchs.</p>";
        console.error(error);
    }
}

// Chargement initial
loadLiveGames();

// Bouton Refresh
document.getElementById("refresh-btn").addEventListener("click", () => {
    loadLiveGames();
});
