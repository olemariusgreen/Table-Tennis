class Game:
    def __init__(self, player_a, player_b):
        self.player_a = player_a
        self.player_b = player_b
        self.score_a = 0
        self.score_b = 0

    def point_to_a(self):
        if not self.is_finished:
            self.score_a += 1
        else: 
            self.score_a += 0

    def point_to_b(self):
        if not self.is_finished:
            self.score_b += 1
        else: 
            self.score_b += 0

    @property
    def is_finished(self):
        if self.score_a < 11 and self.score_b < 11:
            return False

        return abs(self.score_a - self.score_b) >= 2

    @property
    def winner(self):
        if not self.is_finished:
            return None

        if self.score_a > self.score_b:
            return self.player_a

        return self.player_b