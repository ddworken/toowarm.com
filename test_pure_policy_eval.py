"""Test pure policy evaluation"""

from boop_alphazero_network import BoopNetWrapper
from boop_game import BoopGame, Color
from boop_strategies import RandomStrategy
import time

print("Creating untrained network...")
net = BoopNetWrapper(device='cpu')
opponent = RandomStrategy()

print("Playing 1 game with pure policy...")
game = BoopGame(verbose=False)
move_count = 0
max_moves = 100

start = time.time()

while not game.is_game_over() and move_count < max_moves:
    if game.state.current_player_idx == 0:
        # AlphaZero (pure policy)
        policy, _ = net.predict(game.state)
        action_idx = policy.argmax()
        action = net.decode_action(action_idx)

        if action is None:
            valid = game.get_valid_moves()
            if valid:
                action = valid[0]
            else:
                print(f"No valid moves at move {move_count}")
                break

        success = game.play_move(*action)
        if not success:
            print(f"Invalid move by AlphaZero at move {move_count}: {action}")
            break
    else:
        # Opponent
        action = opponent.choose_move(game)
        game.play_move(*action)

    move_count += 1
    if move_count % 10 == 0:
        print(f"  Move {move_count}...")

elapsed = time.time() - start

winner = game.get_winner()
print(f"\nGame completed in {elapsed:.2f}s ({move_count} moves)")
print(f"Winner: {winner}")
