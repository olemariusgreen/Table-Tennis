from src.table_tennis.scoring.game import Game
def test_game():
    game = Game("Ola", "Per")
    assert game.player_a == "Ola"
    assert game.player_b == "Per"
    assert game.score_a == 0 
    assert game.score_b == 0 
    assert game.is_finished is False
    assert game.winner is None

def test_is_finished():
    game1 = Game("Petter", "Sofie")
    game2 = Game("Petter2", "Sofie2")
    for _ in range(11):
        game1.point_to_a()
    
    for _ in range(9):
        game1.point_to_b()

    for _ in range(10):
        game2.point_to_a()
        
    for _ in range(10):
        game2.point_to_b()
    assert game1.is_finished is True
    assert game2.is_finished is False 
    game2.point_to_a()
    game2.point_to_b()
    assert game2.is_finished is False 
    game2.point_to_a()
    game2.point_to_a()
    assert game2.is_finished is True

def test_points_not_awarded_when_finished():
    game = Game("Ole", "Ole Marius")
    for _ in range(11):
        game.point_to_a()
    game.point_to_a
    game.point_to_a
    assert game.score_a == 11

