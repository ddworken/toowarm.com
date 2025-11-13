#!/usr/bin/env python3
"""
AlphaZero Training - Smart configuration:
- Fast self-play with 5 MCTS sims
- Strong evaluation with 25 MCTS sims
"""

import sys
import torch
from boop_alphazero_train import AlphaZeroTrainer
from boop_mcts import MCTS
from boop_alphazero_strategy import AlphaZeroStrategy

def train_smart():
    """Train with smart simulation strategy"""
    print("="*70, flush=True)
    print("ALPHAZERO SMART TRAINING", flush=True)
    print("="*70, flush=True)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n", flush=True)

    # Fast self-play with minimal MCTS
    trainer = AlphaZeroTrainer(
        num_simulations=5,           # Fast for self-play
        num_self_play_games=5,
        num_training_epochs=3,
        batch_size=32,
        replay_buffer_size=2000,
        learning_rate=0.002,
        temperature_threshold=5,
        device=device
    )

    print("Smart Configuration:", flush=True)
    print("- Self-play: 5 MCTS simulations (FAST)", flush=True)
    print("- Evaluation: 25 MCTS simulations (STRONG)", flush=True)
    print("- This balances training speed with evaluation quality\n", flush=True)

    max_iterations = 60
    eval_frequency = 10

    for i in range(max_iterations):
        iteration_num = i + 1
        print(f"\n{'='*70}", flush=True)
        print(f"ITERATION {iteration_num}/{max_iterations}", flush=True)
        print(f"{'='*70}", flush=True)

        # Fast self-play with 5 sims
        print("Self-play (5 MCTS sims)...", flush=True)
        trainer.run_self_play()
        print(f"  Buffer: {len(trainer.replay_buffer)} examples", flush=True)

        # Train
        print("Training...", flush=True)
        trainer.train()

        # Evaluate with STRONG mcts (25 sims)
        if iteration_num % eval_frequency == 0 or iteration_num == 1:
            print(f"\n{'='*20} EVALUATION {'='*20}", flush=True)
            print("Evaluating with 25 MCTS simulations (this takes longer)...", flush=True)

            # Create strong evaluator
            strong_strategy = AlphaZeroStrategy(
                model_path=None,  # Use current model
                num_simulations=25,  # STRONG evaluation
                temperature=0.0,
                device=device
            )
            # Load current weights
            strong_strategy.neural_net.model = trainer.neural_net.model

            # Evaluate against baselines
            from boop_strategies import RandomStrategy, GreedyStrategy, SmartStrategy
            from boop_game import BoopGame, Color

            def evaluate_strong(num_games=12):
                """Evaluate with strong MCTS"""
                results = {}
                strategies = {
                    'Random': RandomStrategy(),
                    'Greedy': GreedyStrategy(),
                    'Smart': SmartStrategy()
                }

                for name, opponent in strategies.items():
                    wins = 0
                    for game_num in range(num_games):
                        game = BoopGame(verbose=False)
                        as_player_0 = (game_num % 2 == 0)

                        while not game.is_game_over():
                            if (as_player_0 and game.state.current_player_idx == 0) or \
                               (not as_player_0 and game.state.current_player_idx == 1):
                                # AlphaZero turn
                                action = strong_strategy.choose_move(game)
                                game.play_move(*action)
                            else:
                                # Opponent turn
                                action = opponent.choose_move(game)
                                game.play_move(*action)

                        winner = game.get_winner()
                        if winner:
                            if (as_player_0 and winner == Color.ORANGE) or \
                               (not as_player_0 and winner == Color.GRAY):
                                wins += 1

                    results[name] = wins / num_games

                return results

            results = evaluate_strong(12)

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)

            print(f"\nResults (iteration {iteration_num}, 25 MCTS sims):", flush=True)
            print(f"  vs Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  vs Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  vs Smart:   {smart_wr*100:5.1f}%", flush=True)

            # Record
            trainer.history['iteration'].append(iteration_num)
            trainer.history['win_rate_vs_random'].append(random_wr)
            trainer.history['win_rate_vs_greedy'].append(greedy_wr)
            trainer.history['win_rate_vs_smart'].append(smart_wr)

            # Check for success
            if iteration_num >= 20:
                if smart_wr >= 0.70 and greedy_wr >= 0.70:
                    print(f"\n{'='*70}", flush=True)
                    print("SUCCESS! AlphaZero beats all strategies!", flush=True)
                    print(f"{'='*70}", flush=True)
                    break

            # Save checkpoint
            if iteration_num % 20 == 0:
                checkpoint_path = f"boop_alphazero_smart_iter{iteration_num}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"Checkpoint saved: {checkpoint_path}", flush=True)
        else:
            trainer.iteration += 1
            print(f"  (next evaluation at iteration {(iteration_num // eval_frequency + 1) * eval_frequency})", flush=True)

    # Final save
    print(f"\n{'='*70}", flush=True)
    print("TRAINING COMPLETE", flush=True)
    print(f"{'='*70}", flush=True)

    final_model_path = "boop_alphazero_smart_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model saved: {final_model_path}", flush=True)

    print(f"\nTotal iterations: {trainer.iteration}", flush=True)
    print(f"Final win rates:", flush=True)
    if trainer.history['win_rate_vs_smart']:
        print(f"  vs Random:  {trainer.history['win_rate_vs_random'][-1]*100:.1f}%", flush=True)
        print(f"  vs Greedy:  {trainer.history['win_rate_vs_greedy'][-1]*100:.1f}%", flush=True)
        print(f"  vs Smart:   {trainer.history['win_rate_vs_smart'][-1]*100:.1f}%", flush=True)

    return trainer

if __name__ == "__main__":
    trainer = train_smart()
