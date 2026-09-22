from src.table_tennis.scoring.game import Game
from table_tennis.rating.player import Player
def test_game():
    p1, p2 = Player("Big Willy", {"elo": 1000, "k_fac": 40, "games_played": 5}), Player("Small Willy", {"elo": 1200, "k_fac": 20, "games_played": 20})
    game = Game(player1=p1, player2=p2)
    assert game.playerA.name == "Big Willy"
    assert game.playerB.name == "Small Willy"
    assert game.score_a == 0 
    assert game.score_b == 0 
    assert game.is_finished is False
    assert game.winner is None
