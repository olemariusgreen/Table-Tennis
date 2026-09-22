import json

from .scoring.game import Game
from .rating.player import Player, who_is_json
from .rating.elo import Elo

def main():

    print("🏓 Table Tennis")
    print()

    # Initializing players
    player1_name, player2_name = str(input("Player 1 name: ")), str(input("Player 2 name: "))
    assert(player1_name != player2_name)
    player1_dict, player2_dict = who_is_json(player1_name), who_is_json(player2_name)
    player1, player2 = Player(name=player1_name, player_dict=player1_dict), Player(name=player2_name, player_dict=player2_dict)

    # Setting up game and elo instance
    game = Game(player1=player1, player2=player2)
    elo_game = Elo()
    elo_game.register_player([player1, player2])

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

    newEloA, newEloB = elo_game.calculate_change(game=game)

    player1.elo, player2.elo = newEloA, newEloB

    player1.write_to_player_json()
    player2.write_to_player_json()

if __name__ == "__main__":
    main()