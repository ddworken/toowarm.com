"""
Ultra-Fast AlphaZero Training for BOOP - Minimal MCTS for quick demonstration
"""

import os
import time
import torch
import torch.nn.functional as F

from boop_alphazero_train import AlphaZeroTrainer

def main():
    """Ultra-fast training with minimal MCTS simulations"""
    print("="*70)
    print("ULTRA-FAST ALPHAZERO TRAINING FOR BOOP")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Create trainer with minimal simulations for ultra-fast training
    trainer = AlphaZeroTrainer(
        num_simulations=10,  # Minimal simulations for speed
        num_self_play_games=5,  # Few games for fast iterations
        num_training_epochs=3,
        batch_size=16,
        replay_buffer_size=1000,
        learning_rate=0.003,  # Higher LR for faster learning
        temperature_threshold=5,
        device=device
    )

    checkpoint_dir = "checkpoints_ultra_fast"
    os.makedirs(checkpoint_dir, exist_ok=True)

    print("\nOptimized for ultra-fast training:")
    print("- 10 MCTS simulations per move (minimal)")
    print("- 5 self-play games per iteration")
    print("- 3 training epochs")
    print("- Focus on rapid iteration and demonstration")
    print()

    # Training loop
    max_iterations = 50
    target_win_rate = 0.70

    for i in range(max_iterations):
        print(f"\nStarting iteration {trainer.iteration + 1}...")
        start_time = time.time()

        results = trainer.train_iteration()

        iteration_time = time.time() - start_time
        print(f"Iteration completed in {iteration_time:.1f}s")

        # Save checkpoint every 10 iterations
        if trainer.iteration % 10 == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_iter_{trainer.iteration}.pt")
            trainer.save_checkpoint(checkpoint_path)

        # Check if we're beating all strategies
        if trainer.iteration >= 5:
            recent_vs_smart = trainer.history['win_rate_vs_smart'][-3:]
            recent_vs_greedy = trainer.history['win_rate_vs_greedy'][-3:]
            recent_vs_random = trainer.history['win_rate_vs_random'][-3:]

            avg_vs_smart = sum(recent_vs_smart) / len(recent_vs_smart) if recent_vs_smart else 0
            avg_vs_greedy = sum(recent_vs_greedy) / len(recent_vs_greedy) if recent_vs_greedy else 0
            avg_vs_random = sum(recent_vs_random) / len(recent_vs_random) if recent_vs_random else 0

            print(f"\nRecent avg performance (last 3 iterations):")
            print(f"  vs Random:  {avg_vs_random*100:.1f}%")
            print(f"  vs Greedy:  {avg_vs_greedy*100:.1f}%")
            print(f"  vs Smart:   {avg_vs_smart*100:.1f}%")

            if avg_vs_smart >= target_win_rate and avg_vs_greedy >= target_win_rate:
                print(f"\n{'='*70}")
                print("SUCCESS! AlphaZero is consistently beating all strategies!")
                print(f"Win rate vs Smart: {avg_vs_smart*100:.1f}%")
                print(f"Win rate vs Greedy: {avg_vs_greedy*100:.1f}%")
                print(f"{'='*70}")
                break

    # Final comprehensive evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION (50 games each)")
    print(f"{'='*70}")
    final_results = trainer.evaluate(num_games=50)

    # Save final model
    final_model_path = "boop_alphazero_ultra_fast_final.pt"
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
