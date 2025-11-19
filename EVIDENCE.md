## EVIDENCE.md

```markdown
# Evidence: Tennis Kata Clean Architecture

## 1. Domain Model
**File**: `src/tennis/game.py:1-8`
```python
class Player:
    def __init__(self, name: str, score: int = 0):
        self.name = name
        self.score = score

class TennisGame:
    SCORE_MAP = {0: "Love", 1: "Fifteen", 2: "Thirty", 3: "Forty"}

    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
```

## 2. Business Logic
**File**: `src/tennis/game.py:17-30`
```python
    def __translate_score_to_idiom(self, player: Player) -> str:
        return self.SCORE_MAP.get(player.score, str(player.score))

    def __is_win(self) -> bool:
        return (self.player1.score > 3 or self.player2.score > 3) and \
               abs(self.player1.score - self.player2.score) >= 2

    def __is_advantage(self) -> bool:
        return (self.player1.score >= 3 and self.player2.score >= 3) and \
               abs(self.player1.score - self.player2.score) == 1
```

## 3. Score Calculation
**File**: `src/tennis/game.py:52-70`
```python
    def score(self):
        if self.__is_win():
            return f"Win for {self.__leading_player().name}"
        elif self.__is_advantage():
            return f"Advantage {self.__leading_player().name}"
        elif self.__is_tied():
            return "Deuce" if self.player1.score >= 3 else f"{self.__translate_score_to_idiom(self.player1)}-All"
        else:
            return f"{self.__translate_score_to_idiom(self.player1)}-{self.__translate_score_to_idiom(self.player2)}"
```

## 4. Comprehensive Testing
**File**: `tests/tennis_test.py:1-10`
```python
@pytest.mark.parametrize("p1_points p2_points score p1_name p2_name".split(), test_cases)
def test_get_score_most_games(p1_points, p2_points, score, p1_name, p2_name):
    game = play_game(TennisGame, p1_points, p2_points, p1_name, p2_name)
    assert score == game.score()
```

## 5. Test Data Samples
**File**: `tests/tennis_unittest.py:1-10`
```python
test_cases = [
    (0, 0, "Love-All", "player1", "player2"),
    (3, 3, "Deuce", "player1", "player2"), 
    (4, 3, "Advantage player1", "player1", "player2"),
    (4, 0, "Win for player1", "player1", "player2"),
    (15, 14, "Advantage player1", "player1", "player2"),
]
```

## 6. Test Helper
**File**: `tests/tennis_unittest.py:64-70`
```python
def play_game(TennisGame, player1_score, player2_score, player1_name, player2_name):
    player1 = Player(player1_name, player1_score)
    player2 = Player(player2_name, player2_score)
    return TennisGame(player1, player2)
```

## Key Improvements
- **Clean Architecture**: Player objects vs internal state
- **Small Methods**: 6 focused methods vs 1 complex method  
- **Type Safety**: Type hints throughout
- **Testability**: Direct state injection vs point simulation
- **33 Test Cases**: Full coverage of tennis scoring rules
```