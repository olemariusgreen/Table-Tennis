
class Player:
    def __init__(self, name, elo=1000, k_fac=40, games_played=0):
        self.name = name
        self.elo = elo
        self.k_fac = k_fac
        self.games_played = games_played

    def update_games(self):
        self.games_played += 1

    def update_k(self):
        if self.games_played < 10:
            self.k_fac = 40
        elif 10 <= self.games_played < 20:
            self.k_fac = 20
        else:
            self.k_fac = 10

        
    
