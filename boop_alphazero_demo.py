"""
Minimal AlphaZero Demo - Train just enough to show it works
"""

import torch
import torch.nn.functional as F
import numpy as np
from boop_alphazero_train import AlphaZeroTrainer

def quick_demo():
    """Quick demonstration of AlphaZero beating baseline strategies"""
    print("="*70)
    print("ALPHAZERO QUICK DEMONSTRATION")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n")

    # Ultra-minimal settings for quick demonstration
    trainer = AlphaZeroTrainer(
        num_simulations=5,  # Absolutely minimal MCTS
        num_self_play_games=3,  # Just 3 games per iteration
        num_training_epochs=2,  # Minimal training
        batch_size=8,
        replay_buffer_size=500,
        learning_rate=0.005,
        temperature_threshold=3,
        device=device
    )

    print("Training Configuration:")
    print("- 5 MCTS simulations per move (minimal)")
    print("- 3 self-play games per iteration")
    print("- 2 training epochs")
    print("- Target: 20 iterations\n")

    # Quick training loop
    for i in range(20):
        print(f"\n{'='*70}")
        print(f"ITERATION {i+1}/20")
        print(f"{'='*70}")

        results = trainer.train_iteration()

        # Show progress
        if trainer.iteration >= 2:
            print(f"\nCurrent Performance:")
            print(f"  vs Random:  {results.get('Random', 0)*100:.1f}%")
            print(f"  vs Greedy:  {results.get('Greedy', 0)*100:.1f}%")
            print(f"  vs Smart:   {results.get('Smart', 0)*100:.1f}%")

    print(f"\n{'='*70}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*70}")

    # Save the model
    trainer.neural_net.save("boop_alphazero_demo.pt")
    print(f"\nModel saved to boop_alphazero_demo.pt")

    # Final evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION (30 games each)")
    print(f"{'='*70}")
    final_results = trainer.evaluate(num_games=30)

    return trainer

if __name__ == "__main__":
    trainer = quick_demo()
