"""
Simplest Demo - Focus on training, minimal evaluation
"""

import torch
from boop_alphazero_train import AlphaZeroTrainer

def simple_demo():
    """Train with minimal evaluation"""
    print("="*70)
    print("SIMPLE ALPHAZERO TRAINING - Fast iterations!")
    print("="*70)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n")

    trainer = AlphaZeroTrainer(
        num_simulations=3,
        num_self_play_games=5,
        num_training_epochs=2,
        batch_size=16,
        replay_buffer_size=1000,
        learning_rate=0.005,
        temperature_threshold=3,
        device=device
    )

    print("Configuration:")
    print("- 3 MCTS simulations")
    print("- 5 self-play games per iteration")
    print("- Training only - evaluation every 10 iterations\n")

    # Training loop
    for i in range(50):
        print(f"\n--- Iteration {i+1}/50 ---")

        # Self-play
        trainer.run_self_play()
        print(f"Buffer: {len(trainer.replay_buffer)} examples")

        # Train
        losses = trainer.train()

        # Evaluate sparingly
        if (i + 1) % 10 == 0:
            print("\nEvaluating (this may take a minute)...")
            results = trainer.evaluate(num_games=10)
            print(f"vs Random: {results.get('Random', 0)*100:.1f}%")
            print(f"vs Greedy: {results.get('Greedy', 0)*100:.1f}%")
            print(f"vs Smart: {results.get('Smart', 0)*100:.1f}%")

            # Check for success
            if results.get('Smart', 0) >= 0.65:
                print(f"\n{'='*70}")
                print("SUCCESS! Beating Smart strategy!")
                print(f"{'='*70}")
                break
        else:
            # Update iteration manually
            trainer.iteration += 1

    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")

    # Save
    model_path = "boop_alphazero_simple.pt"
    trainer.neural_net.save(model_path)
    print(f"\nModel saved to {model_path}")

    print(f"\nTotal iterations: {trainer.iteration}")
    print(f"Total examples: {len(trainer.replay_buffer)}")

    return trainer

if __name__ == "__main__":
    trainer = simple_demo()
