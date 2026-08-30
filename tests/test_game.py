from src.table_tennis.scoring.game import Game
def test_game():
    game = Game("Ola", "Per")
    assert game.player1 == "Ola"
    assert game.player2 == "Per"
    assert game.score_a == 0 
    assert game.score_b == 0 
    assert game.is_finished is False
    assert game.winner is None
