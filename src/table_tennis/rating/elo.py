from .player import Player 


class Elo:
    def __init__(self):
        self.players = {}

    def register_player(self, player_list: list):
        for player in player_list:
            name = player.name
            self.players[name] = player

    def get_player(self, name):
        return self.players[name]

    def calculate_change(self, game) -> int:
        if game.winner == game.player_A.name:
            S_A = 1
            S_B = 0 
        elif game.winner == game.player_B.name:
            S_A = 0
            S_B = 1
        else: 
            raise ValueError("Game is not finished yet")

        eloA = game.player_A.elo
        eloB = game.player_B.elo 
        EXP_A = 1/(1 + 10**((eloB-eloA)/400))
        EXP_B = 1/(1 + 10**((eloA-eloB)/400))
        new_eloA = eloA + game.player_A.k_fac*(S_A-EXP_A)
        new_eloB = eloB + game.player_B.k_fac*(S_B-EXP_B)
        game.player_A.elo = new_eloA
        game.player_B.elo = new_eloB
        game.player_A.games_played += 1
        game.player_B.games_played += 1

        print(f"{game.player_A.name} new elo: {new_eloA}")
        print(f"{game.player_B.name} new elo: {new_eloB}")

        return new_eloA, new_eloB
       

