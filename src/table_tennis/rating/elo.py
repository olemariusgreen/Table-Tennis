from .player import Player 

class Elo:
    def __init__(self):
        self.players = {}

    def register_player(self, name, elo=1000):
        player = Player(name, elo)
        self.players[name] = player

    def get_player(self, name):
        return self.players[name]