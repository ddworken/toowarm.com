#!/usr/bin/env python3
"""
CPU-Optimized AlphaZero Training - Continuous training until victory!
Uses pure policy network (NO MCTS) for maximum speed, trains for hundreds of iterations
"""

import sys
import torch
import torch.nn.functional as F
from boop_alphazero_train import AlphaZeroTrainer
from boop_game import BoopGame, Color
import numpy as np

def train_continuous():
    """Train continuously with pure policy until model beats strategies"""
    print("="*70, flush=True)
    print("CONTINUOUS CPU TRAINING - PURE POLICY FOR SPEED", flush=True)
    print("="*70, flush=True)

    device = 'cpu'
    print(f"Using device: {device}\n", flush=True)

    # NO MCTS during training - pure policy for maximum speed!
    trainer = AlphaZeroTrainer(
        num_simulations=1,  # Minimal
        num_self_play_games=20,  # Many games
        num_training_epochs=5,  # More learning
        batch_size=128,  # Large batches
        replay_buffer_size=10000,  # Huge buffer
        learning_rate=0.001,
        temperature_threshold=15,  # Long exploration
        device=device
    )

    print("CPU-Optimized Strategy:", flush=True)
    print("- Pure policy self-play (minimal MCTS overhead)", flush=True)
    print("- 20 games per iteration for rich training data", flush=True)
    print("- 5 training epochs per iteration", flush=True)
    print("- Evaluate every 50 iterations", flush=True)
    print("- CONTINUOUS TRAINING until 70%+ win rate!\n", flush=True)

    iteration = 0
    best_win_rate = 0.0

    while True:  # Train forever until we succeed!
        iteration += 1

        if iteration % 10 == 1 or iteration <= 5:
            print(f"\n{'='*70}", flush=True)
            print(f"ITERATION {iteration}", flush=True)
            print(f"{'='*70}", flush=True)
        elif iteration % 10 == 0:
            print(f"Iteration {iteration}...", flush=True)

        # Fast self-play
        trainer.run_self_play()

        # Train
        trainer.train()

        # Evaluate every 50 iterations
        if iteration % 50 == 0:
            print(f"\n{'='*70}", flush=True)
            print(f"EVALUATION AT ITERATION {iteration}", flush=True)
            print(f"{'='*70}", flush=True)

            # Quick evaluation with 10 games each
            results = trainer.evaluate(num_games=10)

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)

            print(f"\nResults (iteration {iteration}):", flush=True)
            print(f"  vs Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  vs Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  vs Smart:   {smart_wr*100:5.1f}%", flush=True)

            avg_wr = (random_wr + greedy_wr + smart_wr) / 3
            print(f"  Average:    {avg_wr*100:5.1f}%", flush=True)

            if avg_wr > best_win_rate:
                best_win_rate = avg_wr
                # Save best model
                checkpoint_path = f"boop_best_iter{iteration}_wr{int(avg_wr*100)}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"  NEW BEST! Saved: {checkpoint_path}", flush=True)

            # Check for success
            if smart_wr >= 0.70 and greedy_wr >= 0.70:
                print(f"\n{'='*70}", flush=True)
                print("SUCCESS! 70%+ WIN RATE ACHIEVED!", flush=True)
                print(f"{'='*70}", flush=True)

                # Final comprehensive evaluation
                print("\nRunning final evaluation with 30 games each...", flush=True)
                final_results = trainer.evaluate(num_games=30)

                print(f"\nFINAL RESULTS:", flush=True)
                print(f"  vs Random:  {final_results.get('Random', 0)*100:.1f}%", flush=True)
                print(f"  vs Greedy:  {final_results.get('Greedy', 0)*100:.1f}%", flush=True)
                print(f"  vs Smart:   {final_results.get('Smart', 0)*100:.1f}%", flush=True)

                final_path = "boop_alphazero_VICTORY.pt"
                trainer.neural_net.save(final_path)
                print(f"\nVictory model saved: {final_path}", flush=True)
                break

        # Save checkpoints periodically
        elif iteration % 100 == 0:
            checkpoint_path = f"boop_continuous_iter{iteration}.pt"
            trainer.save_checkpoint(checkpoint_path)
            print(f"Checkpoint saved: {checkpoint_path}", flush=True)

        # Update iteration counter
        trainer.iteration = iteration

    print(f"\n{'='*70}", flush=True)
    print(f"TRAINING COMPLETE AFTER {iteration} ITERATIONS", flush=True)
    print(f"{'='*70}", flush=True)

    return trainer

if __name__ == "__main__":
    try:
        trainer = train_continuous()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user", flush=True)
        print("Saving current model...", flush=True)
        trainer.neural_net.save("boop_interrupted.pt")
        print("Model saved to boop_interrupted.pt", flush=True)
