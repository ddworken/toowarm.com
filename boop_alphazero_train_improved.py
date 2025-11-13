#!/usr/bin/env python3
"""
AlphaZero Training - Improved configuration for better generalization
"""

import sys
import torch
from boop_alphazero_train import AlphaZeroTrainer

def train_improved():
    """Train with better settings for generalization"""
    print("="*70, flush=True)
    print("ALPHAZERO TRAINING - IMPROVED CONFIGURATION", flush=True)
    print("="*70, flush=True)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n", flush=True)

    # Improved settings - more MCTS simulations for better play
    trainer = AlphaZeroTrainer(
        num_simulations=10,          # Increased from 3 to 10 for stronger play
        num_self_play_games=5,
        num_training_epochs=3,       # More epochs
        batch_size=32,               # Larger batch
        replay_buffer_size=3000,     # Larger buffer
        learning_rate=0.002,         # Lower learning rate
        temperature_threshold=5,     # Longer exploration phase
        device=device
    )

    print("Improved Configuration:", flush=True)
    print("- 10 MCTS simulations (was 3) - stronger play quality", flush=True)
    print("- 3 training epochs (was 2) - better learning", flush=True)
    print("- Batch size 32 (was 16) - more stable gradients", flush=True)
    print("- Learning rate 0.002 (was 0.003) - prevent overfitting", flush=True)
    print("- Temperature threshold 5 (was 3) - longer exploration\n", flush=True)

    max_iterations = 80
    eval_frequency = 10
    success_threshold = 0.70

    for i in range(max_iterations):
        iteration_num = i + 1
        print(f"\n{'='*70}", flush=True)
        print(f"ITERATION {iteration_num}/{max_iterations}", flush=True)
        print(f"{'='*70}", flush=True)

        # Self-play
        print("Self-play...", flush=True)
        trainer.run_self_play()
        print(f"  Buffer size: {len(trainer.replay_buffer)}", flush=True)

        # Train
        print("Training...", flush=True)
        trainer.train()

        # Evaluate periodically
        if iteration_num % eval_frequency == 0 or iteration_num == 1:
            print(f"\n{'='*20} EVALUATION {'='*20}", flush=True)
            print("Playing evaluation games...", flush=True)

            results = trainer.evaluate(num_games=15)  # More games for better stats

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)

            print(f"\nResults (iteration {iteration_num}):", flush=True)
            print(f"  vs Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  vs Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  vs Smart:   {smart_wr*100:5.1f}%", flush=True)

            # Check for success
            if iteration_num >= 20:  # Only check after 20 iterations
                if smart_wr >= success_threshold and greedy_wr >= success_threshold:
                    print(f"\n{'='*70}", flush=True)
                    print("SUCCESS! AlphaZero beats all strategies!", flush=True)
                    print(f"{'='*70}", flush=True)
                    break

            # Save checkpoint
            if iteration_num % 20 == 0:
                checkpoint_path = f"boop_alphazero_improved_iter{iteration_num}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"Checkpoint saved: {checkpoint_path}", flush=True)
        else:
            trainer.iteration += 1
            print(f"  (next evaluation at iteration {(iteration_num // eval_frequency + 1) * eval_frequency})", flush=True)

    # Final save
    print(f"\n{'='*70}", flush=True)
    print("TRAINING COMPLETE", flush=True)
    print(f"{'='*70}", flush=True)

    final_model_path = "boop_alphazero_improved_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model saved: {final_model_path}", flush=True)

    # Final evaluation
    if trainer.iteration >= 10:
        print("\nRunning final evaluation (30 games each)...", flush=True)
        final_results = trainer.evaluate(num_games=30)

        print("\nFINAL PERFORMANCE:", flush=True)
        print(f"  vs Random:  {final_results.get('Random', 0)*100:.1f}%", flush=True)
        print(f"  vs Greedy:  {final_results.get('Greedy', 0)*100:.1f}%", flush=True)
        print(f"  vs Smart:   {final_results.get('Smart', 0)*100:.1f}%", flush=True)

    print(f"\nTotal iterations: {trainer.iteration}", flush=True)
    print(f"Total examples: {len(trainer.replay_buffer)}", flush=True)

    return trainer

if __name__ == "__main__":
    trainer = train_improved()
