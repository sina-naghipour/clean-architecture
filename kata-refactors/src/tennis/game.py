class Player:
    def __init__(self, name: str, score: int = 0):
        self.name = name
        self.score = score


class TennisGame:
    SCORE_MAP = {0: "Love", 1: "Fifteen", 2: "Thirty", 3: "Forty"}

    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2

    def __translate_score_to_idiom(self, player: Player) -> str:
        return self.SCORE_MAP.get(player.score, str(player.score))

    def __translate_idiom_to_score(self, idiom: str) -> int:
        if idiom == "Love":
            return 0
        elif idiom == "Fifteen":
            return 1
        elif idiom == "Thirty":
            return 2
        elif idiom == "Forty":
            return 3
        else:
            raise ValueError(f"Invalid idiom: {idiom}")

    def __leading_player(self) -> Player:
        if self.player1.score > self.player2.score:
            return self.player1
        else:
            return self.player2

    def __is_win(self) -> bool:
        if self.player1.score > 3 or self.player2.score > 3:
            if abs(self.player1.score - self.player2.score) >= 2:
                return True
            else:
                return False
        else:
            return False

    def __is_advantage(self) -> bool:
        if self.player1.score >= 3 and self.player2.score >= 3:
            if abs(self.player1.score - self.player2.score) == 1:
                return True
        return False

    def __is_tied(self):
        return self.player1.score == self.player2.score

    def score(self):
        if self.__is_win():
            return f"Win for {self.__leading_player().name}"

        elif self.__is_advantage():
            return f"Advantage {self.__leading_player().name}"

        elif self.__is_tied():
            if self.player1.score < 3:
                idiom_player_1 = self.__translate_score_to_idiom(self.player1)
                return f"{idiom_player_1}-All"
            else:
                return "Deuce"

        elif self.player1.score <= 3 and self.player2.score <= 3:
            idiom_player_1 = self.__translate_score_to_idiom(self.player1)
            idiom_player_2 = self.__translate_score_to_idiom(self.player2)

            return f"{idiom_player_1}-{idiom_player_2}"
