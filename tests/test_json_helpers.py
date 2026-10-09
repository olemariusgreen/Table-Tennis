import json
from pathlib import Path

import pytest

from table_tennis.rating import Elo
from table_tennis.rating.json_helpers import (
    canonical_name,
    registered_players,
    reset_pin,
    resolve_players,
    table_dir,
    who_is_json,
    write_players,
    write_to_elo_ranking_json,
    write_to_match,
)
from table_tennis.scoring.match import Match


TABLE = "Stripa"
OTHER = "Matteland"


@pytest.fixture(autouse=True)
def in_tmp_cwd(tmp_path, monkeypatch):
    """The json paths are relative to the cwd, so every test gets a fresh one."""
    monkeypatch.chdir(tmp_path)


def at(name, table=TABLE):
    return table_dir(table) / name


def test_creates_players_json_when_missing():
    assert not at("players.json").exists()
    assert who_is_json("Ola", TABLE) == {"elo": 1000.0, "k_fac": 40, "games_played": 0}
    assert at("players.json").exists()


def test_same_minute_matches_do_not_overwrite_each_other():
    match = Match("Ola", "Kari", [(11, 9)], TABLE)
    write_to_match(match)
    write_to_match(match)
    records = json.loads(at("matches.json").read_text(encoding="utf-8"))["matches"]
    assert len(records) == 2


def test_match_record_keeps_names_games_and_point_scores():
    write_to_match(Match("Ola", "Kari", [(11, 9), (8, 11), (11, 7), (11, 5)], TABLE))
    record = json.loads(at("matches.json").read_text(encoding="utf-8"))["matches"][0]
    assert record["player_a"] == "Ola" and record["player_b"] == "Kari"
    assert record["winner"] == "Ola"
    assert (record["games_won_a"], record["games_won_b"]) == (3, 1)
    assert record["games"] == [[11, 9], [8, 11], [11, 7], [11, 5]]
    assert record["played_at"].startswith("20")


def test_non_ascii_names_are_written_as_utf8():
    who_is_json("Łukasz", TABLE)
    write_to_match(Match("Łukasz", "Bjørn", [(11, 9)], TABLE))
    write_to_elo_ranking_json(TABLE)
    for path in table_dir(TABLE).glob("*.json"):
        raw = path.read_bytes()
        raw.decode("utf-8")  # raises if it was written as cp1252
    assert b"\xc5\x81ukasz" in at("players.json").read_bytes()


def test_elo_is_stored_as_a_float():
    elo = Elo("Ola", "Kari", TABLE)
    elo.calculate_change("Ola")
    players = json.loads(at("players.json").read_text(encoding="utf-8"))["players"]
    assert isinstance(players["Ola"]["elo"], float)
    assert players["Ola"]["elo"] > 1000 > players["Kari"]["elo"]


def test_both_players_advance_games_and_k_factor():
    elo = Elo("Ola", "Kari", TABLE)
    elo.player_A.games_played = 9
    elo.player_B.games_played = 9
    elo.calculate_change("Ola")
    players = json.loads(at("players.json").read_text(encoding="utf-8"))["players"]
    # k drops to 20 at 10 games -- player_B used to be skipped entirely
    for name in ("Ola", "Kari"):
        assert players[name]["games_played"] == 10, name
        assert players[name]["k_fac"] == 20, name


def test_atomic_write_leaves_no_temp_file():
    write_players([], TABLE)
    write_to_match(Match("Ola", "Kari", [(11, 9)], TABLE))
    write_to_elo_ranking_json(TABLE)
    assert list(table_dir(TABLE).glob("*.json"))
    assert not list(table_dir(TABLE).glob("*.tmp"))


def test_ranking_is_sorted_by_elo():
    who_is_json("Low", TABLE)
    Elo("Winner", "Loser", TABLE).calculate_change("Winner")
    write_to_elo_ranking_json(TABLE)
    ranking = json.loads(at("elo_ranking.json").read_text(encoding="utf-8"))
    assert [r["rank"] for r in ranking] == [1, 2, 3]
    assert ranking[0]["name"] == "Winner" and ranking[-1]["name"] == "Loser"


def test_tables_are_rated_independently():
    Elo("Ola", "Kari", TABLE).calculate_change("Ola")
    write_to_elo_ranking_json(TABLE)

    # untouched at the other table
    assert who_is_json("Ola", OTHER)["elo"] == 1000.0
    assert json.loads(at("players.json").read_text(encoding="utf-8"))["players"]["Ola"]["elo"] > 1000
    assert at("players.json", TABLE) != at("players.json", OTHER)


def test_unknown_table_is_rejected():
    with pytest.raises(ValueError, match="unknown table"):
        who_is_json("Ola", "Gløshaugen")


# --- player codes -----------------------------------------------------------

def test_code_registers_on_first_sight_then_must_match():
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    with pytest.raises(ValueError, match="wrong code for Ola"):
        resolve_players(["Ola", "Kari"], ["9999", "5678"])


def test_code_is_readable_so_a_forgotten_one_can_be_handed_back():
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    assert registered_players() == [("Kari", "5678"), ("Ola", "1234")]


@pytest.mark.parametrize("bad", ["123", "12345", "abcd", "", None, 1234, "12 4", "１２３４"])
def test_code_must_be_four_digits(bad):
    with pytest.raises(ValueError, match="4-digit code"):
        resolve_players(["Ola", "Kari"], [bad, "5678"])


def test_code_file_is_outside_the_published_data_dir():
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    assert Path("pins.json").exists()
    assert not list(Path("data").rglob("pins.json"))


def test_case_does_not_let_you_claim_a_taken_name():
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    # "ola" is the same person, so the registered code still applies
    with pytest.raises(ValueError, match="wrong code"):
        resolve_players(["ola", "Kari"], ["0000", "5678"])
    # and the right code resolves back to the registered spelling
    assert resolve_players(["  OLA ", "Kari"], ["1234", "5678"])[0] == "Ola"


def test_rejected_match_registers_nobody():
    resolve_players(["Kari"], ["5678"])
    with pytest.raises(ValueError, match="wrong code for Kari"):
        resolve_players(["Newbie", "Kari"], ["4242", "0000"])
    # Newbie was never stored, so they are still free to pick any code
    assert resolve_players(["Newbie", "Kari"], ["9999", "5678"])[0] == "Newbie"


def test_reset_lets_a_player_pick_a_new_code():
    resolve_players(["Ola", "Kari"], ["1234", "5678"])
    assert reset_pin("ola") == "Ola"          # case-insensitive for the admin
    assert resolve_players(["Ola", "Kari"], ["4321", "5678"]) == ["Ola", "Kari"]
    with pytest.raises(ValueError, match="no player called"):
        reset_pin("Nobody")


def test_canonical_name_folds_case_and_spacing():
    assert canonical_name("Ola") == canonical_name(" OLA ") == canonical_name("ola")
    assert canonical_name("Ola  Nordmann") == canonical_name("ola nordmann")
    assert canonical_name("Ola") != canonical_name("Kari")
