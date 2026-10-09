from .player import Player
import json
import re
from datetime import datetime
from pathlib import Path

# The tables at NTNU. Each keeps its own ratings, so a player is rated per table.
TABLES = ["Matteland", "Valgrinda", "Stripa", "Kjelhuset", "Realfagsbygget"]

# Player pins live outside data/, which the server publishes. Ratings are
# per table, but a person is one person, so their pin is not.
PINS = Path("pins.json")

def table_dir(table: str) -> Path:
    """Storage directory for one table. Raises ValueError for an unknown table."""
    if table not in TABLES:
        raise ValueError(f"unknown table: {table!r}")
    return Path("data") / re.sub(r"[^a-z0-9]+", "-", table.lower()).strip("-")

def _load(path: Path) -> dict:
    """Read a json dict, creating an empty one if the file is missing."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))

def _dump(path: Path, data) -> None:
    """Write json atomically, so a crash mid-write cannot corrupt the existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)

def write_to_elo_ranking_json(table: str):
    players = _load(table_dir(table) / "players.json").get("players", {})

    sorted_players = sorted(players.items(), key=lambda x: x[1]["elo"], reverse=True)

    rankings = [
        {"rank": rank, "name": name, "elo": data["elo"], "games_played": data["games_played"]}
        for rank, (name, data) in enumerate(sorted_players, start=1)
    ]

    _dump(table_dir(table) / "elo_ranking.json", rankings)

def write_to_match(match):
    path = table_dir(match.table) / "matches.json"
    data = _load(path)
    matches = data.setdefault("matches", [])
    matches.append({
        "player_a": match.player_A,
        "player_b": match.player_B,
        "winner": match.winner,
        "games_won_a": match.games_won_a,
        "games_won_b": match.games_won_b,
        "games": [[g.score_a, g.score_b] for g in match.games],
        "played_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    })
    _dump(path, data)

def write_players(players, table: str):
    """Persist Player instances into one table's players.json in a single read/write."""
    path = table_dir(table) / "players.json"
    data = _load(path)
    stored = data.setdefault("players", {})
    for player in players:
        stored[player.name] = player.to_dict()
    _dump(path, data)

def canonical_name(name: str) -> str:
    """Identity key for a player: case- and spacing-insensitive.

    Without this, "Ola", "ola" and "OLA" are three different players, which both
    defeats the pin (claim a taken name in different case) and lets someone play
    themselves for free elo.
    """
    return " ".join(name.split()).casefold()

def _valid_pin(pin) -> bool:
    # bool is an int subclass and str.isdigit() accepts superscripts, so be strict
    return isinstance(pin, str) and len(pin) == 4 and all(c in "0123456789" for c in pin)

def resolve_players(names, pins) -> list:
    """Check both players' codes, then return the spelling each is registered under.

    All-or-nothing: every existing player is verified before any new one is
    registered, so a rejected match never leaves a code behind for a name that
    was never used.

    Codes are kept as typed so they can be looked up and handed back to whoever
    forgot theirs. They stop a club mate logging matches in your name; they are
    not authentication, and pins.json stays out of the published data/ dir.
    """
    for name, pin in zip(names, pins):
        if not _valid_pin(pin):
            raise ValueError(f"{name} needs a 4-digit code")

    data = _load(PINS)
    registered = data.setdefault("pins", {})

    # pass 1: verify everyone who already exists, changing nothing
    for name, pin in zip(names, pins):
        record = registered.get(canonical_name(name))
        if record and record["code"] != pin:
            raise ValueError(f"wrong code for {name}")

    # pass 2: only now register whoever is new
    display = []
    changed = False
    for name, pin in zip(names, pins):
        key = canonical_name(name)
        record = registered.get(key)
        if record is None:
            record = registered[key] = {
                "display": " ".join(name.split()),
                "code": pin,
                "registered": datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            changed = True
        display.append(record["display"])

    if changed:
        _dump(PINS, data)
    return display

def reset_pin(player_name: str) -> str:
    """Forget a player's code so they can set a new one on their next match."""
    data = _load(PINS)
    registered = data.setdefault("pins", {})
    record = registered.pop(canonical_name(player_name), None)
    if record is None:
        raise ValueError(f"no player called {player_name!r}")
    _dump(PINS, data)
    return record["display"]

def registered_players() -> list:
    """Every registered player as (name, code), for looking up a forgotten one."""
    records = _load(PINS).get("pins", {}).values()
    return sorted((r["display"], r["code"]) for r in records)

def who_is_json(player_name: str, table: str) -> dict:
    """This player's rating at this table, creating it at 1000 on first appearance."""
    path = table_dir(table) / "players.json"
    data = _load(path)
    players = data.setdefault("players", {})
    if player_name not in players:
        players[player_name] = Player(name=player_name).to_dict()
        _dump(path, data)
    return players[player_name]
