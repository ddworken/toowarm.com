"""
Ultra-Fast AlphaZero Demo - Uses pure policy for evaluation
"""

import torch
import numpy as np
from boop_alphazero_train import AlphaZeroTrainer
from boop_alphazero_network import BoopNetWrapper
from boop_game import BoopGame, Color
from boop_strategies import RandomStrategy, GreedyStrategy, SmartStrategy

def ultra_fast_demo():
    """Ultra-fast demonstration with minimal MCTS for self-play, pure policy for evaluation"""
    print("="*70)
    print("ULTRA-FAST ALPHAZERO TRAINING")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n")

    # Minimal settings
    trainer = AlphaZeroTrainer(
        num_simulations=3,          # Ultra-minimal MCTS
        num_self_play_games=5,      # 5 games for better data
        num_training_epochs=2,
        batch_size=16,
        replay_buffer_size=500,
        learning_rate=0.005,
        temperature_threshold=3,
        device=device
    )

    print("Ultra-Fast Strategy:")
    print("- Self-play: 5 games with 3 MCTS sims")
    print("- Evaluation: Pure policy network (NO MCTS) for speed!")
    print("- Evaluate every 3 iterations with 15 games each")
    print("- Target: 30 iterations\n")

    # Pure policy evaluator (no MCTS)
    def evaluate_pure_policy(neural_net, opponent, num_games=15):
        """Evaluate using pure policy network without MCTS"""
        wins = 0
        for game_num in range(num_games):
            game = BoopGame(verbose=False)

            as_player_0 = (game_num % 2 == 0)

            while not game.is_game_over():
                if (as_player_0 and game.state.current_player_idx == 0) or \
                   (not as_player_0 and game.state.current_player_idx == 1):
                    # AlphaZero's turn - use pure policy
                    policy, _ = neural_net.predict(game.state)
                    action_idx = policy.argmax()
                    action = neural_net.decode_action(action_idx)

                    if action is None:
                        action = game.get_valid_moves()[0] if game.get_valid_moves() else None

                    if action:
                        game.play_move(*action)
                else:
                    # Opponent's turn
                    action = opponent.choose_move(game)
                    game.play_move(*action)

            winner = game.get_winner()
            if winner:
                if (as_player_0 and winner == Color.ORANGE) or \
                   (not as_player_0 and winner == Color.GRAY):
                    wins += 1

        return wins / num_games

    # Training loop
    total_iterations = 30
    eval_frequency = 3

    for i in range(total_iterations):
        print(f"\n{'='*70}")
        print(f"ITERATION {i+1}/{total_iterations}")
        print(f"{'='*70}")

        # Self-play
        trainer.run_self_play()
        print(f"Replay buffer: {len(trainer.replay_buffer)} examples")

        # Training
        trainer.train()

        # Fast evaluation every N iterations
        if (i + 1) % eval_frequency == 0 or i == 0:
            print(f"\n>>> FAST EVALUATION (Pure Policy) <<<")

            random_wr = evaluate_pure_policy(trainer.neural_net, RandomStrategy(), 15)
            greedy_wr = evaluate_pure_policy(trainer.neural_net, GreedyStrategy(), 15)
            smart_wr = evaluate_pure_policy(trainer.neural_net, SmartStrategy(), 15)

            print(f"  vs Random:  {random_wr*100:.1f}%")
            print(f"  vs Greedy:  {greedy_wr*100:.1f}%")
            print(f"  vs Smart:   {smart_wr*100:.1f}%")

            # Record for history
            trainer.history['iteration'].append(trainer.iteration + 1)
            trainer.history['win_rate_vs_random'].append(random_wr)
            trainer.history['win_rate_vs_greedy'].append(greedy_wr)
            trainer.history['win_rate_vs_smart'].append(smart_wr)

            # Early stopping
            if i >= 15 and smart_wr >= 0.70 and greedy_wr >= 0.70:
                print(f"\n{'='*70}")
                print("SUCCESS! Consistently beating all strategies!")
                print(f"{'='*70}")
                break

        trainer.iteration += 1

    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")

    # Save model
    model_path = "boop_alphazero_ultra_fast.pt"
    trainer.neural_net.save(model_path)
    print(f"\nModel saved to {model_path}")

    # Final evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION (30 games, pure policy)")
    print(f"{'='*70}")

    final_random = evaluate_pure_policy(trainer.neural_net, RandomStrategy(), 30)
    final_greedy = evaluate_pure_policy(trainer.neural_net, GreedyStrategy(), 30)
    final_smart = evaluate_pure_policy(trainer.neural_net, SmartStrategy(), 30)

    print(f"  vs Random:  {final_random*100:.1f}%")
    print(f"  vs Greedy:  {final_greedy*100:.1f}%")
    print(f"  vs Smart:   {final_smart*100:.1f}%")

    return trainer

if __name__ == "__main__":
    trainer = ultra_fast_demo()
