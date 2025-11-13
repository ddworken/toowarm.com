"""
BOOP Game Engine - Complete Implementation
A two-player abstract strategy game where cats push each other around a bed.
"""

from enum import Enum
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from copy import deepcopy


class PieceType(Enum):
    KITTEN = "kitten"
    CAT = "cat"


class Color(Enum):
    ORANGE = "orange"
    GRAY = "gray"


@dataclass
class Piece:
    """Represents a game piece (Kitten or Cat)"""
    type: PieceType
    color: Color

    def __str__(self):
        prefix = 'O' if self.color == Color.ORANGE else 'G'
        suffix = 'k' if self.type == PieceType.KITTEN else 'C'
        return f"{prefix}{suffix}"

    def can_boop(self, other: 'Piece') -> bool:
        """Check if this piece can boop another piece"""
        if self.type == PieceType.KITTEN and other.type == PieceType.CAT:
            return False  # Kittens cannot boop Cats
        return True


class Board:
    """6x6 game board"""
    SIZE = 6

    def __init__(self):
        # Board[row][col] = Piece or None
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(self.SIZE)] for _ in range(self.SIZE)]

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within board bounds"""
        return 0 <= row < self.SIZE and 0 <= col < self.SIZE

    def is_empty(self, row: int, col: int) -> bool:
        """Check if a position is empty"""
        return self.is_valid_position(row, col) and self.grid[row][col] is None

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Get piece at position"""
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return None

    def place_piece(self, row: int, col: int, piece: Piece):
        """Place a piece on the board"""
        if not self.is_empty(row, col):
            raise ValueError(f"Position ({row}, {col}) is not empty")
        self.grid[row][col] = piece

    def remove_piece(self, row: int, col: int) -> Optional[Piece]:
        """Remove and return piece from position"""
        piece = self.grid[row][col]
        self.grid[row][col] = None
        return piece

    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """Move piece from one position to another"""
        piece = self.remove_piece(from_row, from_col)
        if piece and self.is_empty(to_row, to_col):
            self.place_piece(to_row, to_col, piece)
        return piece

    def get_all_adjacent(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all 8 adjacent positions (orthogonal and diagonal)"""
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        adjacent = []
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                adjacent.append((new_row, new_col))
        return adjacent

    def count_pieces_by_color(self, color: Color) -> int:
        """Count how many pieces of a color are on the board"""
        count = 0
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                piece = self.grid[row][col]
                if piece and piece.color == color:
                    count += 1
        return count

    def __str__(self):
        """String representation of the board"""
        lines = ["  " + " ".join(str(i) for i in range(self.SIZE))]
        for row in range(self.SIZE):
            row_str = f"{row} "
            for col in range(self.SIZE):
                piece = self.grid[row][col]
                if piece:
                    row_str += str(piece) + " "
                else:
                    row_str += ".  "
            lines.append(row_str)
        return "\n".join(lines)


@dataclass
class Player:
    """Represents a player"""
    color: Color
    pool: List[Piece]  # Available pieces to play
    reserve: List[Piece]  # Cats waiting to be graduated

    def __init__(self, color: Color):
        self.color = color
        # Start with 8 Kittens in pool
        self.pool = [Piece(PieceType.KITTEN, color) for _ in range(8)]
        # Start with 8 Cats in reserve
        self.reserve = [Piece(PieceType.CAT, color) for _ in range(8)]

    def has_pieces_to_play(self) -> bool:
        """Check if player has any pieces left to play"""
        return len(self.pool) > 0

    def get_piece_from_pool(self, piece_type: PieceType) -> Optional[Piece]:
        """Get a piece of the specified type from pool"""
        for i, piece in enumerate(self.pool):
            if piece.type == piece_type:
                return self.pool.pop(i)
        return None

    def return_to_pool(self, piece: Piece):
        """Return a piece to the pool"""
        self.pool.append(piece)

    def graduate_kittens(self, count: int = 3):
        """Graduate kittens: remove from game, move cats from reserve to pool"""
        if len(self.reserve) >= count:
            for _ in range(count):
                cat = self.reserve.pop()
                self.pool.append(cat)


class GameState:
    """Represents the complete game state"""

    def __init__(self):
        self.board = Board()
        self.players = [Player(Color.ORANGE), Player(Color.GRAY)]
        self.current_player_idx = 0
        self.winner: Optional[Color] = None
        self.move_count = 0

    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_player_idx]

    def get_opponent(self) -> Player:
        """Get the opponent player"""
        return self.players[1 - self.current_player_idx]

    def switch_player(self):
        """Switch to the other player"""
        self.current_player_idx = 1 - self.current_player_idx

    def get_empty_positions(self) -> List[Tuple[int, int]]:
        """Get all empty positions on the board"""
        empty = []
        for row in range(Board.SIZE):
            for col in range(Board.SIZE):
                if self.board.is_empty(row, col):
                    empty.append((row, col))
        return empty

    def copy(self) -> 'GameState':
        """Create a deep copy of the game state"""
        return deepcopy(self)


class BoopEngine:
    """Handles the booping (pushing) mechanics"""

    @staticmethod
    def calculate_push_direction(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate the direction vector for pushing away from placed piece"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        dr = to_row - from_row
        dc = to_col - from_col
        # Normalize to -1, 0, or 1
        dr = 0 if dr == 0 else (1 if dr > 0 else -1)
        dc = 0 if dc == 0 else (1 if dc > 0 else -1)
        return (dr, dc)

    @staticmethod
    def is_blocked_by_line_of_two(board: Board, pos: Tuple[int, int], push_dir: Tuple[int, int]) -> bool:
        """Check if piece is blocked from being pushed due to line-of-two rule"""
        row, col = pos
        dr, dc = push_dir
        # Check if there's another piece behind in the push direction
        behind_row = row + dr
        behind_col = col + dc

        if board.is_valid_position(behind_row, behind_col):
            behind_piece = board.get_piece(behind_row, behind_col)
            if behind_piece is not None:
                return True  # Blocked by line of two or more

        return False

    @staticmethod
    def resolve_boop(game_state: GameState, placed_pos: Tuple[int, int]) -> List[Piece]:
        """
        Resolve all booping from a newly placed piece.
        Returns list of pieces that were pushed off the board.
        """
        board = game_state.board
        placed_row, placed_col = placed_pos
        placed_piece = board.get_piece(placed_row, placed_col)

        if not placed_piece:
            return []

        booped_off = []
        adjacent_positions = board.get_all_adjacent(placed_row, placed_col)

        for adj_row, adj_col in adjacent_positions:
            target_piece = board.get_piece(adj_row, adj_col)

            if target_piece is None:
                continue

            # Check if placed piece can boop the target
            if not placed_piece.can_boop(target_piece):
                continue

            # Calculate push direction
            push_dir = BoopEngine.calculate_push_direction(
                (placed_row, placed_col),
                (adj_row, adj_col)
            )

            # Check for line-of-two blocking
            if BoopEngine.is_blocked_by_line_of_two(board, (adj_row, adj_col), push_dir):
                continue

            # Calculate destination
            dest_row = adj_row + push_dir[0]
            dest_col = adj_col + push_dir[1]

            # Execute the boop
            if not board.is_valid_position(dest_row, dest_col):
                # Pushed off the board
                piece = board.remove_piece(adj_row, adj_col)
                booped_off.append(piece)
            elif board.is_empty(dest_row, dest_col):
                # Move to empty destination
                board.move_piece(adj_row, adj_col, dest_row, dest_col)
            # else: destination occupied, piece doesn't move

        return booped_off


class GraduationEngine:
    """Handles kitten graduation mechanics"""

    @staticmethod
    def find_lines_of_three(board: Board, color: Color) -> List[List[Tuple[int, int]]]:
        """Find all lines of three pieces of the same color"""
        lines = []

        # Check horizontal lines
        for row in range(Board.SIZE):
            for col in range(Board.SIZE - 2):
                line = [(row, col), (row, col + 1), (row, col + 2)]
                if GraduationEngine._is_valid_line(board, line, color):
                    lines.append(line)

        # Check vertical lines
        for row in range(Board.SIZE - 2):
            for col in range(Board.SIZE):
                line = [(row, col), (row + 1, col), (row + 2, col)]
                if GraduationEngine._is_valid_line(board, line, color):
                    lines.append(line)

        # Check diagonal lines (top-left to bottom-right)
        for row in range(Board.SIZE - 2):
            for col in range(Board.SIZE - 2):
                line = [(row, col), (row + 1, col + 1), (row + 2, col + 2)]
                if GraduationEngine._is_valid_line(board, line, color):
                    lines.append(line)

        # Check diagonal lines (top-right to bottom-left)
        for row in range(Board.SIZE - 2):
            for col in range(2, Board.SIZE):
                line = [(row, col), (row + 1, col - 1), (row + 2, col - 2)]
                if GraduationEngine._is_valid_line(board, line, color):
                    lines.append(line)

        return lines

    @staticmethod
    def _is_valid_line(board: Board, positions: List[Tuple[int, int]], color: Color) -> bool:
        """Check if positions form a valid line for the color"""
        pieces = [board.get_piece(row, col) for row, col in positions]

        # All positions must have pieces of the correct color
        if any(p is None or p.color != color for p in pieces):
            return False

        return True

    @staticmethod
    def _line_has_kitten(board: Board, positions: List[Tuple[int, int]]) -> bool:
        """Check if line has at least one kitten"""
        for row, col in positions:
            piece = board.get_piece(row, col)
            if piece and piece.type == PieceType.KITTEN:
                return True
        return False

    @staticmethod
    def graduate_line(game_state: GameState, line: List[Tuple[int, int]]):
        """
        Graduate a line of three pieces.
        Remove all pieces from board. Kittens leave game, Cats return to pool.
        Add 3 new Cats from reserve to pool.
        """
        player = game_state.get_current_player()
        board = game_state.board

        # Remove pieces from board
        cats_returned = 0
        kittens_graduated = 0

        for row, col in line:
            piece = board.remove_piece(row, col)
            if piece:
                if piece.type == PieceType.CAT:
                    player.return_to_pool(piece)
                    cats_returned += 1
                else:  # KITTEN
                    kittens_graduated += 1
                    # Kitten leaves the game permanently

        # Graduate: move 3 Cats from reserve to pool
        player.graduate_kittens(3)


class WinChecker:
    """Checks for win conditions"""

    @staticmethod
    def check_win(game_state: GameState) -> Optional[Color]:
        """
        Check if current player has won.
        Returns winning color or None.
        """
        player = game_state.get_current_player()
        board = game_state.board

        # Check for three Cats in a row
        lines = GraduationEngine.find_lines_of_three(board, player.color)
        for line in lines:
            # Check if all three are Cats
            pieces = [board.get_piece(row, col) for row, col in line]
            if all(p and p.type == PieceType.CAT for p in pieces):
                return player.color

        # Check if all 8 pieces on board are Cats
        cat_count = 0
        for row in range(Board.SIZE):
            for col in range(Board.SIZE):
                piece = board.get_piece(row, col)
                if piece and piece.color == player.color and piece.type == PieceType.CAT:
                    cat_count += 1

        if cat_count == 8:
            return player.color

        return None


class BoopGame:
    """Main game engine"""

    def __init__(self, verbose: bool = False):
        self.state = GameState()
        self.verbose = verbose

    def play_move(self, row: int, col: int, piece_type: PieceType) -> bool:
        """
        Play a move: place a piece and resolve all consequences.
        Returns True if move was valid and game continues, False if invalid.
        """
        player = self.state.get_current_player()

        # Validate position
        if not self.state.board.is_empty(row, col):
            if self.verbose:
                print(f"Invalid move: Position ({row}, {col}) is not empty")
            return False

        # Get piece from pool
        piece = player.get_piece_from_pool(piece_type)
        if not piece:
            if self.verbose:
                print(f"Invalid move: No {piece_type} available in pool")
            return False

        # Place piece
        self.state.board.place_piece(row, col, piece)
        self.state.move_count += 1

        if self.verbose:
            print(f"\n{player.color.value.upper()} plays {piece_type.value} at ({row}, {col})")

        # Resolve booping
        booped_off = BoopEngine.resolve_boop(self.state, (row, col))

        # Return booped pieces to their owners' pools
        for booped_piece in booped_off:
            for p in self.state.players:
                if p.color == booped_piece.color:
                    p.return_to_pool(booped_piece)
                    if self.verbose:
                        print(f"  {booped_piece} was booped off the board")

        if self.verbose and self.verbose:
            print(self.state.board)

        # Check for graduation
        lines = GraduationEngine.find_lines_of_three(self.state.board, player.color)
        if lines:
            # Graduate first line that has at least one kitten
            for line in lines:
                if GraduationEngine._line_has_kitten(self.state.board, line):
                    if self.verbose:
                        print(f"  Graduating line: {line}")
                    GraduationEngine.graduate_line(self.state, line)
                    break

        # Alternative graduation: all 8 pieces on board, no lines
        pieces_on_board = self.state.board.count_pieces_by_color(player.color)
        if pieces_on_board == 8 and not lines:
            # Could graduate a single kitten, but this is optional and rare
            # For simplicity, we'll skip this in AI for now
            pass

        # Check for win
        winner = WinChecker.check_win(self.state)
        if winner:
            self.state.winner = winner
            if self.verbose:
                print(f"\n{winner.value.upper()} WINS!")
            return True

        # Switch player
        self.state.switch_player()

        return True

    def get_valid_moves(self) -> List[Tuple[int, int, PieceType]]:
        """Get all valid moves for current player"""
        moves = []
        player = self.state.get_current_player()
        empty_positions = self.state.get_empty_positions()

        # Check what piece types are available
        has_kitten = any(p.type == PieceType.KITTEN for p in player.pool)
        has_cat = any(p.type == PieceType.CAT for p in player.pool)

        for row, col in empty_positions:
            if has_kitten:
                moves.append((row, col, PieceType.KITTEN))
            if has_cat:
                moves.append((row, col, PieceType.CAT))

        return moves

    def is_game_over(self) -> bool:
        """Check if game is over"""
        if self.state.winner:
            return True

        # Game is over if current player has no moves
        player = self.state.get_current_player()
        if not player.has_pieces_to_play():
            return True

        # Check if board is full
        if len(self.state.get_empty_positions()) == 0:
            return True

        return False

    def get_winner(self) -> Optional[Color]:
        """Get the winner, if any"""
        return self.state.winner


if __name__ == "__main__":
    # Simple test game
    game = BoopGame(verbose=True)

    print("BOOP Game Engine Test")
    print("=" * 40)
    print(game.state.board)

    # Play a few moves
    game.play_move(2, 2, PieceType.KITTEN)  # Orange center
    game.play_move(2, 3, PieceType.KITTEN)  # Gray next to orange
    game.play_move(3, 2, PieceType.KITTEN)  # Orange

    print("\nGame engine test complete!")
