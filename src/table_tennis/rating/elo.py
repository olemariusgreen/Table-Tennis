from .player import Player 


class Elo:
    def __init__(self):
        self.players = {}

    def register_player(self, name, elo=1000, k_fac = 40, games_played = 0):
        player = Player(name, elo, k_fac, games_played)
        self.players[name] = player

    def get_player(self, name):
        return self.players[name]

    def calculate_change(self, game):
        player_a = game.player_a
        player_b = game.player_a
        if game.winner == player_a:
            S_A = 1
            S_B = 0 
        elif game.winner == player_b:
            S_A = 0
            S_B = 1
        else: 
            raise ValueError("Game is not finished yet")

        eloA = player_a.elo
        eloB = player_b.elo 
        EXP_A = 1/(1 + 10**((eloB-eloA)/400))
        EXP_B = 1/(1 + 10**((eloA-eloB)/400))
        new_eloA = eloA + player_a.k_fac*(S_A-EXP_A)
        new_eloB = eloB + player_b.k_fac*(S_B-EXP_B)
        player_a.elo = new_eloA
        player_b.elo = new_eloB
        player_a.games_played += 1
        player_b.games_played += 1
       

