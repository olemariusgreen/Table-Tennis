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
        playerA = game.player_A
        playerB = game.player_B
        if game.winner == playerA:
            S_A = 1
            S_B = 0 
        elif game.winner == playerB:
            S_A = 0
            S_B = 1
        else: 
            raise ValueError("Game is not finished yet")

        eloA = playerA.elo
        eloB = playerB.elo 
        EXP_A = 1/(1 + 10**((eloB-eloA)/400))
        EXP_B = 1/(1 + 10**((eloA-eloB)/400))
        new_eloA = eloA + playerA.k_fac*(S_A-EXP_A)
        new_eloB = eloB + playerB.k_fac*(S_B-EXP_B)
        playerA.elo = new_eloA
        playerB.elo = new_eloB
        playerA.games_played += 1
        playerB.games_played += 1
       

