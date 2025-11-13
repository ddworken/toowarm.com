"""
AlphaZero Training System for BOOP
Self-play → Training → Evaluation loop
"""

import os
import time
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
from copy import deepcopy

from boop_game import BoopGame, Color
from boop_alphazero_network import BoopNet, BoopNetWrapper
from boop_mcts import MCTS
from boop_strategies import RandomStrategy, GreedyStrategy, DefensiveStrategy, SmartStrategy


class AlphaZeroTrainer:
    """AlphaZero training system for BOOP"""

    def __init__(self,
                 num_simulations=100,
                 num_self_play_games=50,
                 num_training_epochs=10,
                 batch_size=64,
                 replay_buffer_size=10000,
                 learning_rate=0.001,
                 temperature_threshold=15,
                 c_puct=1.5,
                 device='cpu'):
        """
        Initialize AlphaZero trainer.

        Args:
            num_simulations: MCTS simulations per move
            num_self_play_games: Games to play per iteration
            num_training_epochs: Training epochs per iteration
            batch_size: Batch size for training
            replay_buffer_size: Maximum size of replay buffer
            learning_rate: Learning rate for optimizer
            temperature_threshold: Move number after which temperature = 0
            c_puct: Exploration constant for MCTS
            device: 'cpu' or 'cuda'
        """
        self.num_simulations = num_simulations
        self.num_self_play_games = num_self_play_games
        self.num_training_epochs = num_training_epochs
        self.batch_size = batch_size
        self.temperature_threshold = temperature_threshold
        self.c_puct = c_puct
        self.device = device

        # Neural network
        self.neural_net = BoopNetWrapper(device=device)

        # MCTS
        self.mcts = MCTS(
            self.neural_net,
            num_simulations=num_simulations,
            c_puct=c_puct,
            temperature=1.0
        )

        # Optimizer
        self.optimizer = optim.Adam(
            self.neural_net.model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4  # L2 regularization
        )

        # Replay buffer: stores (state, policy, value) tuples
        self.replay_buffer = deque(maxlen=replay_buffer_size)

        # Training history
        self.history = {
            'iteration': [],
            'policy_loss': [],
            'value_loss': [],
            'total_loss': [],
            'win_rate_vs_random': [],
            'win_rate_vs_greedy': [],
            'win_rate_vs_smart': [],
        }

        self.iteration = 0

    def self_play_game(self, temperature=1.0, verbose=False):
        """
        Play one self-play game and collect training data.

        Returns:
            examples: List of (state, policy, value) tuples
        """
        examples = []
        game = BoopGame(verbose=verbose)

        move_count = 0

        while not game.is_game_over():
            move_count += 1

            # Get current state
            state = deepcopy(game.state)

            # Determine temperature (high early, low later)
            temp = temperature if move_count < self.temperature_threshold else 0.0

            # Run MCTS to get improved policy
            action_probs, value = self.mcts.search(state, temperature=temp)

            # Store example (state, improved policy, None for value - will fill in later)
            examples.append((
                self.neural_net.encode_state(state),
                action_probs,
                None  # Will be filled with game outcome
            ))

            # Sample action from policy
            if temp == 0:
                action_idx = np.argmax(action_probs)
            else:
                action_idx = np.random.choice(len(action_probs), p=action_probs)

            # Decode and execute action
            action = self.neural_net.decode_action(action_idx)
            if action is None:
                if verbose:
                    print(f"Warning: Invalid action sampled, choosing random valid move")
                # Fallback
                valid_moves = game.get_valid_moves()
                if valid_moves:
                    action = valid_moves[0]
                else:
                    break

            success = game.play_move(*action)
            if not success:
                if verbose:
                    print(f"Warning: Move failed: {action}")
                break

        # Assign values based on game outcome
        winner = game.get_winner()
        if winner is None:
            outcome = 0.0  # Draw
        else:
            outcome = 1.0  # Will flip for losing player

        # Fill in values from perspective of each player
        for i, (state, policy, _) in enumerate(examples):
            # Determine which player made this move
            player_idx = i % 2

            # Value from this player's perspective
            if winner is None:
                value = 0.0
            elif player_idx == 0:
                # Player 0 (Orange)
                value = 1.0 if winner == Color.ORANGE else -1.0
            else:
                # Player 1 (Gray)
                value = 1.0 if winner == Color.GRAY else -1.0

            examples[i] = (state, policy, value)

        return examples

    def run_self_play(self, num_games=None, verbose=False):
        """
        Run multiple self-play games and add to replay buffer.

        Args:
            num_games: Number of games to play (default: self.num_self_play_games)
            verbose: Print game details
        """
        if num_games is None:
            num_games = self.num_self_play_games

        print(f"\nRunning {num_games} self-play games...")
        start_time = time.time()

        total_examples = 0

        for game_num in range(num_games):
            examples = self.self_play_game(verbose=verbose)
            total_examples += len(examples)

            # Add to replay buffer
            self.replay_buffer.extend(examples)

            if (game_num + 1) % 10 == 0:
                elapsed = time.time() - start_time
                games_per_sec = (game_num + 1) / elapsed
                print(f"  Played {game_num + 1}/{num_games} games "
                      f"({games_per_sec:.1f} games/sec, "
                      f"{total_examples} examples collected)")

        elapsed = time.time() - start_time
        print(f"Self-play complete: {num_games} games, {total_examples} examples "
              f"in {elapsed:.1f}s ({num_games/elapsed:.2f} games/sec)")
        print(f"Replay buffer size: {len(self.replay_buffer)}")

    def train(self, num_epochs=None):
        """
        Train neural network on replay buffer.

        Args:
            num_epochs: Number of training epochs (default: self.num_training_epochs)
        """
        if num_epochs is None:
            num_epochs = self.num_training_epochs

        if len(self.replay_buffer) < self.batch_size:
            print(f"Not enough data in replay buffer ({len(self.replay_buffer)} < {self.batch_size})")
            return

        print(f"\nTraining for {num_epochs} epochs...")
        self.neural_net.train_mode()

        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_loss = 0.0
        num_batches = 0

        for epoch in range(num_epochs):
            # Sample batches
            indices = np.random.choice(len(self.replay_buffer), size=len(self.replay_buffer), replace=False)

            epoch_policy_loss = 0.0
            epoch_value_loss = 0.0
            epoch_total_loss = 0.0
            epoch_batches = 0

            for i in range(0, len(indices), self.batch_size):
                batch_indices = indices[i:i + self.batch_size]

                # Prepare batch
                states = []
                target_policies = []
                target_values = []

                for idx in batch_indices:
                    state, policy, value = self.replay_buffer[idx]
                    states.append(state)
                    target_policies.append(policy)
                    target_values.append([value])

                # Convert to tensors
                states = torch.FloatTensor(np.array(states)).to(self.device)
                target_policies = torch.FloatTensor(np.array(target_policies)).to(self.device)
                target_values = torch.FloatTensor(np.array(target_values)).to(self.device)

                # Forward pass
                self.optimizer.zero_grad()
                policy_logits, values = self.neural_net.model(states)

                # Compute losses
                policy_loss = -torch.sum(target_policies * F.log_softmax(policy_logits, dim=1)) / target_policies.size(0)
                value_loss = torch.mean((values - target_values) ** 2)
                loss = policy_loss + value_loss

                # Backward pass
                loss.backward()
                self.optimizer.step()

                # Track losses
                epoch_policy_loss += policy_loss.item()
                epoch_value_loss += value_loss.item()
                epoch_total_loss += loss.item()
                epoch_batches += 1

            # Average losses for epoch
            avg_policy_loss = epoch_policy_loss / epoch_batches
            avg_value_loss = epoch_value_loss / epoch_batches
            avg_total_loss = epoch_total_loss / epoch_batches

            total_policy_loss += epoch_policy_loss
            total_value_loss += epoch_value_loss
            total_loss += epoch_total_loss
            num_batches += epoch_batches

            if (epoch + 1) % 5 == 0 or epoch == num_epochs - 1:
                print(f"  Epoch {epoch+1}/{num_epochs}: "
                      f"Loss={avg_total_loss:.4f} "
                      f"(Policy={avg_policy_loss:.4f}, Value={avg_value_loss:.4f})")

        # Record average losses
        avg_policy_loss = total_policy_loss / num_batches
        avg_value_loss = total_value_loss / num_batches
        avg_total_loss = total_loss / num_batches

        self.history['policy_loss'].append(avg_policy_loss)
        self.history['value_loss'].append(avg_value_loss)
        self.history['total_loss'].append(avg_total_loss)

        self.neural_net.eval_mode()

        print(f"Training complete: "
              f"Avg Loss={avg_total_loss:.4f} "
              f"(Policy={avg_policy_loss:.4f}, Value={avg_value_loss:.4f})")

    def evaluate(self, num_games=20):
        """
        Evaluate current model against baseline strategies.

        Args:
            num_games: Number of games to play against each strategy
        """
        print(f"\nEvaluating against baseline strategies ({num_games} games each)...")

        strategies = [
            ('Random', RandomStrategy()),
            ('Greedy', GreedyStrategy()),
            ('Smart', SmartStrategy()),
        ]

        results = {}

        for name, strategy in strategies:
            wins = 0
            losses = 0
            draws = 0

            for game_num in range(num_games):
                # Alternate colors
                if game_num % 2 == 0:
                    # AlphaZero plays as Orange (player 0)
                    winner = self._play_evaluation_game(strategy, as_player_0=True)
                    if winner == Color.ORANGE:
                        wins += 1
                    elif winner == Color.GRAY:
                        losses += 1
                    else:
                        draws += 1
                else:
                    # AlphaZero plays as Gray (player 1)
                    winner = self._play_evaluation_game(strategy, as_player_0=False)
                    if winner == Color.GRAY:
                        wins += 1
                    elif winner == Color.ORANGE:
                        losses += 1
                    else:
                        draws += 1

            win_rate = wins / num_games
            results[name] = win_rate

            print(f"  vs {name:10s}: {wins:2d}-{losses:2d}-{draws:2d} (Win rate: {win_rate*100:.1f}%)")

        # Record win rates
        self.history['win_rate_vs_random'].append(results.get('Random', 0.0))
        self.history['win_rate_vs_greedy'].append(results.get('Greedy', 0.0))
        self.history['win_rate_vs_smart'].append(results.get('Smart', 0.0))

        return results

    def _play_evaluation_game(self, opponent_strategy, as_player_0=True):
        """
        Play one evaluation game against an opponent.

        Args:
            opponent_strategy: Strategy instance to play against
            as_player_0: If True, AlphaZero plays as player 0 (Orange)

        Returns:
            winner: Color of winner or None for draw
        """
        game = BoopGame(verbose=False)

        while not game.is_game_over():
            current_player_idx = game.state.current_player_idx

            if (as_player_0 and current_player_idx == 0) or (not as_player_0 and current_player_idx == 1):
                # AlphaZero's turn
                action = self.mcts.get_best_action(game.state, temperature=0.0)  # Greedy for evaluation
            else:
                # Opponent's turn
                action = opponent_strategy.choose_move(game)

            success = game.play_move(*action)
            if not success:
                # Invalid move - opponent loses
                return Color.ORANGE if current_player_idx == 1 else Color.GRAY

        return game.get_winner()

    def train_iteration(self):
        """Run one complete training iteration"""
        self.iteration += 1
        print(f"\n{'='*70}")
        print(f"ITERATION {self.iteration}")
        print(f"{'='*70}")

        # Self-play
        self.run_self_play()

        # Train
        self.train()

        # Evaluate
        results = self.evaluate()

        # Record iteration
        self.history['iteration'].append(self.iteration)

        return results

    def save_checkpoint(self, filepath):
        """Save training checkpoint"""
        checkpoint = {
            'iteration': self.iteration,
            'model_state_dict': self.neural_net.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history,
            'replay_buffer': list(self.replay_buffer),
        }
        torch.save(checkpoint, filepath)
        print(f"Checkpoint saved to {filepath}")

    def load_checkpoint(self, filepath):
        """Load training checkpoint"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.iteration = checkpoint['iteration']
        self.neural_net.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        self.replay_buffer = deque(checkpoint['replay_buffer'], maxlen=self.replay_buffer.maxlen)
        print(f"Checkpoint loaded from {filepath} (iteration {self.iteration})")


# Import F for loss calculation
import torch.nn.functional as F


def main():
    """Main training loop"""
    print("="*70)
    print("ALPHAZERO TRAINING FOR BOOP")
    print("="*70)

    # Check for GPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Create trainer
    trainer = AlphaZeroTrainer(
        num_simulations=50,  # Start with fewer simulations for speed
        num_self_play_games=20,  # Fewer games initially
        num_training_epochs=5,
        batch_size=32,
        replay_buffer_size=5000,
        learning_rate=0.001,
        temperature_threshold=10,
        device=device
    )

    # Training loop
    target_iterations = 20  # Will run more if needed to beat all strategies
    checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)

    try:
        for i in range(target_iterations):
            results = trainer.train_iteration()

            # Save checkpoint
            checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_iter_{trainer.iteration}.pt")
            trainer.save_checkpoint(checkpoint_path)

            # Check if we're consistently beating all strategies
            if trainer.iteration >= 5:
                recent_vs_smart = trainer.history['win_rate_vs_smart'][-3:]
                recent_vs_greedy = trainer.history['win_rate_vs_greedy'][-3:]

                if len(recent_vs_smart) >= 3 and all(wr >= 0.70 for wr in recent_vs_smart) and \
                   len(recent_vs_greedy) >= 3 and all(wr >= 0.70 for wr in recent_vs_greedy):
                    print(f"\n{'='*70}")
                    print("SUCCESS! AlphaZero is consistently beating all strategies!")
                    print(f"{'='*70}")
                    break

    except KeyboardInterrupt:
        print("\nTraining interrupted by user")

    # Final evaluation
    print(f"\n{'='*70}")
    print("FINAL EVALUATION")
    print(f"{'='*70}")
    final_results = trainer.evaluate(num_games=50)

    # Save final model
    final_model_path = "boop_alphazero_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model saved to {final_model_path}")

    return trainer


if __name__ == "__main__":
    trainer = main()
