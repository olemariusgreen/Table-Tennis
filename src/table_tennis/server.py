"""Serves website/ and records matches, reusing the rating code as-is.

ponytail: single-threaded http.server bound to localhost. Being single-threaded
serializes every write, so two people recording at once cannot lose each other's
update. Swap in waitress/Flask behind a reverse proxy if this ever faces the
public internet.
"""
import argparse
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .rating import Elo
from .rating.json_helpers import (
    TABLES,
    canonical_name,
    resolve_players,
    write_to_elo_ranking_json,
    write_to_match,
)
from .scoring.match import Match

ROOT = Path(__file__).resolve().parents[2]
WEBSITE = ROOT / "website"
DATA = ROOT / "data"
ASSETS = ROOT / "website" / "assets"

MAX_BODY = 4096      # a match payload is a few hundred bytes
MAX_GAMES = 9        # best-of-9 is already generous
MAX_POINTS = 99
MAX_NAME = 40       # keeps a silly-long name out of the leaderboard

# Only these are public under /data/. An allowlist, so a file added to a table's
# directory later is never served by accident.
PUBLIC_DATA = {"players.json", "matches.json", "elo_ranking.json"}


def _clean_names(payload):
    names = []
    for key in ("player_a", "player_b"):
        name = payload.get(key)
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{key} is required")
        if len(name.strip()) > MAX_NAME:
            raise ValueError(f"{key} is too long")
        names.append(" ".join(name.split()))
    # compared canonically, so "Ola" cannot play "OLA" for free elo
    if canonical_name(names[0]) == canonical_name(names[1]):
        raise ValueError("the two players must be different")
    return names


def _clean_scores(payload):
    games = payload.get("games")
    if not isinstance(games, list) or not games:
        raise ValueError("at least one game is required")
    if len(games) > MAX_GAMES:
        raise ValueError(f"at most {MAX_GAMES} games")
    scores = []
    for i, pair in enumerate(games, start=1):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"game {i}: need two scores")
        # bool is a subclass of int, so json true would otherwise count as 1
        if not all(isinstance(s, int) and not isinstance(s, bool) and 0 <= s <= MAX_POINTS
                   for s in pair):
            raise ValueError(f"game {i}: scores must be whole numbers")
        scores.append(tuple(pair))
    return scores


def build_match(payload) -> Match:
    """Validate an /api/match payload. Raises ValueError with a displayable message."""
    if not isinstance(payload, dict):
        raise ValueError("expected a json object")
    table = payload.get("table")
    if table not in TABLES:
        raise ValueError("pick one of the tables")
    name_a, name_b = _clean_names(payload)
    match = Match(name_a, name_b, _clean_scores(payload), table)
    match.pins = (payload.get("pin_a"), payload.get("pin_b"))
    for i, game in enumerate(match.games, start=1):
        if not game.is_finished:
            raise ValueError(f"game {i}: {game.score_a}-{game.score_b} is not a finished game")
    if match.winner is None:
        raise ValueError("the match is a draw, so there is no winner")
    return match


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBSITE), **kwargs)

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        for prefix, directory in (("/data/", DATA), ("/assets/", ASSETS)):
            if clean.startswith(prefix):
                # dropping "." and ".." segments keeps /data/../../secret inside
                parts = [p for p in clean[len(prefix):].split("/") if p not in ("", ".", "..")]
                if not parts:
                    return str(directory)
                if directory is DATA and parts[-1] not in PUBLIC_DATA:
                    return str(DATA / "__not_public__")   # 404s
                return str(directory.joinpath(*parts))
        return super().translate_path(path)

    def end_headers(self):
        # Cloudflare caches css/js at its edge by default, which serves a stale
        # stylesheet for hours after an edit and would let a leaderboard go stale
        # too. Nothing here is worth caching: the origin is one small local server.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/tables":
            self._send_json(200, {"tables": TABLES})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/match":
            self.send_error(404)
            return
        try:
            match = build_match(self._read_json())
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        # both codes before anything is written, so a wrong one changes nothing
        try:
            names = resolve_players((match.player_A, match.player_B), match.pins)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        # rebuild under the spelling each player is registered with, so the same
        # person typed a different way lands on one rating rather than two
        if names != [match.player_A, match.player_B]:
            match = Match(names[0], names[1],
                          [(g.score_a, g.score_b) for g in match.games], match.table)

        elo = Elo(match.player_A, match.player_B, match.table)
        elo.calculate_change(match.winner)
        write_to_match(match)
        write_to_elo_ranking_json(match.table)

        self._send_json(200, {
            "table": match.table,
            "winner": match.winner,
            "games_won": [match.games_won_a, match.games_won_b],
            "elo": {p.name: round(p.elo, 2) for p in (elo.player_A, elo.player_B)},
        })

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise ValueError("bad Content-Length")
        if length <= 0:
            raise ValueError("empty request")
        if length > MAX_BODY:
            raise ValueError("request too large")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("body is not valid json")

    def _send_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main():
    # Windows consoles default to cp1252, which crashes on names like "Łukasz"
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Serve the table tennis site")
    parser.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to expose on the LAN")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # json_helpers uses paths relative to the cwd
    os.chdir(ROOT)

    try:
        server = HTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print(f"Could not start on port {args.port}: {exc}")
        print(f"Something else is probably using it. Try:  python run.py --port {args.port + 1}")
        raise SystemExit(1)

    print(f"Table tennis is running. Open:  http://{args.host}:{args.port}", flush=True)
    print("Press ctrl-c to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
