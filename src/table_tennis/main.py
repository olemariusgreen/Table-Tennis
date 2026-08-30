from table_tennis.scoring.game import Game


def main():
    game = Game()

    print("🏓 Table Tennis")
    print()

    while not game.is_finished:
        print(f"Score: {game.score_a} - {game.score_b}")

        player = input("Who scored? (A/B): ").upper()

        if player == "A":
            game.point_to_a()
        elif player == "B":
            game.point_to_b()
        else:
            print("Please enter A or B.")

        print()

    print(f"Final score: {game.score_a} - {game.score_b}")
    print(f"Player {game.winner} wins!")


if __name__ == "__main__":
    main()