import json

from .scoring.game import Game
from .rating import Elo

def main():

    print("🏓 Table Tennis")
    print()

    # Initializing players
    player1_name, player2_name = str(input("Player 1 name: ")), str(input("Player 2 name: "))
    assert(player1_name != player2_name)
    elo_game_instance = Elo(player1_name, player2_name)

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

    elo_game_instance.calculate_change(game.winner)

if __name__ == "__main__":
    main()