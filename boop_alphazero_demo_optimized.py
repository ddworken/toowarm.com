"""
Optimized AlphaZero Demo - Fast training with strategic evaluation
"""

import torch
import torch.nn.functional as F
import numpy as np
from boop_alphazero_train import AlphaZeroTrainer

def optimized_demo():
    """Optimized demonstration focusing on training speed"""
    print("="*70)
    print("OPTIMIZED ALPHAZERO TRAINING")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n")

    # Ultra-minimal settings for maximum speed
    trainer = AlphaZeroTrainer(
        num_simulations=5,          # Minimal MCTS
        num_self_play_games=3,      # Just 3 games
        num_training_epochs=2,      # Minimal training
        batch_size=8,
        replay_buffer_size=500,
        learning_rate=0.005,
        temperature_threshold=3,
        device=device
    )

    print("Optimization Strategy:")
    print("- Self-play: 3 games with 5 MCTS sims (FAST)")
    print("- Training: 2 epochs per iteration")
    print("- Evaluation: Every 5 iterations with 10 games (not 20)")
    print("- Target: 30 iterations to show learning\n")

    # Quick training loop with sparse evaluation
    total_iterations = 30
    eval_frequency = 5  # Evaluate every N iterations

    for i in range(total_iterations):
        print(f"\n{'='*70}")
        print(f"ITERATION {i+1}/{total_iterations}")
        print(f"{'='*70}")

        # Self-play phase
        buffer_size_before = len(trainer.replay_buffer)
        trainer.run_self_play()
        new_examples = len(trainer.replay_buffer) - buffer_size_before
        print(f"Self-play: Added {new_examples} examples (buffer: {len(trainer.replay_buffer)})")

        # Training phase
        trainer.train()

        # Sparse evaluation - only every N iterations
        if (i + 1) % eval_frequency == 0 or i == 0 or i == total_iterations - 1:
            print(f"\n>>> EVALUATION (Iteration {i+1}) <<<")
            results = trainer.evaluate(num_games=10)  # Faster: 10 games instead of 20

            # Show current performance
            print(f"\nCurrent Performance:")
            print(f"  vs Random:  {results.get('Random', 0)*100:.1f}%")
            print(f"  vs Greedy:  {results.get('Greedy', 0)*100:.1f}%")
            print(f"  vs Smart:   {results.get('Smart', 0)*100:.1f}%")

            # Early stopping if doing really well
            if i >= 15:
                if results.get('Smart', 0) >= 0.70 and results.get('Greedy', 0) >= 0.70:
                    print(f"\n{'='*70}")
                    print("SUCCESS! AlphaZero is consistently beating all strategies!")
                    print(f"{'='*70}")
                    break
        else:
            # Skip evaluation for speed
            print(f"Skipping evaluation (will evaluate at iteration {((i+1)//eval_frequency + 1)*eval_frequency})")
            # Update iteration counter manually
            trainer.iteration += 1

    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")

    # Save the model
    model_path = "boop_alphazero_optimized.pt"
    trainer.neural_net.save(model_path)
    print(f"\nModel saved to {model_path}")

    # Final comprehensive evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION (30 games each)")
    print(f"{'='*70}")
    final_results = trainer.evaluate(num_games=30)

    # Print summary
    print(f"\n{'='*70}")
    print("TRAINING SUMMARY")
    print(f"{'='*70}")
    print(f"Total iterations: {trainer.iteration}")
    print(f"Total games played: {trainer.iteration * trainer.num_self_play_games}")
    print(f"Replay buffer size: {len(trainer.replay_buffer)}")

    if trainer.history['win_rate_vs_smart']:
        print(f"\nPerformance Improvement:")
        print(f"  vs Random: {trainer.history['win_rate_vs_random'][0]*100:.1f}% → {trainer.history['win_rate_vs_random'][-1]*100:.1f}%")
        print(f"  vs Greedy: {trainer.history['win_rate_vs_greedy'][0]*100:.1f}% → {trainer.history['win_rate_vs_greedy'][-1]*100:.1f}%")
        print(f"  vs Smart:  {trainer.history['win_rate_vs_smart'][0]*100:.1f}% → {trainer.history['win_rate_vs_smart'][-1]*100:.1f}%")

    return trainer

if __name__ == "__main__":
    trainer = optimized_demo()
