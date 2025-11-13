"""
AlphaZero Neural Network for BOOP
Combines policy and value prediction in a single network
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from boop_game import Board, PieceType, Color, GameState


class BoopNet(nn.Module):
    """
    Neural Network for BOOP following AlphaZero architecture.

    Input: 6x6x4 board representation
        - Channel 0: Current player's Kittens
        - Channel 1: Current player's Cats
        - Channel 2: Opponent's Kittens
        - Channel 3: Opponent's Cats

    Output:
        - Policy head: Probability distribution over all possible actions
        - Value head: Expected game outcome from current player's perspective (-1 to 1)
    """

    def __init__(self, board_size=6, num_actions=108, num_channels=128, num_res_blocks=5):
        super(BoopNet, self).__init__()

        self.board_size = board_size
        self.num_actions = num_actions  # 36 positions * 3 piece types (kitten/cat/pass)

        # Initial convolution
        self.conv_input = nn.Conv2d(4, num_channels, kernel_size=3, padding=1)
        self.bn_input = nn.BatchNorm2d(num_channels)

        # Residual blocks
        self.res_blocks = nn.ModuleList([
            ResidualBlock(num_channels) for _ in range(num_res_blocks)
        ])

        # Policy head
        self.policy_conv = nn.Conv2d(num_channels, 32, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(32)
        self.policy_fc = nn.Linear(32 * board_size * board_size, num_actions)

        # Value head
        self.value_conv = nn.Conv2d(num_channels, 32, kernel_size=1)
        self.value_bn = nn.BatchNorm2d(32)
        self.value_fc1 = nn.Linear(32 * board_size * board_size, 256)
        self.value_fc2 = nn.Linear(256, 1)

    def forward(self, x):
        """
        Forward pass through the network.

        Args:
            x: Tensor of shape (batch_size, 4, 6, 6)

        Returns:
            policy: Tensor of shape (batch_size, num_actions)
            value: Tensor of shape (batch_size, 1)
        """
        # Initial convolution
        x = F.relu(self.bn_input(self.conv_input(x)))

        # Residual blocks
        for block in self.res_blocks:
            x = block(x)

        # Policy head
        policy = F.relu(self.policy_bn(self.policy_conv(x)))
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)

        # Value head
        value = F.relu(self.value_bn(self.value_conv(x)))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value


class ResidualBlock(nn.Module):
    """Residual block with two convolutional layers and skip connection"""

    def __init__(self, num_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(num_channels)
        self.conv2 = nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(num_channels)

    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        x += residual
        x = F.relu(x)
        return x


class BoopNetWrapper:
    """Wrapper class for the neural network with game-specific encoding/decoding"""

    def __init__(self, model=None, device='cpu'):
        self.device = device
        if model is None:
            self.model = BoopNet().to(device)
        else:
            self.model = model.to(device)
        self.model.eval()

    def encode_state(self, game_state: GameState) -> np.ndarray:
        """
        Encode game state into neural network input format.

        Returns 6x6x4 numpy array:
            - Channel 0: Current player's Kittens
            - Channel 1: Current player's Cats
            - Channel 2: Opponent's Kittens
            - Channel 3: Opponent's Cats
        """
        board = np.zeros((4, 6, 6), dtype=np.float32)

        current_player = game_state.get_current_player()
        current_color = current_player.color

        for row in range(6):
            for col in range(6):
                piece = game_state.board.get_piece(row, col)
                if piece:
                    if piece.color == current_color:
                        # Current player's pieces
                        if piece.type == PieceType.KITTEN:
                            board[0, row, col] = 1.0
                        else:  # CAT
                            board[1, row, col] = 1.0
                    else:
                        # Opponent's pieces
                        if piece.type == PieceType.KITTEN:
                            board[2, row, col] = 1.0
                        else:  # CAT
                            board[3, row, col] = 1.0

        return board

    def decode_action(self, action_idx: int) -> tuple:
        """
        Decode action index into (row, col, piece_type).

        Action encoding:
            - Actions 0-35: Place Kitten at position
            - Actions 36-71: Place Cat at position
            - Actions 72-107: Reserved/pass
        """
        if action_idx < 36:
            # Kitten placement
            position = action_idx
            return (position // 6, position % 6, PieceType.KITTEN)
        elif action_idx < 72:
            # Cat placement
            position = action_idx - 36
            return (position // 6, position % 6, PieceType.CAT)
        else:
            # Pass/invalid
            return None

    def encode_action(self, row: int, col: int, piece_type: PieceType) -> int:
        """Encode (row, col, piece_type) into action index"""
        position = row * 6 + col
        if piece_type == PieceType.KITTEN:
            return position
        else:  # CAT
            return position + 36

    def get_valid_actions_mask(self, game_state: GameState) -> np.ndarray:
        """
        Get mask of valid actions (1 for valid, 0 for invalid).

        Returns numpy array of shape (108,)
        """
        mask = np.zeros(108, dtype=np.float32)
        valid_moves = game_state.get_valid_moves() if hasattr(game_state, 'get_valid_moves') else []

        # If no valid moves method, compute manually
        if not valid_moves:
            player = game_state.get_current_player()
            empty_positions = game_state.get_empty_positions()

            has_kitten = any(p.type == PieceType.KITTEN for p in player.pool)
            has_cat = any(p.type == PieceType.CAT for p in player.pool)

            for row, col in empty_positions:
                if has_kitten:
                    action_idx = self.encode_action(row, col, PieceType.KITTEN)
                    mask[action_idx] = 1.0
                if has_cat:
                    action_idx = self.encode_action(row, col, PieceType.CAT)
                    mask[action_idx] = 1.0
        else:
            for row, col, piece_type in valid_moves:
                action_idx = self.encode_action(row, col, piece_type)
                mask[action_idx] = 1.0

        # If no valid moves, something is wrong - allow pass
        if mask.sum() == 0:
            mask[72] = 1.0

        return mask

    def predict(self, game_state: GameState) -> tuple:
        """
        Predict policy and value for a game state.

        Returns:
            policy: numpy array of action probabilities (masked and normalized)
            value: float in range [-1, 1]
        """
        # Encode state
        board_tensor = torch.FloatTensor(self.encode_state(game_state)).unsqueeze(0).to(self.device)

        # Forward pass
        with torch.no_grad():
            policy_logits, value = self.model(board_tensor)

        # Convert to numpy
        policy_logits = policy_logits.cpu().numpy()[0]
        value = value.cpu().item()

        # Mask invalid actions and normalize
        valid_mask = self.get_valid_actions_mask(game_state)
        policy_logits = policy_logits - np.max(policy_logits)  # Numerical stability
        policy = np.exp(policy_logits) * valid_mask

        if policy.sum() > 0:
            policy = policy / policy.sum()
        else:
            # Fallback: uniform over valid actions
            policy = valid_mask / valid_mask.sum()

        return policy, value

    def train_mode(self):
        """Set model to training mode"""
        self.model.train()

    def eval_mode(self):
        """Set model to evaluation mode"""
        self.model.eval()

    def save(self, filepath):
        """Save model weights"""
        torch.save(self.model.state_dict(), filepath)

    def load(self, filepath):
        """Load model weights"""
        self.model.load_state_dict(torch.load(filepath, map_location=self.device))
        self.model.eval()


def test_network():
    """Test the neural network"""
    print("Testing BoopNet...")

    from boop_game import BoopGame

    # Create a game
    game = BoopGame()

    # Create network wrapper
    net = BoopNetWrapper()

    # Test prediction
    policy, value = net.predict(game.state)

    print(f"Policy shape: {policy.shape}")
    print(f"Policy sum: {policy.sum():.4f}")
    print(f"Value: {value:.4f}")
    print(f"Number of valid actions: {(policy > 0).sum()}")

    # Test encoding/decoding
    action_idx = np.argmax(policy)
    decoded = net.decode_action(action_idx)
    print(f"Best action: idx={action_idx}, decoded={decoded}")

    if decoded:
        row, col, piece_type = decoded
        encoded = net.encode_action(row, col, piece_type)
        print(f"Re-encoded: {encoded}")
        assert encoded == action_idx, "Encoding/decoding mismatch!"

    print("Network test passed!")


if __name__ == "__main__":
    test_network()
