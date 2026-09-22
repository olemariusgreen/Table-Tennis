from .player import Player
from .json_helpers import who_is_json
from numpy import floor
import json

class Elo:
    def __init__(self, player1_name, player2_name):
        player1 = Player(player1_name, who_is_json(player1_name))
        player2 = Player(player2_name, who_is_json(player2_name))
        self.player_A = player1
        self.player_B = player2

    def get_player(self, name):
        return self.players[name]

    def calculate_change(self, winner) -> int:
        if winner == self.player_A.name:
            S_A = 1
            S_B = 0 
        elif winner == self.player_B.name:
            S_A = 0
            S_B = 1
        else: 
            raise ValueError("Game is not finished yet")

        eloA = self.player_A.elo
        eloB = self.player_B.elo 
        EXP_A = 1/(1 + 10**((eloB-eloA)/400))
        EXP_B = 1/(1 + 10**((eloA-eloB)/400))
        new_eloA = floor(eloA + self.player_A.k_fac*(S_A-EXP_A))
        new_eloB = floor(eloB + (self.player_B.k_fac*(S_B-EXP_B)))
        self.player_A.elo = new_eloA
        self.player_B.elo = new_eloB
        self.player_A.update_games()
        self.player_B.update_games()
        self.player_A.update_k()
        self.player_A.update_k()
        
        print(f"{self.player_A.name} new elo: {new_eloA}")
        print(f"{self.player_B.name} new elo: {new_eloB}")

        self.player_A.write_to_player_json()
        self.player_B.write_to_player_json()

