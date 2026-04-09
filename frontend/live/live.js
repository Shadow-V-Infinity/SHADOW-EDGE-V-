const API_URL = "https://shadow-edge-v-production.up.railway.app/nba/live/games";

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

            card.innerHTML = `
                <h2>${game.homeTeam} vs ${game.awayTeam}</h2>
                <p>Status : ${game.status}</p>
                <p>Score : ${game.homeScore} - ${game.awayScore}</p>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = "<p>Erreur lors du chargement des matchs.</p>";
        console.error(error);
    }
}

loadLiveGames();
