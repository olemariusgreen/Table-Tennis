from .player import Player
import json
from datetime import datetime

def write_to_elo_ranking_json():
    with open("data/players.json") as f:
        players = json.load(f)["players"]

    sorted_players = sorted(players.items(), key=lambda x: x[1]["elo"], reverse=True)

    rankings = [
        {"rank": rank, "name": name, "elo": data["elo"]}
        for rank, (name, data) in enumerate(sorted_players, start=1)
    ]

    with open("data/elo_ranking.json", "w") as f:
        json.dump(rankings, f, indent=2, ensure_ascii=False)
            

def write_to_games(game):
    with open("data/games.json") as read_file:
        data = json.load(read_file)
    games = data.setdefault("games", {})

    game_name = f"{game.player_A}_v_{game.player_B}_{datetime.now():%Y-%m-%d_%H-%M}"
    game_data = {"winner": game.winner, "score_a": game.score_a, "score_b": game.score_b}

    games[game_name] = game_data
    with open("data/games.json", "w") as write_file:
        json.dump(data, write_file, indent=2, ensure_ascii=False)

def who_is_json(player_name: str) -> dict:
    with open("data/players.json") as read_file:
        data = json.load(read_file)
    players = data.setdefault("players", {})
    if player_name not in players:
        new_player = Player(name=player_name)
        players[player_name] = {"elo": new_player.elo, "k_fac": new_player.k_fac, "games_played": new_player.games_played}
        with open("data/players.json", "w") as write_file:
            json.dump(data, write_file, indent=2, ensure_ascii=False)
    return players[player_name]
