class Game:
    def __init__(self, player1_name: str, player2_name: str):
        
        self.player_A = player1_name
        self.player_B = player2_name
        self.score_a = 0
        self.score_b = 0

    def point_to_a(self) -> None:
        if not self.is_finished:
            self.score_a += 1
        else: 
            self.score_a += 0

    def point_to_b(self) -> None:
        if not self.is_finished:
            self.score_b += 1
        else: 
            self.score_b += 0

    @property
    def is_finished(self) -> bool:
        if self.score_a < 11 and self.score_b < 11:
            return False

        return abs(self.score_a - self.score_b) >= 2

    @property
    def winner(self) -> str:
        if self.is_finished:
            if self.score_a > self.score_b:
                return self.player_A
            return self.player_B
        return None

