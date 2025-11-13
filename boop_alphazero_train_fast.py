"""
Fast AlphaZero Training for BOOP - Optimized for quick iterations
"""

import os
import time
import torch
import torch.nn.functional as F

from boop_alphazero_train import AlphaZeroTrainer

def main():
    """Fast training with reduced MCTS simulations for quicker iterations"""
    print("="*70)
    print("FAST ALPHAZERO TRAINING FOR BOOP")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Create trainer with reduced simulations for speed
    trainer = AlphaZeroTrainer(
        num_simulations=25,  # Reduced from 50 for 2x speedup
        num_self_play_games=10,  # Fewer games for faster iterations
        num_training_epochs=3,  # Fewer epochs
        batch_size=32,
        replay_buffer_size=2000,
        learning_rate=0.002,  # Slightly higher LR for faster learning
        temperature_threshold=8,
        device=device
    )

    checkpoint_dir = "checkpoints_fast"
    os.makedirs(checkpoint_dir, exist_ok=True)

    print("\nOptimized for fast training:")
    print("- 25 MCTS simulations per move (vs 50)")
    print("- 10 self-play games per iteration (vs 20)")
    print("- 3 training epochs (vs 5)")
    print()

    # Training loop - run until consistently beating strategies
    max_iterations = 30
    target_win_rate = 0.70

    for i in range(max_iterations):
        results = trainer.train_iteration()

        # Save checkpoint every 5 iterations
        if trainer.iteration % 5 == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_iter_{trainer.iteration}.pt")
            trainer.save_checkpoint(checkpoint_path)

        # Check if we're beating all strategies
        if trainer.iteration >= 10:
            recent_vs_smart = trainer.history['win_rate_vs_smart'][-5:]
            recent_vs_greedy = trainer.history['win_rate_vs_greedy'][-5:]
            recent_vs_random = trainer.history['win_rate_vs_random'][-5:]

            avg_vs_smart = sum(recent_vs_smart) / len(recent_vs_smart) if recent_vs_smart else 0
            avg_vs_greedy = sum(recent_vs_greedy) / len(recent_vs_greedy) if recent_vs_greedy else 0
            avg_vs_random = sum(recent_vs_random) / len(recent_vs_random) if recent_vs_random else 0

            print(f"\nRecent performance (last 5 iterations):")
            print(f"  vs Random:  {avg_vs_random*100:.1f}%")
            print(f"  vs Greedy:  {avg_vs_greedy*100:.1f}%")
            print(f"  vs Smart:   {avg_vs_smart*100:.1f}%")

            if avg_vs_smart >= target_win_rate and avg_vs_greedy >= target_win_rate:
                print(f"\n{'='*70}")
                print("SUCCESS! AlphaZero is consistently beating all strategies!")
                print(f"{'='*70}")
                break

    # Final comprehensive evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION (100 games each)")
    print(f"{'='*70}")
    final_results = trainer.evaluate(num_games=100)

    # Save final model
    final_model_path = "boop_alphazero_fast_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model saved to {final_model_path}")

    # Print training history summary
    print(f"\n{'='*70}")
    print("TRAINING SUMMARY")
    print(f"{'='*70}")
    print(f"Total iterations: {trainer.iteration}")
    print(f"Total games played: {trainer.iteration * trainer.num_self_play_games}")
    print(f"Replay buffer size: {len(trainer.replay_buffer)}")

    if trainer.history['win_rate_vs_smart']:
        print(f"\nWin rate progression:")
        print(f"  vs Random: {trainer.history['win_rate_vs_random'][0]*100:.1f}% → {trainer.history['win_rate_vs_random'][-1]*100:.1f}%")
        print(f"  vs Greedy: {trainer.history['win_rate_vs_greedy'][0]*100:.1f}% → {trainer.history['win_rate_vs_greedy'][-1]*100:.1f}%")
        print(f"  vs Smart:  {trainer.history['win_rate_vs_smart'][0]*100:.1f}% → {trainer.history['win_rate_vs_smart'][-1]*100:.1f}%")

    return trainer


if __name__ == "__main__":
    trainer = main()
