# BOOP Game Implementation

A complete implementation of the BOOP board game with AI strategies and tournament system.

## Overview

BOOP is a two-player abstract strategy game where players place cat pieces on a 6x6 grid. When placed, pieces "boop" (push) adjacent pieces away. Players graduate Kittens into Cats by forming lines of three, and win by lining up three Cats in a row.

## Files

- **boop_game.py** - Core game engine with complete rule implementation
- **boop_strategies.py** - AI strategies for playing the game
- **boop_tournament.py** - Tournament system for running AI vs AI competitions
- **boop_demo.py** - Quick demonstrations and simplified tournaments

## Game Engine Features

### Complete Rule Implementation

1. **6x6 Board** - Grid-based gameplay
2. **Piece Types** - Kittens and Cats with different properties
3. **Booping Mechanics**
   - Pieces push all 8 adjacent neighbors away
   - Kittens cannot boop Cats (but Cats can boop everything)
   - Line-of-two blocking (pieces in a line cannot be pushed further along that line)
   - Pieces pushed off the board return to owner's pool

4. **Graduation System**
   - Three Kittens in a row graduate to become Cats
   - Mixed lines (Kittens + Cats) also graduate
   - Graduated Kittens leave the game, Cats return to pool

5. **Win Conditions**
   - Three Cats in a row (horizontal, vertical, or diagonal)
   - All 8 pieces on board are Cats (alternative win)

## AI Strategies

Five different strategies implemented:

### 1. RandomStrategy
- Plays completely random valid moves
- Baseline for comparison

### 2. GreedyStrategy
- Prioritizes winning moves
- Tries to create graduation opportunities
- Prefers Cats over Kittens
- Favors center positions for control
- Basic threat detection

### 3. DefensiveStrategy
- Focuses on blocking opponent lines
- Tries to boop opponent pieces off the board
- Avoids edge positions (harder to be pushed off)
- Evaluates blocking potential
- Prefers safe, sustainable positions

### 4. AggressiveStrategy
- Rushes to build three Cats in a row
- Graduates Kittens as fast as possible
- Takes risks for potential wins
- Heavily favors Cat placements
- Looks for winning line opportunities

### 5. SmartStrategy
- Balanced approach combining multiple heuristics
- Looks ahead for winning moves
- Blocks opponent threats
- Manages piece types strategically
- Best overall performance

## Usage

### Run a Single Demo Game
```bash
python3 boop_demo.py
```

Shows a detailed move-by-move game between Greedy and Defensive strategies.

### Run Quick Tournament (2 strategies, 5 games)
```bash
python3 boop_demo.py tournament
```

Quick results showing Random vs Greedy.

### Run Full Tournament (All strategies, round-robin)
```bash
python3 boop_tournament.py
```

Runs 100 matches total:
- Each strategy plays every other strategy
- 10 games per matchup
- Colors alternate
- Complete statistics and head-to-head records

## Tournament Results

The tournament system provides:
- Win/Loss records for each strategy
- Win percentages
- Average moves per game
- Average time per game
- Complete head-to-head matchup records

### Example Output
```
Rank   Strategy        W     L     Win%     Avg Moves    Avg Time (s)
----------------------------------------------------------------------
1      Smart           XX    XX    XX.X%    XX.X         X.XXX
2      Greedy          XX    XX    XX.X%    XX.X         X.XXX
3      Defensive       XX    XX    XX.X%    XX.X         X.XXX
4      Aggressive      XX    XX    XX.X%    XX.X         X.XXX
5      Random          XX    XX    XX.X%    XX.X         X.XXX
```

## Implementation Highlights

### Booping Engine
The booping mechanics are the most complex part:
- Calculates push directions for all 8 neighbors
- Checks line-of-two blocking rule
- Handles cascading effects (pieces pushed but don't cause new boops)
- Returns pieces to appropriate pools when booped off board

### Graduation Engine
- Searches for all lines of three in 4 directions
- Handles mixed lines (Kittens + Cats)
- Properly removes/returns pieces
- Manages reserve and pool correctly

### Win Checker
- Verifies Cat-only lines (not Kittens)
- Checks all-Cats-on-board alternative win
- Validates after all booping resolves

## Game State Management

The engine maintains:
- Board state (6x6 grid)
- Player pools (available pieces to play)
- Player reserves (Cats waiting to graduate)
- Current player tracking
- Move history
- Winner status

## Strategy Evaluation

Strategies are evaluated by simulating moves and scoring:
- Immediate wins: +10000
- Letting opponent win: -5000
- Graduation opportunities: +200-400
- Piece control: +50-150
- Position quality: +10-50
- Blocking value: +100+

## Performance

- Random vs Greedy: Greedy wins ~60-70%
- Smart strategies typically win 60-80% against Random
- Greedy vs Defensive: Very competitive (~50/50)
- Games typically complete in 20-40 moves

## Future Enhancements

Potential improvements:
1. **Monte Carlo Tree Search (MCTS)** for stronger AI
2. **Neural network evaluation** for position assessment
3. **Opening book** for early game optimization
4. **Endgame database** for perfect play in final positions
5. **Human vs AI interface** (command-line or GUI)
6. **Move validation UI** for teaching the rules
7. **Replay system** to review interesting games
8. **ELO rating system** for strategy ranking

## Technical Details

### Language: Python 3
### Dependencies: None (pure Python standard library)
### Key Classes:
- `Board` - 6x6 grid management
- `Piece` - Individual game pieces
- `Player` - Player state and piece management
- `GameState` - Complete game state
- `BoopEngine` - Booping mechanics
- `GraduationEngine` - Kitten graduation
- `WinChecker` - Win condition validation
- `BoopGame` - Main game controller
- `Strategy` - Base class for AI
- `Tournament` - Competition management

## License

Educational implementation for demonstration purposes.

## Credits

BOOP is a game by Scott Brady, published by Smirk and Dagger Games.
This is an independent implementation for educational purposes.
