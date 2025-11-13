#!/usr/bin/env python3
"""
Evaluate existing checkpoint with strong MCTS to see real performance
"""

import torch
from boop_alphazero_strategy import AlphaZeroStrategy
from boop_strategies import RandomStrategy, GreedyStrategy, SmartStrategy, DefensiveStrategy, AggressiveStrategy
from boop_game import BoopGame, Color

def evaluate_checkpoint(checkpoint_path, num_simulations=50, num_games=30):
    """Evaluate checkpoint with strong MCTS"""

    print("="*70)
    print(f"EVALUATING CHECKPOINT: {checkpoint_path}")
    print(f"MCTS Simulations: {num_simulations}")
    print(f"Games per opponent: {num_games}")
    print("="*70)
    print()

    # Load checkpoint
    print(f"Loading checkpoint from {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    print(f"Checkpoint iteration: {checkpoint['iteration']}")
    print()

    # Create strong AlphaZero strategy
    az_strategy = AlphaZeroStrategy(
        model_path=None,
        num_simulations=num_simulations,
        temperature=0.0,
        device='cpu'
    )

    # Load checkpoint weights
    az_strategy.neural_net.model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Model loaded with {num_simulations} MCTS simulations per move")
    print()

    # Strategies to evaluate against
    opponents = {
        'Random': RandomStrategy(),
        'Greedy': GreedyStrategy(),
        'Smart': SmartStrategy(),
        'Defensive': DefensiveStrategy(),
        'Aggressive': AggressiveStrategy()
    }

    results = {}

    for name, opponent in opponents.items():
        print(f"Playing {num_games} games vs {name}...")
        wins = 0
        draws = 0
        losses = 0

        for game_num in range(num_games):
            game = BoopGame(verbose=False)
            as_player_0 = (game_num % 2 == 0)

            while not game.is_game_over():
                if (as_player_0 and game.state.current_player_idx == 0) or \
                   (not as_player_0 and game.state.current_player_idx == 1):
                    # AlphaZero's turn
                    action = az_strategy.choose_move(game)
                    game.play_move(*action)
                else:
                    # Opponent's turn
                    action = opponent.choose_move(game)
                    game.play_move(*action)

            winner = game.get_winner()
            if winner is None:
                draws += 1
            elif (as_player_0 and winner == Color.ORANGE) or \
                 (not as_player_0 and winner == Color.GRAY):
                wins += 1
            else:
                losses += 1

            if (game_num + 1) % 10 == 0:
                print(f"  Progress: {game_num + 1}/{num_games} games")

        win_rate = wins / num_games
        results[name] = win_rate

        print(f"  Results: {wins}W - {draws}D - {losses}L ({win_rate*100:.1f}% win rate)")
        print()

    print("="*70)
    print("FINAL RESULTS")
    print("="*70)
    for name, wr in results.items():
        print(f"  vs {name:12s}: {wr*100:5.1f}%")
    print()

    avg_wr = sum(results.values()) / len(results)
    print(f"Average win rate: {avg_wr*100:.1f}%")

    if results.get('Smart', 0) >= 0.70 and results.get('Greedy', 0) >= 0.70:
        print()
        print("="*70)
        print("SUCCESS! AlphaZero beats Smart and Greedy at 70%+!")
        print("="*70)

    return results

if __name__ == "__main__":
    import sys

    checkpoint_path = "boop_alphazero_checkpoint_iter20.pt"

    # Check if custom path provided
    if len(sys.argv) > 1:
        checkpoint_path = sys.argv[1]

    # Check if checkpoint exists
    import os
    if not os.path.exists(checkpoint_path):
        print(f"ERROR: Checkpoint not found: {checkpoint_path}")
        print()
        print("Available checkpoints:")
        import glob
        for f in glob.glob("boop_alphazero_*.pt"):
            print(f"  {f}")
        sys.exit(1)

    results = evaluate_checkpoint(checkpoint_path, num_simulations=50, num_games=30)
