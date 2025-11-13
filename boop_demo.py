"""
Quick Demo of BOOP Game - Shows two strategies playing against each other
"""

from boop_game import BoopGame
from boop_strategies import RandomStrategy, GreedyStrategy, DefensiveStrategy, SmartStrategy


def play_demo_game(strategy1, strategy2, verbose=True):
    """Play a single demo game between two strategies"""
    game = BoopGame(verbose=verbose)

    strategies = [strategy1, strategy2]

    print(f"\n{'='*70}")
    print(f"DEMO GAME: {strategy1.name} (Orange) vs {strategy2.name} (Gray)")
    print(f"{'='*70}\n")

    if verbose:
        print("Initial board:")
        print(game.state.board)

    move_count = 0
    max_moves = 200

    while not game.is_game_over() and move_count < max_moves:
        current_strategy = strategies[game.state.current_player_idx]
        current_color = game.state.get_current_player().color.value

        if verbose:
            print(f"\n--- Move {move_count + 1}: {current_strategy.name} ({current_color}) ---")

        try:
            move = current_strategy.choose_move(game)
            row, col, piece_type = move

            if verbose:
                print(f"Playing {piece_type.value} at ({row}, {col})")

            success = game.play_move(*move)

            if not success:
                print(f"Invalid move!")
                break

            move_count += 1

            if verbose:
                print(game.state.board)

        except Exception as e:
            print(f"Error: {e}")
            break

    winner = game.get_winner()

    print(f"\n{'='*70}")
    if winner:
        winner_name = strategy1.name if winner == strategies[0].color else strategy2.name
        print(f"GAME OVER! {winner_name} ({winner.value}) WINS in {move_count} moves!")
    else:
        print(f"GAME OVER! Draw or timeout after {move_count} moves")
    print(f"{'='*70}\n")

    return winner


def quick_tournament():
    """Run a quick tournament with fewer games"""
    print("\n" + "="*70)
    print("BOOP QUICK TOURNAMENT - 2 strategies, 5 games each")
    print("="*70 + "\n")

    # Use two strategies
    strategy1 = RandomStrategy()
    strategy2 = GreedyStrategy()

    results = {strategy1.name: 0, strategy2.name: 0}

    print(f"Matchup: {strategy1.name} vs {strategy2.name}")
    print()

    for game_num in range(5):
        # Alternate who goes first
        if game_num % 2 == 0:
            s1, s2 = strategy1, strategy2
        else:
            s1, s2 = strategy2, strategy1

        print(f"Game {game_num + 1}/5: {s1.name} (Orange) vs {s2.name} (Gray)")

        game = BoopGame(verbose=False)
        strategies = [s1, s2]

        move_count = 0
        max_moves = 200

        while not game.is_game_over() and move_count < max_moves:
            current_strategy = strategies[game.state.current_player_idx]
            move = current_strategy.choose_move(game)
            game.play_move(*move)
            move_count += 1

        winner = game.get_winner()

        if winner:
            # Winner is a Color enum, s1 played as Orange (player 0), s2 as Gray (player 1)
            from boop_game import Color
            if winner == Color.ORANGE:
                winner_name = s1.name
            else:
                winner_name = s2.name

            results[winner_name] += 1
            print(f"  Winner: {winner_name} in {move_count} moves")
        else:
            print(f"  Draw after {move_count} moves")

    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"{strategy1.name}: {results[strategy1.name]} wins")
    print(f"{strategy2.name}: {results[strategy2.name]} wins")
    print(f"{'='*70}\n")


def main():
    """Run demonstrations"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "tournament":
        quick_tournament()
    else:
        # Play a single demo game
        strategy1 = GreedyStrategy()
        strategy2 = DefensiveStrategy()

        play_demo_game(strategy1, strategy2, verbose=True)


if __name__ == "__main__":
    main()
