import json

class Player:
    def __init__(self, name="Ole Marius Green", player_dict=None):
        """
        Args:
            name: name in string format
            player_dict: dict with format {"elo": _ , "k_fac": _ , "games_played": _ }
        """
        if player_dict is None:
            player_dict = {"elo": 1000, "k_fac": 40, "games_played": 0}
        self.name = name
        self.elo = player_dict["elo"]
        self.k_fac = player_dict["k_fac"]
        self.games_played = player_dict["games_played"]
        self.write_to_player_json()

    def update_games(self):
        self.games_played += 1

    def update_k(self):
        if self.games_played < 10:
            self.k_fac = 40
        elif 10 <= self.games_played < 20:
            self.k_fac = 20
        else:
            self.k_fac = 10

    def to_dict(self):
        return {"elo": self.elo, "k_fac": self.k_fac, "games_played": self.games_played}

    def write_to_player_json(self):
        """Assumes player is already in players.json"""
        with open("data/players.json") as read_file:
            data = json.load(read_file)
        players = data.setdefault("players", {})
        player_data = self.to_dict()
        players[self.name] = player_data
        with open("data/players.json", "w") as write_file:
            json.dump(data, write_file, indent=2, ensure_ascii=False)
