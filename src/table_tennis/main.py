import sys

from .scoring.game import Game
from .scoring.match import Match
from .rating import Elo
from .rating.json_helpers import TABLES, write_to_elo_ranking_json, write_to_match

def main():
    # Windows consoles default to cp1252, which crashes on names like "Łukasz"
    sys.stdout.reconfigure(encoding="utf-8")

    print("🏓 Table Tennis")
    print()

    # Which table, since ratings are kept per table
    for number, name in enumerate(TABLES, start=1):
        print(f"  {number}. {name}")
    table = None
    while table is None:
        choice = input("Table: ")
        if choice.isdigit() and 1 <= int(choice) <= len(TABLES):
            table = TABLES[int(choice) - 1]
        elif choice in TABLES:
            table = choice
        else:
            print("Please pick one of the numbers above")
    print()
    print(f"Playing at {table}")
    print()

    # Initializing players
    player1_name, player2_name = str(input("Player 1 name: ")), str(input("Player 2 name: "))
    assert(player1_name != player2_name)
    elo_game_instance = Elo(player1_name, player2_name, table)

    # Setting up game and elo instance
    game = Game(player1_name=player1_name, player2_name=player2_name)

    while not game.is_finished:
        print(f"Score: {game.score_a} - {game.score_b}")

        point_given = False
        while not point_given:
            player = input("Who scored? (A/B): ").upper()
            if player == "A":
                game.point_to_a()
                point_given = True
            elif player == "B":
                game.point_to_b()
                point_given = True
            else:
                print("Please enter name again")
        print()

    print(f"Final score: {game.score_a} - {game.score_b}")
    print(f"Player {game.winner} wins!")

    # ponytail: the CLI plays one game, recorded as a one-game match
    match = Match(player1_name, player2_name, [(game.score_a, game.score_b)], table)
    elo_game_instance.calculate_change(match.winner)

    write_to_match(match)
    write_to_elo_ranking_json(table)

if __name__ == "__main__":
    main()
