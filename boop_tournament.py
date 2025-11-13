"""
Tournament System for BOOP AI Strategies
"""

import time
from typing import List, Dict, Tuple
from dataclasses import dataclass
from boop_game import BoopGame, Color
from boop_strategies import (
    Strategy, RandomStrategy, GreedyStrategy,
    DefensiveStrategy, AggressiveStrategy, SmartStrategy
)


@dataclass
class MatchResult:
    """Results of a single match"""
    player1_strategy: str
    player2_strategy: str
    winner: Color
    move_count: int
    duration: float


@dataclass
class StrategyStats:
    """Statistics for a strategy"""
    name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_moves: int = 0
    total_time: float = 0.0

    @property
    def games_played(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played

    @property
    def avg_moves(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.total_moves / self.games_played

    @property
    def avg_time(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.total_time / self.games_played


class Tournament:
    """Run tournaments between strategies"""

    def __init__(self, strategies: List[Strategy]):
        self.strategies = strategies
        self.results: List[MatchResult] = []
        self.stats: Dict[str, StrategyStats] = {
            s.name: StrategyStats(s.name) for s in strategies
        }

    def play_match(self, strategy1: Strategy, strategy2: Strategy, verbose: bool = False) -> MatchResult:
        """Play a single match between two strategies"""
        game = BoopGame(verbose=verbose)

        # strategy1 plays as Orange (player 0), strategy2 as Gray (player 1)
        strategies = [strategy1, strategy2]

        start_time = time.time()
        max_moves = 500  # Prevent infinite games

        while not game.is_game_over() and game.state.move_count < max_moves:
            current_strategy = strategies[game.state.current_player_idx]

            try:
                move = current_strategy.choose_move(game)
                success = game.play_move(*move)

                if not success:
                    if verbose:
                        print(f"Invalid move by {current_strategy.name}")
                    break

            except Exception as e:
                if verbose:
                    print(f"Error in {current_strategy.name}: {e}")
                break

        duration = time.time() - start_time

        # Determine winner
        winner = game.get_winner()
        if winner is None:
            # Game ended without winner (timeout or error)
            winner = Color.ORANGE  # Default for now

        result = MatchResult(
            player1_strategy=strategy1.name,
            player2_strategy=strategy2.name,
            winner=winner,
            move_count=game.state.move_count,
            duration=duration
        )

        return result

    def run_round_robin(self, games_per_matchup: int = 10, verbose: bool = False) -> None:
        """
        Run a round-robin tournament where each strategy plays against every other.
        Each matchup is played multiple times with alternating colors.
        """
        total_matches = len(self.strategies) * (len(self.strategies) - 1) * games_per_matchup // 2

        print(f"\n{'='*70}")
        print(f"Starting Round-Robin Tournament")
        print(f"Strategies: {', '.join(s.name for s in self.strategies)}")
        print(f"Games per matchup: {games_per_matchup}")
        print(f"Total matches: {total_matches}")
        print(f"{'='*70}\n")

        match_num = 0

        for i, strategy1 in enumerate(self.strategies):
            for j, strategy2 in enumerate(self.strategies):
                if i >= j:  # Skip self-play and duplicate matchups
                    continue

                print(f"Matchup: {strategy1.name} vs {strategy2.name}")

                for game_num in range(games_per_matchup):
                    match_num += 1

                    # Alternate which strategy plays first
                    if game_num % 2 == 0:
                        s1, s2 = strategy1, strategy2
                    else:
                        s1, s2 = strategy2, strategy1

                    result = self.play_match(s1, s2, verbose=verbose)
                    self.results.append(result)

                    # Update stats
                    if result.winner == Color.ORANGE:
                        winner_name = s1.name
                        loser_name = s2.name
                    else:
                        winner_name = s2.name
                        loser_name = s1.name

                    self.stats[winner_name].wins += 1
                    self.stats[loser_name].losses += 1

                    for name in [s1.name, s2.name]:
                        self.stats[name].total_moves += result.move_count
                        self.stats[name].total_time += result.duration

                    if not verbose:
                        print(f"  Game {game_num + 1}/{games_per_matchup}: "
                              f"{winner_name} wins in {result.move_count} moves")

                print()

        print(f"\n{'='*70}")
        print("Tournament Complete!")
        print(f"{'='*70}\n")

    def run_gauntlet(self, champion: Strategy, challengers: List[Strategy],
                     games_per_challenger: int = 20, verbose: bool = False) -> None:
        """
        Run a gauntlet where one strategy (champion) plays against all others.
        """
        print(f"\n{'='*70}")
        print(f"Gauntlet Tournament: {champion.name} vs All")
        print(f"Challengers: {', '.join(c.name for c in challengers)}")
        print(f"Games per challenger: {games_per_challenger}")
        print(f"{'='*70}\n")

        for challenger in challengers:
            if challenger.name == champion.name:
                continue

            print(f"{champion.name} vs {challenger.name}")

            for game_num in range(games_per_challenger):
                # Alternate colors
                if game_num % 2 == 0:
                    s1, s2 = champion, challenger
                else:
                    s1, s2 = challenger, champion

                result = self.play_match(s1, s2, verbose=verbose)
                self.results.append(result)

                # Update stats
                if result.winner == Color.ORANGE:
                    winner_name = s1.name
                    loser_name = s2.name
                else:
                    winner_name = s2.name
                    loser_name = s1.name

                self.stats[winner_name].wins += 1
                self.stats[loser_name].losses += 1

                for name in [s1.name, s2.name]:
                    self.stats[name].total_moves += result.move_count
                    self.stats[name].total_time += result.duration

                if not verbose:
                    print(f"  Game {game_num + 1}: {winner_name} wins "
                          f"in {result.move_count} moves")

            print()

        print(f"\n{'='*70}")
        print("Gauntlet Complete!")
        print(f"{'='*70}\n")

    def print_results(self) -> None:
        """Print tournament results and statistics"""
        print(f"\n{'='*70}")
        print("TOURNAMENT RESULTS")
        print(f"{'='*70}\n")

        # Sort strategies by win rate
        sorted_stats = sorted(
            self.stats.values(),
            key=lambda s: (s.win_rate, s.wins),
            reverse=True
        )

        print(f"{'Rank':<6} {'Strategy':<15} {'W':<5} {'L':<5} {'Win%':<8} "
              f"{'Avg Moves':<12} {'Avg Time (s)':<12}")
        print("-" * 70)

        for rank, stat in enumerate(sorted_stats, 1):
            print(f"{rank:<6} {stat.name:<15} {stat.wins:<5} {stat.losses:<5} "
                  f"{stat.win_rate*100:>6.1f}%  {stat.avg_moves:>10.1f}  "
                  f"{stat.avg_time:>10.3f}")

        print()

        # Print head-to-head records
        print(f"\n{'='*70}")
        print("HEAD-TO-HEAD RECORDS")
        print(f"{'='*70}\n")

        h2h = self._calculate_head_to_head()

        strategies_list = [s.name for s in self.strategies]
        print(f"{'vs':<15}", end="")
        for name in strategies_list:
            print(f"{name[:10]:<12}", end="")
        print()
        print("-" * 70)

        for s1 in strategies_list:
            print(f"{s1:<15}", end="")
            for s2 in strategies_list:
                if s1 == s2:
                    print(f"{'---':<12}", end="")
                else:
                    record = h2h.get((s1, s2), (0, 0))
                    print(f"{record[0]}-{record[1]:<9}", end="")
            print()

        print()

    def _calculate_head_to_head(self) -> Dict[Tuple[str, str], Tuple[int, int]]:
        """Calculate head-to-head records (wins, losses)"""
        h2h = {}

        for result in self.results:
            s1 = result.player1_strategy
            s2 = result.player2_strategy

            if result.winner == Color.ORANGE:
                winner, loser = s1, s2
            else:
                winner, loser = s2, s1

            # Update winner's record against loser
            if (winner, loser) not in h2h:
                h2h[(winner, loser)] = (0, 0)
            wins, losses = h2h[(winner, loser)]
            h2h[(winner, loser)] = (wins + 1, losses)

            # Update loser's record against winner
            if (loser, winner) not in h2h:
                h2h[(loser, winner)] = (0, 0)
            wins, losses = h2h[(loser, winner)]
            h2h[(loser, winner)] = (wins, losses + 1)

        return h2h


def main():
    """Run the tournament"""
    print("\n" + "="*70)
    print("BOOP GAME - AI STRATEGY TOURNAMENT")
    print("="*70)

    # Initialize all strategies
    strategies = [
        RandomStrategy(),
        GreedyStrategy(),
        DefensiveStrategy(),
        AggressiveStrategy(),
        SmartStrategy(),
    ]

    # Create tournament
    tournament = Tournament(strategies)

    # Run round-robin tournament
    tournament.run_round_robin(games_per_matchup=10, verbose=False)

    # Print results
    tournament.print_results()

    print("\n" + "="*70)
    print("Tournament finished!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
