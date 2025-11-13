#!/usr/bin/env python3
"""
AlphaZero Ultra-Fast Training - Maximum speed configuration
- Minimal MCTS (1 sim) for lightning-fast self-play
- Many iterations to compensate for low quality
- Final strong evaluation with 50 MCTS sims
"""

import sys
import torch
from boop_alphazero_train import AlphaZeroTrainer

def train_ultra_fast():
    """Ultra-fast training with volume over quality"""
    print("="*70, flush=True)
    print("ALPHAZERO ULTRA-FAST TRAINING", flush=True)
    print("="*70, flush=True)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n", flush=True)

    # Ultra-minimal MCTS for maximum speed
    trainer = AlphaZeroTrainer(
        num_simulations=1,           # MINIMAL - just 1 MCTS sim
        num_self_play_games=10,      # More games per iteration
        num_training_epochs=4,       # More epochs
        batch_size=64,               # Larger batches
        replay_buffer_size=5000,     # Much larger buffer
        learning_rate=0.001,         # Lower LR
        temperature_threshold=8,     # Longer exploration
        device=device
    )

    print("Ultra-Fast Configuration:", flush=True)
    print("- Self-play: 1 MCTS simulation (MAXIMUM SPEED)", flush=True)
    print("- 10 games per iteration (more data)", flush=True)
    print("- 4 training epochs (better learning)", flush=True)
    print("- Quick evaluation every 20 iterations", flush=True)
    print("- Target: 100 iterations to build strong model\n", flush=True)

    max_iterations = 100
    eval_frequency = 20  # Evaluate rarely

    for i in range(max_iterations):
        iteration_num = i + 1
        print(f"\n{'='*70}", flush=True)
        print(f"ITERATION {iteration_num}/{max_iterations}", flush=True)
        print(f"{'='*70}", flush=True)

        # Ultra-fast self-play
        print("Self-play...", flush=True)
        trainer.run_self_play()
        print(f"  Buffer: {len(trainer.replay_buffer)}", flush=True)

        # Train
        print("Training...", flush=True)
        trainer.train()

        # Quick evaluation
        if iteration_num % eval_frequency == 0 or iteration_num == 1:
            print(f"\n{'='*20} QUICK EVALUATION {'='*20}", flush=True)

            # Use same minimal MCTS for speed
            results = trainer.evaluate(num_games=8)  # Few games

            random_wr = results.get('Random', 0)
            greedy_wr = results.get('Greedy', 0)
            smart_wr = results.get('Smart', 0)

            print(f"\nResults (iteration {iteration_num}):", flush=True)
            print(f"  vs Random:  {random_wr*100:5.1f}%", flush=True)
            print(f"  vs Greedy:  {greedy_wr*100:5.1f}%", flush=True)
            print(f"  vs Smart:   {smart_wr*100:5.1f}%", flush=True)

            # Save checkpoint
            if iteration_num % 20 == 0:
                checkpoint_path = f"boop_alphazero_ultra_iter{iteration_num}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"Checkpoint: {checkpoint_path}", flush=True)
        else:
            trainer.iteration += 1

    # Final comprehensive evaluation with STRONG MCTS
    print(f"\n{'='*70}", flush=True)
    print("FINAL STRONG EVALUATION WITH 50 MCTS SIMS", flush=True)
    print(f"{'='*70}", flush=True)

    from boop_alphazero_strategy import AlphaZeroStrategy
    from boop_strategies import RandomStrategy, GreedyStrategy, SmartStrategy
    from boop_game import BoopGame, Color

    # Create strong evaluator with 50 sims
    strong_strategy = AlphaZeroStrategy(
        model_path=None,
        num_simulations=50,  # STRONG evaluation
        temperature=0.0,
        device=device
    )
    strong_strategy.neural_net.model = trainer.neural_net.model

    def evaluate_final(num_games=20):
        """Final strong evaluation"""
        results = {}
        strategies = {
            'Random': RandomStrategy(),
            'Greedy': GreedyStrategy(),
            'Smart': SmartStrategy()
        }

        for name, opponent in strategies.items():
            print(f"Playing vs {name}...", flush=True)
            wins = 0
            for game_num in range(num_games):
                game = BoopGame(verbose=False)
                as_player_0 = (game_num % 2 == 0)

                while not game.is_game_over():
                    if (as_player_0 and game.state.current_player_idx == 0) or \
                       (not as_player_0 and game.state.current_player_idx == 1):
                        action = strong_strategy.choose_move(game)
                        game.play_move(*action)
                    else:
                        action = opponent.choose_move(game)
                        game.play_move(*action)

                winner = game.get_winner()
                if winner:
                    if (as_player_0 and winner == Color.ORANGE) or \
                       (not as_player_0 and winner == Color.GRAY):
                        wins += 1

            results[name] = wins / num_games
            print(f"  {name}: {results[name]*100:.1f}% ({wins}/{num_games} wins)", flush=True)

        return results

    final_results = evaluate_final(20)

    print(f"\n{'='*70}", flush=True)
    print("TRAINING COMPLETE", flush=True)
    print(f"{'='*70}", flush=True)

    final_model_path = "boop_alphazero_ultra_final.pt"
    trainer.neural_net.save(final_model_path)
    print(f"\nFinal model: {final_model_path}", flush=True)

    print(f"\nFINAL PERFORMANCE (50 MCTS sims):", flush=True)
    print(f"  vs Random:  {final_results.get('Random', 0)*100:.1f}%", flush=True)
    print(f"  vs Greedy:  {final_results.get('Greedy', 0)*100:.1f}%", flush=True)
    print(f"  vs Smart:   {final_results.get('Smart', 0)*100:.1f}%", flush=True)

    if final_results.get('Smart', 0) >= 0.70 and final_results.get('Greedy', 0) >= 0.70:
        print(f"\n{'='*70}", flush=True)
        print("SUCCESS! AlphaZero beats all strategies!", flush=True)
        print(f"{'='*70}", flush=True)

    return trainer

if __name__ == "__main__":
    trainer = train_ultra_fast()
