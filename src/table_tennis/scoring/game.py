class Game:
    def __init__(self, player1_name: str, player2_name: str, score_a: int = 0, score_b: int = 0):
        """A single game to 11. Pass score_a/score_b to build one from a final score."""
        self.player_A = player1_name
        self.player_B = player2_name
        self.score_a = score_a
        self.score_b = score_b

    def point_to_a(self) -> None:
        if not self.is_finished:
            self.score_a += 1

    def point_to_b(self) -> None:
        if not self.is_finished:
            self.score_b += 1

    @property
    def is_finished(self) -> bool:
        """True for a legally completed game. Rejects impossible scores like 12-9."""
        hi, lo = max(self.score_a, self.score_b), min(self.score_a, self.score_b)
        return (hi == 11 and lo <= 9) or (hi > 11 and hi - lo == 2)

    @property
    def winner(self) -> str | None:
        if self.is_finished:
            if self.score_a > self.score_b:
                return self.player_A
            return self.player_B
        return None
