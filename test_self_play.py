"""Test self-play to see where it hangs"""

from boop_alphazero_train import AlphaZeroTrainer
import time

print("Creating trainer...")
trainer = AlphaZeroTrainer(
    num_simulations=5,
    num_self_play_games=1,  # Just 1 game
    num_training_epochs=2,
    batch_size=8,
    replay_buffer_size=500,
    learning_rate=0.005,
    temperature_threshold=3,
    device='cpu'
)

print("Running single self-play game...")
start = time.time()

try:
    trainer.run_self_play()
    elapsed = time.time() - start
    print(f"Self-play completed in {elapsed:.2f}s")
    print(f"Collected {len(trainer.replay_buffer)} examples")
except Exception as e:
    elapsed = time.time() - start
    print(f"ERROR after {elapsed:.2f}s: {e}")
    import traceback
    traceback.print_exc()
