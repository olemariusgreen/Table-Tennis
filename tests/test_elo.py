from src.table_tennis.rating.elo import Elo

def test_register_player():
    elo = Elo()

    elo.register_player("Ole")

    player = elo.get_player("Ole")

    assert player.name == "Ole"
    assert player.elo == 1000
    assert player.k_fac == 40
    assert player.games_played == 0

def test_get_player():
    elo = Elo()

    elo.register_player("Ole", 1200)

    player = elo.get_player("Ole")

    assert player.name == "Ole"
    assert player.elo == 1200

def test_elo_change_equal_players():
    elo = Elo()

    elo.register_player("Ole")
    elo.register_player("Per")

    elo.calculate_change("Ole", "Per", "A")

    assert elo.get_player("Ole").elo == 1020
    assert elo.get_player("Per").elo == 980