from table_tennis.rating.player import Player


def test_player_initializes_attributes():
    player = Player("Alice")

    assert player.name == "Alice"
    assert player.elo == 1000
    assert player.k_fac == 40
    assert player.games_played == 0


def test_update_k_changes_with_game_count():
    player = Player("Bob", games_played=9)
    player.update_k()
    assert player.k_fac == 40

    player.games_played = 10
    player.update_k()
    assert player.k_fac == 20

    player.games_played = 20
    player.update_k()
    assert player.k_fac == 10
