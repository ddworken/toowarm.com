"""
AlphaZero Strategy for BOOP - Can play against other strategies
"""

from boop_strategies import Strategy
from boop_alphazero_network import BoopNetWrapper
from boop_mcts import MCTS
from boop_game import PieceType


class AlphaZeroStrategy(Strategy):
    """
    AlphaZero-based strategy using neural network + MCTS
    """

    def __init__(self, model_path=None, num_simulations=25, temperature=0.0, device='cpu'):
        """
        Initialize AlphaZero strategy.

        Args:
            model_path: Path to trained model weights (None for untrained)
            num_simulations: Number of MCTS simulations per move
            temperature: Temperature for move selection (0 = greedy, 1 = stochastic)
            device: 'cpu' or 'cuda'
        """
        super().__init__("AlphaZero")

        self.neural_net = BoopNetWrapper(device=device)

        if model_path:
            try:
                self.neural_net.load(model_path)
                self.name = f"AlphaZero({num_simulations})"
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                self.name = f"AlphaZero-Untrained({num_simulations})"
        else:
            self.name = f"AlphaZero-Untrained({num_simulations})"

        self.mcts = MCTS(
            self.neural_net,
            num_simulations=num_simulations,
            c_puct=1.5,
            temperature=temperature
        )

    def choose_move(self, game):
        """
        Choose a move using MCTS + neural network.

        Args:
            game: BoopGame instance

        Returns:
            (row, col, piece_type) tuple
        """
        try:
            action = self.mcts.get_best_action(game.state, temperature=0.0)
            return action
        except Exception as e:
            # Fallback to random valid move if MCTS fails
            print(f"AlphaZero move selection failed: {e}, using fallback")
            valid_moves = game.get_valid_moves()
            if valid_moves:
                return valid_moves[0]
            raise ValueError("No valid moves available")


class AlphaZeroPurePolicy(Strategy):
    """
    Pure policy network strategy (no MCTS) - much faster but weaker
    """

    def __init__(self, model_path=None, device='cpu'):
        """
        Initialize pure policy strategy.

        Args:
            model_path: Path to trained model weights (None for untrained)
            device: 'cpu' or 'cuda'
        """
        super().__init__("AlphaZero-Policy")

        self.neural_net = BoopNetWrapper(device=device)

        if model_path:
            try:
                self.neural_net.load(model_path)
                self.name = "AlphaZero-Policy"
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                self.name = "AlphaZero-Policy-Untrained"
        else:
            self.name = "AlphaZero-Policy-Untrained"

    def choose_move(self, game):
        """
        Choose a move using only the policy network (no MCTS).

        Args:
            game: BoopGame instance

        Returns:
            (row, col, piece_type) tuple
        """
        try:
            # Get policy from neural network
            policy, value = self.neural_net.predict(game.state)

            # Choose action with highest probability
            action_idx = policy.argmax()
            action = self.neural_net.decode_action(action_idx)

            if action is None:
                # Fallback
                valid_moves = game.get_valid_moves()
                if valid_moves:
                    return valid_moves[0]
                raise ValueError("No valid moves available")

            return action
        except Exception as e:
            print(f"Policy move selection failed: {e}, using fallback")
            valid_moves = game.get_valid_moves()
            if valid_moves:
                return valid_moves[0]
            raise ValueError("No valid moves available")


def test_alphazero_strategy():
    """Test AlphaZero strategy against baseline"""
    from boop_game import BoopGame
    from boop_strategies import RandomStrategy, GreedyStrategy

    print("Testing AlphaZero Strategy...")

    # Create strategies
    alphazero = AlphaZeroStrategy(num_simulations=10)  # Fast for testing
    random_strat = RandomStrategy()

    # Play a test game
    game = BoopGame(verbose=False)

    strategies = [alphazero, random_strat]
    move_count = 0
    max_moves = 100

    print(f"\nPlaying: {strategies[0].name} vs {strategies[1].name}")

    while not game.is_game_over() and move_count < max_moves:
        current_strategy = strategies[game.state.current_player_idx]

        try:
            action = current_strategy.choose_move(game)
            success = game.play_move(*action)

            if not success:
                print(f"Invalid move by {current_strategy.name}")
                break

            move_count += 1

        except Exception as e:
            print(f"Error: {e}")
            break

    winner = game.get_winner()
    if winner:
        winner_name = strategies[0].name if winner == game.state.players[0].color else strategies[1].name
        print(f"Winner: {winner_name} in {move_count} moves")
    else:
        print(f"Draw after {move_count} moves")

    print("\nAlphaZero strategy test complete!")


def quick_tournament():
    """Quick tournament with AlphaZero"""
    from boop_game import BoopGame, Color
    from boop_strategies import RandomStrategy, GreedyStrategy, SmartStrategy

    print("\n" + "="*70)
    print("ALPHAZERO vs BASELINE STRATEGIES")
    print("="*70)

    # Create AlphaZero with minimal MCTS for speed
    alphazero = AlphaZeroStrategy(num_simulations=10)

    opponents = [
        RandomStrategy(),
        GreedyStrategy(),
    ]

    num_games = 10

    for opponent in opponents:
        print(f"\n{alphazero.name} vs {opponent.name} ({num_games} games)")

        wins = 0
        losses = 0
        draws = 0

        for game_num in range(num_games):
            game = BoopGame(verbose=False)

            # Alternate colors
            if game_num % 2 == 0:
                strategies = [alphazero, opponent]
            else:
                strategies = [opponent, alphazero]

            move_count = 0
            max_moves = 200

            while not game.is_game_over() and move_count < max_moves:
                current_strategy = strategies[game.state.current_player_idx]

                try:
                    action = current_strategy.choose_move(game)
                    game.play_move(*action)
                    move_count += 1
                except Exception as e:
                    print(f"Game {game_num+1} error: {e}")
                    break

            winner = game.get_winner()

            if winner is None:
                draws += 1
            else:
                alphazero_color = strategies[0].color if game_num % 2 == 0 else strategies[1].color
                # Need to check which strategy was which color
                if game_num % 2 == 0:
                    # AlphaZero was Orange
                    if winner == Color.ORANGE:
                        wins += 1
                    else:
                        losses += 1
                else:
                    # AlphaZero was Gray
                    if winner == Color.GRAY:
                        wins += 1
                    else:
                        losses += 1

        win_rate = wins / num_games
        print(f"  Results: {wins}-{losses}-{draws} (Win rate: {win_rate*100:.1f}%)")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_alphazero_strategy()
    # Uncomment to run tournament:
    # quick_tournament()
