import pytest

from table_tennis.scoring.game import Game
from table_tennis.scoring.match import Match


@pytest.mark.parametrize("score,finished", [
    ((11, 9), True),     # standard win
    ((11, 0), True),
    ((12, 10), True),    # won on the two-point margin
    ((15, 13), True),
    ((9, 11), True),
    ((11, 10), False),   # one point clear, play on
    ((5, 3), False),     # unfinished
    ((0, 0), False),
    ((12, 9), False),    # impossible: would have ended at 11-9
    ((20, 2), False),
])
def test_is_finished_accepts_only_real_scores(score, finished):
    assert Game("a", "b", *score).is_finished is finished


def test_point_by_point_still_works():
    game = Game("a", "b")
    for _ in range(11):
        game.point_to_a()
    assert (game.score_a, game.winner) == (11, "a")
    game.point_to_a()  # ignored once finished
    assert game.score_a == 11


def test_match_counts_games_and_derives_winner():
    match = Match("Ola", "Kari", [(11, 9), (8, 11), (11, 7), (11, 5)], "Stripa")
    assert (match.games_won_a, match.games_won_b) == (3, 1)
    assert match.winner == "Ola"
    assert match.is_valid


def test_match_is_invalid_on_a_draw():
    match = Match("Ola", "Kari", [(11, 9), (9, 11)], "Stripa")
    assert match.winner is None
    assert not match.is_valid


def test_match_is_invalid_with_an_unfinished_game():
    assert not Match("Ola", "Kari", [(11, 9), (5, 3)], "Stripa").is_valid


def test_match_is_invalid_when_empty():
    assert not Match("Ola", "Kari", [], "Stripa").is_valid
