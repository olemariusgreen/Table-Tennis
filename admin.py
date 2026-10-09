"""Admin jobs:  python admin.py list
                python admin.py reset "Ola Nordmann"

"list" shows everyone's code, so when someone forgets theirs you can just look
it up and tell them. "reset" is for when they would rather pick a new one: it
unregisters them, and the next code they type when recording becomes their new
one. Their elo and match history are not touched either way.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from table_tennis.rating.json_helpers import registered_players, reset_pin


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show everyone and their code")
    reset = sub.add_parser("reset", help="forget one player's code")
    reset.add_argument("name", help="player name; case and spacing do not matter")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")   # Windows consoles default to cp1252

    if args.command == "list":
        players = registered_players()
        if not players:
            print("Nobody has registered yet.")
            return
        width = max(len(name) for name, _ in players)
        print(f"{len(players)} registered:")
        for name, code in players:
            print(f"  {name:<{width}}  {code}")
        return

    try:
        name = reset_pin(args.name)
    except ValueError as exc:
        print(exc)
        print("Try:  python admin.py list")
        raise SystemExit(1)
    print(f"Reset {name}.")
    print("The next code they enter when recording a match becomes their new one,")
    print("so tell them to record with whatever code they want from now on.")


if __name__ == "__main__":
    main()
