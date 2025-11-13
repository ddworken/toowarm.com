"""Quick test of optimized copy method"""

from boop_game import BoopGame, PieceType
import time

def test_copy_speed():
    """Test the speed of the optimized copy method"""
    game = BoopGame(verbose=False)

    # Make a few moves to have some state
    game.play_move(0, 0, PieceType.KITTEN)
    game.play_move(1, 1, PieceType.KITTEN)
    game.play_move(2, 2, PieceType.KITTEN)

    # Time many copies
    num_copies = 10000
    start = time.time()

    for _ in range(num_copies):
        copied_state = game.state.copy()

    elapsed = time.time() - start

    print(f"Copied {num_copies} states in {elapsed:.3f}s")
    print(f"Average: {elapsed/num_copies*1000:.3f}ms per copy")
    print(f"Rate: {num_copies/elapsed:.0f} copies/sec")

    # Verify correctness
    copied = game.state.copy()
    assert copied.current_player_idx == game.state.current_player_idx
    assert len(copied.players[0].pool) == len(game.state.players[0].pool)
    assert copied.board.grid[0][0].type == game.state.board.grid[0][0].type

    print("\nCopy correctness verified!")
    return True

if __name__ == "__main__":
    test_copy_speed()
