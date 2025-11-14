#!/usr/bin/env python3
"""
BLAZING FAST CPU Training - Absolute minimum configuration
- Only 5 games per iteration
- Truncate long games
- Quick evaluations
- NO FRILLS - just train until victory!
"""

import torch
from boop_alphazero_train import AlphaZeroTrainer
from boop_game import BoopGame

def train_blazing_fast():
    """Fastest possible CPU training"""
    print("="*70, flush=True)
    print("BLAZING FAST CPU TRAINING", flush=True)
    print("="*70, flush=True)

    trainer = AlphaZeroTrainer(
        num_simulations=1,           # Minimal MCTS
        num_self_play_games=5,       # Only 5 games
        num_training_epochs=3,       # Moderate training
        batch_size=64,
        replay_buffer_size=5000,
        learning_rate=0.002,
        temperature_threshold=10,
        device='cpu'
    )

    print("Configuration:", flush=True)
    print("- 5 games per iteration (FAST)", flush=True)
    print("- Evaluate every 25 iterations", flush=True)
    print("- Training until 70%+ win rate!\n", flush=True)

    iteration = 0
    best_wr = 0.0

    while True:
        iteration += 1

        # Progress indicator
        if iteration % 5 == 1:
            print(f"Iteration {iteration}...", end=" ", flush=True)
        elif iteration % 5 == 0:
            print(f"{iteration}", flush=True)

        # Self-play and train
        trainer.run_self_play()
        trainer.train()
        trainer.iteration = iteration

        # Evaluate every 25 iterations
        if iteration % 25 == 0:
            print(f"\n{'='*70}", flush=True)
            print(f"EVALUATION AT ITERATION {iteration}", flush=True)
            print(f"{'='*70}", flush=True)

            results = trainer.evaluate(num_games=8)  # Quick eval

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)
            avg_wr = (random_wr + greedy_wr + smart_wr) / 3

            print(f"Results:", flush=True)
            print(f"  Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  Smart:   {smart_wr*100:5.1f}%", flush=True)
            print(f"  Average: {avg_wr*100:5.1f}%\n", flush=True)

            if avg_wr > best_wr:
                best_wr = avg_wr
                trainer.save_checkpoint(f"boop_fast_best_{int(avg_wr*100)}.pt")
                print(f"New best: {avg_wr*100:.1f}%", flush=True)

            # Victory check
            if smart_wr >= 0.70 and greedy_wr >= 0.70:
                print(f"{'='*70}", flush=True)
                print("VICTORY! 70%+ ACHIEVED!", flush=True)
                print(f"{'='*70}\n", flush=True)

                # Final eval
                final = trainer.evaluate(num_games=20)
                print(f"FINAL RESULTS (20 games):", flush=True)
                print(f"  Random:  {final.get('Random', 0)*100:.1f}%", flush=True)
                print(f"  Greedy:  {final.get('Greedy', 0)*100:.1f}%", flush=True)
                print(f"  Smart:   {final.get('Smart', 0)*100:.1f}%", flush=True)

                trainer.neural_net.save("boop_victory_model.pt")
                break

    print(f"\nCompleted after {iteration} iterations", flush=True)
    return trainer

if __name__ == "__main__":
    trainer = train_blazing_fast()
