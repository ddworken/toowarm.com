"""
Monte Carlo Tree Search (MCTS) for BOOP with AlphaZero
"""

import numpy as np
import math
from copy import deepcopy
from boop_game import BoopGame, PieceType, Color


class MCTSNode:
    """Node in the Monte Carlo search tree"""

    def __init__(self, game_state, parent=None, prior=0.0, action=None):
        self.game_state = game_state
        self.parent = parent
        self.action = action  # Action that led to this node
        self.prior = prior  # Prior probability from neural network

        self.children = {}  # Dict of action -> MCTSNode
        self.visit_count = 0
        self.value_sum = 0.0
        self.is_expanded = False

    def value(self):
        """Average value of this node"""
        if self.visit_count == 0:
            return 0.0
        return self.value_sum / self.visit_count

    def is_leaf(self):
        """Check if this is a leaf node"""
        return not self.is_expanded

    def select_child(self, c_puct=1.5):
        """
        Select child with highest UCB score.

        UCB score = Q(s,a) + U(s,a)
        where Q(s,a) = value from neural network
              U(s,a) = c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))
        """
        best_score = -float('inf')
        best_action = None
        best_child = None

        for action, child in self.children.items():
            # Q value (from perspective of parent's player, so negate)
            q_value = -child.value()

            # U value (exploration bonus)
            u_value = c_puct * child.prior * math.sqrt(self.visit_count) / (1 + child.visit_count)

            ucb_score = q_value + u_value

            if ucb_score > best_score:
                best_score = ucb_score
                best_action = action
                best_child = child

        return best_action, best_child

    def expand(self, policy, valid_actions):
        """
        Expand this node by creating children for all valid actions.

        Args:
            policy: Policy distribution from neural network
            valid_actions: List of (row, col, piece_type) tuples
        """
        self.is_expanded = True

        for action in valid_actions:
            row, col, piece_type = action

            # Get prior from policy
            action_idx = row * 6 + col
            if piece_type == PieceType.CAT:
                action_idx += 36

            prior = policy[action_idx] if action_idx < len(policy) else 0.0

            # Create child node (game state will be created lazily)
            self.children[action] = MCTSNode(
                game_state=None,
                parent=self,
                prior=prior,
                action=action
            )

    def backup(self, value):
        """
        Backup value through the tree.

        Args:
            value: Value from perspective of the player who just moved
        """
        node = self
        while node is not None:
            node.visit_count += 1
            node.value_sum += value
            value = -value  # Flip value for opponent
            node = node.parent


class MCTS:
    """Monte Carlo Tree Search guided by neural network"""

    def __init__(self, neural_net, num_simulations=100, c_puct=1.5, temperature=1.0):
        """
        Initialize MCTS.

        Args:
            neural_net: BoopNetWrapper instance
            num_simulations: Number of MCTS simulations per move
            c_puct: Exploration constant
            temperature: Temperature for action selection (higher = more exploration)
        """
        self.neural_net = neural_net
        self.num_simulations = num_simulations
        self.c_puct = c_puct
        self.temperature = temperature

    def search(self, game_state, temperature=None):
        """
        Perform MCTS search from given game state.

        Returns:
            action_probs: numpy array of action probabilities
            root_value: Value of root node
        """
        if temperature is None:
            temperature = self.temperature

        # Create root node
        root = MCTSNode(game_state=deepcopy(game_state))

        # Run simulations
        for _ in range(self.num_simulations):
            node = root
            search_path = [node]

            # SELECT: Traverse tree until we reach a leaf
            while not node.is_leaf() and not self._is_terminal(node.game_state):
                action, child = node.select_child(self.c_puct)

                # Lazily create game state for child if needed
                if child.game_state is None:
                    child.game_state = deepcopy(node.game_state)
                    row, col, piece_type = action
                    game = BoopGame()
                    game.state = child.game_state
                    game.play_move(row, col, piece_type)

                node = child
                search_path.append(node)

            # Get value for leaf node
            if self._is_terminal(node.game_state):
                # Terminal node - get actual game result
                winner = node.game_state.winner
                if winner is None:
                    value = 0.0
                else:
                    # Value from perspective of player who just moved
                    current_player = node.game_state.get_current_player().color
                    value = 1.0 if winner == current_player else -1.0
            else:
                # Non-terminal leaf - EXPAND and EVALUATE with neural network
                policy, value = self.neural_net.predict(node.game_state)

                # Get valid actions
                valid_actions = self._get_valid_actions(node.game_state)

                if valid_actions:
                    # Expand node
                    node.expand(policy, valid_actions)
                else:
                    # No valid moves - game should be over
                    value = 0.0

            # BACKUP: Propagate value up the tree
            # Note: value is from perspective of current player at leaf
            # Need to negate for parent
            for i in range(len(search_path) - 1, -1, -1):
                search_node = search_path[i]
                search_node.visit_count += 1
                search_node.value_sum += value
                value = -value  # Flip for parent

        # Get action probabilities from visit counts
        action_probs = self._get_action_probs(root, temperature)

        return action_probs, root.value()

    def _is_terminal(self, game_state):
        """Check if game state is terminal"""
        # Check if there's a winner
        if game_state.winner is not None:
            return True

        # Check if current player has no pieces to play
        player = game_state.get_current_player()
        if not player.has_pieces_to_play():
            return True

        # Check if board is full
        if len(game_state.get_empty_positions()) == 0:
            return True

        return False

    def _get_valid_actions(self, game_state):
        """Get list of valid actions for game state"""
        valid_actions = []
        player = game_state.get_current_player()
        empty_positions = game_state.get_empty_positions()

        has_kitten = any(p.type == PieceType.KITTEN for p in player.pool)
        has_cat = any(p.type == PieceType.CAT for p in player.pool)

        for row, col in empty_positions:
            if has_kitten:
                valid_actions.append((row, col, PieceType.KITTEN))
            if has_cat:
                valid_actions.append((row, col, PieceType.CAT))

        return valid_actions

    def _get_action_probs(self, root, temperature):
        """
        Get action probability distribution from visit counts.

        Args:
            root: Root MCTSNode
            temperature: Temperature parameter
                - temperature = 0: choose most visited action deterministically
                - temperature = 1: sample proportionally to visit counts
                - temperature > 1: more random exploration
        """
        action_probs = np.zeros(108)

        total_visits = sum(child.visit_count for child in root.children.values())

        if total_visits == 0:
            # No visits - return uniform over valid actions
            valid_mask = self.neural_net.get_valid_actions_mask(root.game_state)
            if valid_mask.sum() > 0:
                action_probs = valid_mask / valid_mask.sum()
            return action_probs

        for action, child in root.children.items():
            row, col, piece_type = action
            action_idx = self.neural_net.encode_action(row, col, piece_type)

            if temperature == 0:
                # Greedy - choose most visited
                visit_counts = [c.visit_count for c in root.children.values()]
                max_visits = max(visit_counts)
                if child.visit_count == max_visits:
                    action_probs[action_idx] = 1.0 / visit_counts.count(max_visits)
            else:
                # Proportional to visit count with temperature
                action_probs[action_idx] = child.visit_count

        if temperature != 0 and action_probs.sum() > 0:
            # Apply temperature
            if temperature != 1.0:
                action_probs = np.power(action_probs, 1.0 / temperature)

            # Normalize
            action_probs = action_probs / action_probs.sum()

        return action_probs

    def get_best_action(self, game_state, return_probs=False, temperature=None):
        """
        Get best action for game state.

        Args:
            game_state: Current game state
            return_probs: If True, also return action probabilities
            temperature: Temperature for action selection

        Returns:
            action: (row, col, piece_type) tuple
            probs: (optional) Action probability distribution
        """
        action_probs, value = self.search(game_state, temperature)

        # Choose action based on probabilities
        if temperature == 0:
            action_idx = np.argmax(action_probs)
        else:
            action_idx = np.random.choice(len(action_probs), p=action_probs)

        # Decode action
        action = self.neural_net.decode_action(action_idx)

        if action is None:
            # Fallback: choose random valid action
            valid_actions = self._get_valid_actions(game_state)
            if valid_actions:
                action = valid_actions[0]
            else:
                raise ValueError("No valid actions available")

        if return_probs:
            return action, action_probs
        return action


def test_mcts():
    """Test MCTS implementation"""
    print("Testing MCTS...")

    from boop_game import BoopGame
    from boop_alphazero_network import BoopNetWrapper

    # Create game and network
    game = BoopGame()
    net = BoopNetWrapper()

    # Create MCTS with few simulations for testing
    mcts = MCTS(net, num_simulations=50, temperature=1.0)

    # Get best action
    action, probs = mcts.get_best_action(game.state, return_probs=True, temperature=1.0)

    print(f"Best action: {action}")
    print(f"Action probability distribution stats:")
    print(f"  Sum: {probs.sum():.4f}")
    print(f"  Max: {probs.max():.4f}")
    print(f"  Non-zero actions: {(probs > 0).sum()}")

    # Test a few moves
    for i in range(3):
        action = mcts.get_best_action(game.state, temperature=1.0)
        print(f"\nMove {i+1}: {action}")

        success = game.play_move(*action)
        if not success:
            print(f"  Invalid move!")
            break

        if game.is_game_over():
            print(f"  Game over!")
            break

    print("\nMCTS test passed!")


if __name__ == "__main__":
    test_mcts()
