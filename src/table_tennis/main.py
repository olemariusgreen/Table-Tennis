import json

from .scoring.game import Game
from .rating.player import Player, who_is_json
from .rating.elo import Elo

def main():
    game = Game()

    print("🏓 Table Tennis")
    print()

    player1_name = str(input("Player 1 name: "))
    player2_name = str(input("Player 2 name: "))
    player1_dict, player2_dict = who_is_json(player1_name), who_is_json(player2_name)
    player1, player2 = Player(name=player1_name, player_dict=player1_dict), Player(name=player2_name, player_dict=player2_dict)

    while not game.is_finished:
        print(f"Score: {game.score_a} - {game.score_b}")

        player = input("Who scored?: ").upper()

        point_given = False
        while not point_given:
            if player == player1_name:
                game.point_to_a()
                point_given = True
            elif player == player2_name:
                game.point_to_b()
                point_given = True
            else:
                print("Please enter name again")

        print()

    print(f"Final score: {game.score_a} - {game.score_b}")
    print(f"Player {game.winner} wins!")


if __name__ == "__main__":
    main()