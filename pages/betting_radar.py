def analyze_match(self, home_team, away_team, model_home_prob):
    market = self.get_game_market(home_team, away_team)
    if not market:
        return {"market": None}

    home_odds = market["home_odds"]
    away_odds = market["away_odds"]

    # Probabilités implicites
    home_ip = self.implied_prob(home_odds)
    away_ip = self.implied_prob(away_odds)

    # Value bet
    value = self.value_bet(model_home_prob, home_odds)
    kelly = self.kelly_fraction(model_home_prob, home_odds)
    arb = self.arbitrage(home_odds, away_odds)

    # -----------------------------
    # SIGNES MARCHÉ (Shadow Edge V∞)
    # -----------------------------

    # 1) Steam Move (simulation d'une opening line)
    opening_home_odds = home_odds + (0.10 if home_odds > 1 else 0)
    steam_move = opening_home_odds - home_odds

    # 2) Reverse Line Movement (RLM)
    # Si la probabilité implicite baisse alors que la value augmente → RLM
    rlm = None
    if value is not None and home_ip is not None:
        rlm = value > 0 and home_ip < 0.50

    # 3) Market Pressure Index (MPI)
    mpi = round(abs(steam_move) * 10, 2)

    # 4) Line Movement Score
    lm_score = round((steam_move * -1) * 100, 2)

    # 5) Value Radar
    if value is None:
        value_radar = "No Data"
    elif value > 0.10:
        value_radar = "🔥 Strong Value"
    elif value > 0.03:
        value_radar = "🟢 Weak Value"
    else:
        value_radar = "⚪ No Value"

    return {
        "market": market,
        "implied_probability": {
            "home": home_ip,
            "away": away_ip,
        },
        "value": {
            "home_value": value,
            "value_radar": value_radar,
        },
        "kelly": {
            "home_fraction": kelly,
        },
        "arbitrage": arb,
        "signals": {
            "steam_move": steam_move,
            "reverse_line_movement": rlm,
            "market_pressure_index": mpi,
            "line_movement_score": lm_score,
        }
    }
