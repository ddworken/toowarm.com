#!/usr/bin/env python3
"""
AlphaZero Training - Run to completion until consistently beating all strategies
"""

import sys
import torch
from boop_alphazero_train import AlphaZeroTrainer

def train_to_completion():
    """Train until consistently beating all baseline strategies"""
    print("="*70, flush=True)
    print("ALPHAZERO TRAINING TO COMPLETION", flush=True)
    print("="*70, flush=True)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}", flush=True)

    trainer = AlphaZeroTrainer(
        num_simulations=3,          # Fast MCTS
        num_self_play_games=5,       # Good data collection
        num_training_epochs=2,
        batch_size=16,
        replay_buffer_size=2000,    # Larger buffer
        learning_rate=0.003,
        temperature_threshold=3,
        device=device
    )

    print("\nConfiguration:", flush=True)
    print("- 3 MCTS simulations per move", flush=True)
    print("- 5 self-play games per iteration", flush=True)
    print("- Evaluate every 10 iterations", flush=True)
    print("- Target: 70%+ win rate vs all strategies\n", flush=True)

    max_iterations = 100
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
            print("Playing evaluation games (this takes ~1-2 minutes)...", flush=True)

            results = trainer.evaluate(num_games=10)

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)

            print(f"\nResults (iteration {iteration_num}):", flush=True)
            print(f"  vs Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  vs Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  vs Smart:   {smart_wr*100:5.1f}%", flush=True)

            # Check for success
            if smart_wr >= success_threshold and greedy_wr >= success_threshold:
                print(f"\n{'='*70}", flush=True)
                print("SUCCESS! AlphaZero consistently beats all strategies!", flush=True)
                print(f"{'='*70}", flush=True)
                print(f"Final performance:", flush=True)
                print(f"  vs Random:  {random_wr*100:.1f}%", flush=True)
                print(f"  vs Greedy:  {greedy_wr*100:.1f}%", flush=True)
                print(f"  vs Smart:   {smart_wr*100:.1f}%", flush=True)
                break

            # Save checkpoint
            if iteration_num % 20 == 0:
                checkpoint_path = f"boop_alphazero_checkpoint_iter{iteration_num}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"Checkpoint saved: {checkpoint_path}", flush=True)
        else:
            # Update iteration counter
            trainer.iteration += 1
            print(f"  (next evaluation at iteration {(iteration_num // eval_frequency + 1) * eval_frequency})", flush=True)

    # Final save
    print(f"\n{'='*70}", flush=True)
    print("TRAINING COMPLETE", flush=True)
    print(f"{'='*70}", flush=True)

    final_model_path = "boop_alphazero_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model saved: {final_model_path}", flush=True)

    # Final comprehensive evaluation
    if trainer.iteration >= 10:
        print("\nRunning final comprehensive evaluation (30 games each)...", flush=True)
        final_results = trainer.evaluate(num_games=30)

        print("\nFINAL PERFORMANCE:", flush=True)
        print(f"  vs Random:  {final_results.get('Random', 0)*100:.1f}%", flush=True)
        print(f"  vs Greedy:  {final_results.get('Greedy', 0)*100:.1f}%", flush=True)
        print(f"  vs Smart:   {final_results.get('Smart', 0)*100:.1f}%", flush=True)

    print(f"\nTotal iterations completed: {trainer.iteration}", flush=True)
    print(f"Total examples collected: {len(trainer.replay_buffer)}", flush=True)

    return trainer

if __name__ == "__main__":
    trainer = train_to_completion()
