import pytest

from table_tennis.server import MAX_GAMES, build_match


def test_accepts_a_valid_match():
    match = build_match({"table": "Stripa", "player_a": " Ola ", "player_b": "Kari", "games": [[11, 9], [11, 7]]})
    assert (match.player_A, match.player_B) == ("Ola", "Kari")
    assert match.winner == "Ola"


@pytest.mark.parametrize("payload,message", [
    ("not a dict", "json object"),
    ({"table": "Stripa", "player_b": "Kari", "games": [[11, 9]]}, "player_a is required"),
    ({"table": "Stripa", "player_a": "  ", "player_b": "Kari", "games": [[11, 9]]}, "player_a is required"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Ola", "games": [[11, 9]]}, "must be different"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": []}, "at least one game"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": "11-9"}, "at least one game"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11, 9]] * (MAX_GAMES + 1)}, "at most"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11]]}, "need two scores"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [["11", "9"]]}, "whole numbers"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11, 9.5]]}, "whole numbers"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11, -1]]}, "whole numbers"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[12, 9]]}, "not a finished game"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11, 10]]}, "not a finished game"),
    ({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [[11, 9], [9, 11]]}, "draw"),
])
def test_rejects_bad_payloads(payload, message):
    with pytest.raises(ValueError, match=message):
        build_match(payload)


@pytest.mark.parametrize("table", [None, "", "Gløshaugen", "stripa", 7])
def test_rejects_unknown_tables(table):
    payload = {"table": table, "player_a": "Ola", "player_b": "Kari", "games": [[11, 9]]}
    with pytest.raises(ValueError, match="one of the tables"):
        build_match(payload)


def test_keeps_the_table_on_the_match():
    assert build_match({
        "table": "Kjelhuset", "player_a": "Ola", "player_b": "Kari", "games": [[11, 9]],
    }).table == "Kjelhuset"


@pytest.mark.parametrize("a,b", [
    ("Ola", "OLA"), ("Ola", "ola"), ("Ola", " Ola "), ("Ola Nordmann", "ola  nordmann"),
])
def test_cannot_play_yourself_by_changing_case_or_spacing(a, b):
    with pytest.raises(ValueError, match="must be different"):
        build_match({"table": "Stripa", "player_a": a, "player_b": b, "games": [[11, 9]]})


@pytest.mark.parametrize("score", [[11, True], [True, 11], [11, False]])
def test_booleans_are_not_scores(score):
    # bool subclasses int, so json true would otherwise be accepted as 1
    with pytest.raises(ValueError, match="whole numbers"):
        build_match({"table": "Stripa", "player_a": "Ola", "player_b": "Kari", "games": [score]})


def test_name_length_is_capped():
    with pytest.raises(ValueError, match="too long"):
        build_match({"table": "Stripa", "player_a": "x" * 200, "player_b": "Kari",
                     "games": [[11, 9]]})


def test_names_keep_their_spelling_but_lose_stray_spacing():
    match = build_match({"table": "Stripa", "player_a": "  Ola   Nordmann ",
                         "player_b": "Kari", "games": [[11, 9]]})
    assert match.player_A == "Ola Nordmann"
