"""
AI Strategies for BOOP Game
"""

import random
from typing import Tuple, List, Optional
from abc import ABC, abstractmethod
from boop_game import BoopGame, GameState, PieceType, Color, Board, GraduationEngine, Piece


class Strategy(ABC):
    """Base class for AI strategies"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose a move given the current game state"""
        pass


class RandomStrategy(Strategy):
    """Plays completely random valid moves"""

    def __init__(self):
        super().__init__("Random")

    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose a random valid move"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            raise ValueError("No valid moves available")
        return random.choice(valid_moves)


class GreedyStrategy(Strategy):
    """
    Greedy/Tactical strategy:
    - Prioritizes winning moves (three cats in a row)
    - Tries to graduate kittens when possible
    - Prefers playing Cats over Kittens when available
    - Prefers center positions
    - Tries to block opponent winning moves
    """

    def __init__(self):
        super().__init__("Greedy")

    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose the best greedy move"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            raise ValueError("No valid moves available")

        # Score all moves
        best_score = -float('inf')
        best_moves = []

        for move in valid_moves:
            score = self._evaluate_move(game, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # Return random best move if there are ties
        return random.choice(best_moves)

    def _evaluate_move(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> float:
        """Evaluate a move and return a score"""
        row, col, piece_type = move

        # Simulate the move
        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()

        # Try the move
        test_game.play_move(row, col, piece_type)

        score = 0.0

        # Check if this move wins the game
        if test_game.state.winner == game.state.get_current_player().color:
            return 10000.0  # Winning move is best

        # Check if this move would let opponent win next turn
        if not test_game.is_game_over():
            opponent_color = test_game.state.get_current_player().color
            opponent_can_win = self._can_win_next_move(test_game)
            if opponent_can_win:
                score -= 5000.0  # Avoid moves that let opponent win

        # Prefer cats over kittens
        if piece_type == PieceType.CAT:
            score += 100.0

        # Prefer center positions (more control)
        center_distance = abs(row - 2.5) + abs(col - 2.5)
        score += (7 - center_distance) * 10

        # Check if move creates lines (for graduation)
        board = test_game.state.board
        player_color = game.state.get_current_player().color
        lines = GraduationEngine.find_lines_of_three(board, player_color)
        score += len(lines) * 200.0

        # Bonus for having more cats on board
        cat_count = 0
        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                piece = board.get_piece(r, c)
                if piece and piece.color == player_color and piece.type == PieceType.CAT:
                    cat_count += 1
        score += cat_count * 15.0

        return score

    def _can_win_next_move(self, game: BoopGame) -> bool:
        """Check if current player (opponent) can win on their next move"""
        valid_moves = game.get_valid_moves()

        for move in valid_moves:
            test_game = BoopGame(verbose=False)
            test_game.state = game.state.copy()
            test_game.play_move(*move)

            if test_game.state.winner == game.state.get_current_player().color:
                return True

        return False


class DefensiveStrategy(Strategy):
    """
    Defensive strategy:
    - Blocks opponent lines aggressively
    - Tries to push opponent pieces off the board
    - Builds up cats before playing them
    - Avoids positions where pieces can be easily booped off
    """

    def __init__(self):
        super().__init__("Defensive")

    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose the best defensive move"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            raise ValueError("No valid moves available")

        # Score all moves
        best_score = -float('inf')
        best_moves = []

        for move in valid_moves:
            score = self._evaluate_move(game, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves)

    def _evaluate_move(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> float:
        """Evaluate a move defensively"""
        row, col, piece_type = move

        # Simulate the move
        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()

        current_player_color = game.state.get_current_player().color
        opponent_color = game.state.get_opponent().color

        # Count opponent pieces before
        opponent_pieces_before = test_game.state.board.count_pieces_by_color(opponent_color)

        test_game.play_move(row, col, piece_type)

        score = 0.0

        # Check if this move wins
        if test_game.state.winner == current_player_color:
            return 10000.0

        # Check if opponent can win next
        if not test_game.is_game_over():
            if self._opponent_can_win(test_game):
                score -= 5000.0

        # Count opponent pieces after (did we boop any off?)
        opponent_pieces_after = test_game.state.board.count_pieces_by_color(opponent_color)
        pieces_booped_off = opponent_pieces_before - opponent_pieces_after
        score += pieces_booped_off * 300.0

        # Check if we disrupted opponent lines
        opponent_lines = GraduationEngine.find_lines_of_three(
            test_game.state.board,
            opponent_color
        )
        score -= len(opponent_lines) * 400.0  # Penalty for allowing opponent lines

        # Prefer positions away from edges (harder to boop off)
        edge_distance = min(row, col, Board.SIZE - 1 - row, Board.SIZE - 1 - col)
        score += edge_distance * 20.0

        # Prefer cats for defensive play
        if piece_type == PieceType.CAT:
            score += 150.0

        # Check if move blocks opponent potential lines
        blocking_score = self._evaluate_blocking(game.state.board, row, col, opponent_color)
        score += blocking_score * 100.0

        return score

    def _opponent_can_win(self, game: BoopGame) -> bool:
        """Check if opponent can win next move"""
        valid_moves = game.get_valid_moves()

        for move in valid_moves:
            test_game = BoopGame(verbose=False)
            test_game.state = game.state.copy()
            test_game.play_move(*move)

            if test_game.state.winner == game.state.get_current_player().color:
                return True

        return False

    def _evaluate_blocking(self, board: Board, row: int, col: int, opponent_color: Color) -> float:
        """Evaluate how well this position blocks opponent"""
        blocking_value = 0.0

        # Check all lines that could pass through this position
        directions = [
            [(0, -2), (0, -1), (0, 1), (0, 2)],  # Horizontal
            [(-2, 0), (-1, 0), (1, 0), (2, 0)],  # Vertical
            [(-2, -2), (-1, -1), (1, 1), (2, 2)],  # Diagonal \
            [(-2, 2), (-1, 1), (1, -1), (2, -2)],  # Diagonal /
        ]

        for direction_set in directions:
            opponent_neighbors = 0
            for dr, dc in direction_set:
                r, c = row + dr, col + dc
                if board.is_valid_position(r, c):
                    piece = board.get_piece(r, c)
                    if piece and piece.color == opponent_color:
                        opponent_neighbors += 1

            # More opponent neighbors = better blocking position
            blocking_value += opponent_neighbors

        return blocking_value


class AggressiveStrategy(Strategy):
    """
    Aggressive strategy:
    - Tries to build three cats in a row quickly
    - Graduates kittens as fast as possible
    - Takes risks for potential wins
    - Prefers offensive positions
    """

    def __init__(self):
        super().__init__("Aggressive")

    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose the most aggressive move"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            raise ValueError("No valid moves available")

        best_score = -float('inf')
        best_moves = []

        for move in valid_moves:
            score = self._evaluate_move(game, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves)

    def _evaluate_move(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> float:
        """Evaluate move aggressively"""
        row, col, piece_type = move

        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()

        current_player_color = game.state.get_current_player().color

        test_game.play_move(row, col, piece_type)

        score = 0.0

        # Winning move
        if test_game.state.winner == current_player_color:
            return 10000.0

        # Heavily favor cat placements
        if piece_type == PieceType.CAT:
            score += 200.0

        # Count our cats on board
        board = test_game.state.board
        our_cats = 0
        our_cat_positions = []

        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                piece = board.get_piece(r, c)
                if piece and piece.color == current_player_color:
                    if piece.type == PieceType.CAT:
                        our_cats += 1
                        our_cat_positions.append((r, c))

        # Bonus for having many cats
        score += our_cats * 100.0

        # Check for potential winning lines (two cats that could become three)
        potential_win_lines = self._count_potential_win_lines(board, current_player_color)
        score += potential_win_lines * 400.0

        # Favor lines of kittens (for graduation)
        lines = GraduationEngine.find_lines_of_three(board, current_player_color)
        score += len(lines) * 300.0

        # Prefer center and aggressive positions
        center_bonus = 0
        if 2 <= row <= 3 and 2 <= col <= 3:
            center_bonus = 50.0
        score += center_bonus

        return score

    def _count_potential_win_lines(self, board: Board, color: Color) -> int:
        """Count potential winning positions (two cats with room for third)"""
        count = 0

        # Check all possible three-in-a-row positions
        # Horizontal
        for row in range(Board.SIZE):
            for col in range(Board.SIZE - 2):
                positions = [(row, col), (row, col + 1), (row, col + 2)]
                if self._is_potential_win_line(board, positions, color):
                    count += 1

        # Vertical
        for row in range(Board.SIZE - 2):
            for col in range(Board.SIZE):
                positions = [(row, col), (row + 1, col), (row + 2, col)]
                if self._is_potential_win_line(board, positions, color):
                    count += 1

        # Diagonal \
        for row in range(Board.SIZE - 2):
            for col in range(Board.SIZE - 2):
                positions = [(row, col), (row + 1, col + 1), (row + 2, col + 2)]
                if self._is_potential_win_line(board, positions, color):
                    count += 1

        # Diagonal /
        for row in range(Board.SIZE - 2):
            for col in range(2, Board.SIZE):
                positions = [(row, col), (row + 1, col - 1), (row + 2, col - 2)]
                if self._is_potential_win_line(board, positions, color):
                    count += 1

        return count

    def _is_potential_win_line(self, board: Board, positions: List[Tuple[int, int]], color: Color) -> bool:
        """Check if positions could form a winning line (2 cats + 1 empty)"""
        pieces = [board.get_piece(r, c) for r, c in positions]

        cats = 0
        empty = 0
        wrong = 0

        for piece in pieces:
            if piece is None:
                empty += 1
            elif piece.color == color and piece.type == PieceType.CAT:
                cats += 1
            else:
                wrong += 1

        # Potential win: 2 cats and 1 empty (or 1 cat and 2 empty)
        return (cats == 2 and empty == 1) or (cats == 1 and empty == 2)


class SmartStrategy(Strategy):
    """
    Balanced smart strategy combining multiple heuristics:
    - Looks ahead for winning moves
    - Blocks opponent threats
    - Balances offense and defense
    - Manages piece types strategically
    """

    def __init__(self):
        super().__init__("Smart")

    def choose_move(self, game: BoopGame) -> Tuple[int, int, PieceType]:
        """Choose the smartest balanced move"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            raise ValueError("No valid moves available")

        # First check for immediate winning moves
        for move in valid_moves:
            if self._is_winning_move(game, move):
                return move

        # Then check for moves that block opponent from winning
        blocking_moves = []
        for move in valid_moves:
            if self._blocks_opponent_win(game, move):
                blocking_moves.append(move)

        if blocking_moves:
            # Evaluate blocking moves and pick best
            valid_moves = blocking_moves

        # Score remaining moves
        best_score = -float('inf')
        best_moves = []

        for move in valid_moves:
            score = self._evaluate_move(game, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves)

    def _is_winning_move(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> bool:
        """Check if move wins the game"""
        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()
        current_color = game.state.get_current_player().color

        test_game.play_move(*move)
        return test_game.state.winner == current_color

    def _blocks_opponent_win(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> bool:
        """Check if move blocks opponent from winning next turn"""
        # Simulate our move
        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()
        test_game.play_move(*move)

        if test_game.is_game_over():
            return False

        # Check if opponent can win after our move
        opponent_moves = test_game.get_valid_moves()
        for opp_move in opponent_moves:
            test_game2 = BoopGame(verbose=False)
            test_game2.state = test_game.state.copy()
            test_game2.play_move(*opp_move)

            if test_game2.state.winner == test_game.state.get_current_player().color:
                return False  # Opponent can still win

        return True

    def _evaluate_move(self, game: BoopGame, move: Tuple[int, int, PieceType]) -> float:
        """Evaluate move with balanced strategy"""
        row, col, piece_type = move

        test_game = BoopGame(verbose=False)
        test_game.state = game.state.copy()

        current_color = game.state.get_current_player().color
        opponent_color = game.state.get_opponent().color

        test_game.play_move(row, col, piece_type)

        score = 0.0

        # Evaluate board control
        board = test_game.state.board

        # Count our pieces and cats
        our_cats = 0
        our_kittens = 0
        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                piece = board.get_piece(r, c)
                if piece and piece.color == current_color:
                    if piece.type == PieceType.CAT:
                        our_cats += 1
                    else:
                        our_kittens += 1

        # Balanced cat/kitten ratio
        score += our_cats * 50.0

        # Graduation opportunities
        lines = GraduationEngine.find_lines_of_three(board, current_color)
        score += len(lines) * 250.0

        # Position evaluation
        edge_distance = min(row, col, Board.SIZE - 1 - row, Board.SIZE - 1 - col)
        center_distance = abs(row - 2.5) + abs(col - 2.5)

        score += edge_distance * 15.0  # Avoid edges
        score += (7 - center_distance) * 10.0  # Prefer center

        # Piece type preference based on game state
        if piece_type == PieceType.CAT:
            score += 80.0

        return score
