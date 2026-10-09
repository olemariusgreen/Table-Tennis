from .game import Game

class Match:
    """A match is a sequence of games. Elo is rated per match, never per game."""

    def __init__(self, player1_name: str, player2_name: str, scores, table: str):
        """scores: [(11, 9), (8, 11), ...] - the final point score of each game."""
        self.player_A = player1_name
        self.player_B = player2_name
        self.table = table
        self.games = [Game(player1_name, player2_name, a, b) for a, b in scores]

    @property
    def games_won_a(self) -> int:
        return sum(g.winner == self.player_A for g in self.games)

    @property
    def games_won_b(self) -> int:
        return sum(g.winner == self.player_B for g in self.games)

    @property
    def winner(self) -> str | None:
        if self.games_won_a > self.games_won_b:
            return self.player_A
        if self.games_won_b > self.games_won_a:
            return self.player_B
        return None

    @property
    def is_valid(self) -> bool:
        return bool(self.games) and all(g.is_finished for g in self.games) and self.winner is not None
