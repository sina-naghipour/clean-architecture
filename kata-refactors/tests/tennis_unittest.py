import unittest

from tennis.game import Player, TennisGame

test_cases = [
    (0, 0, "Love-All", "player1", "player2"),
    (1, 1, "Fifteen-All", "player1", "player2"),
    (2, 2, "Thirty-All", "player1", "player2"),
    (3, 3, "Deuce", "player1", "player2"),
    (4, 4, "Deuce", "player1", "player2"),
    (1, 0, "Fifteen-Love", "player1", "player2"),
    (0, 1, "Love-Fifteen", "player1", "player2"),
    (2, 0, "Thirty-Love", "player1", "player2"),
    (0, 2, "Love-Thirty", "player1", "player2"),
    (3, 0, "Forty-Love", "player1", "player2"),
    (0, 3, "Love-Forty", "player1", "player2"),
    (4, 0, "Win for player1", "player1", "player2"),
    (0, 4, "Win for player2", "player1", "player2"),
    (2, 1, "Thirty-Fifteen", "player1", "player2"),
    (1, 2, "Fifteen-Thirty", "player1", "player2"),
    (3, 1, "Forty-Fifteen", "player1", "player2"),
    (1, 3, "Fifteen-Forty", "player1", "player2"),
    (4, 1, "Win for player1", "player1", "player2"),
    (1, 4, "Win for player2", "player1", "player2"),
    (3, 2, "Forty-Thirty", "player1", "player2"),
    (2, 3, "Thirty-Forty", "player1", "player2"),
    (4, 2, "Win for player1", "player1", "player2"),
    (2, 4, "Win for player2", "player1", "player2"),
    (4, 3, "Advantage player1", "player1", "player2"),
    (3, 4, "Advantage player2", "player1", "player2"),
    (5, 4, "Advantage player1", "player1", "player2"),
    (4, 5, "Advantage player2", "player1", "player2"),
    (15, 14, "Advantage player1", "player1", "player2"),
    (14, 15, "Advantage player2", "player1", "player2"),
    (6, 4, "Win for player1", "player1", "player2"),
    (4, 6, "Win for player2", "player1", "player2"),
    (16, 14, "Win for player1", "player1", "player2"),
    (14, 16, "Win for player2", "player1", "player2"),
]


def play_game(TennisGame, player1_score, player2_score, player1_name, player2_name):
    player1 = Player(player1_name, player1_score)
    player2 = Player(player2_name, player2_score)

    game = TennisGame(player1, player2)
    return game


class TestTennis(unittest.TestCase):
    def test_score_games(self):
        for testcase in test_cases:
            (p1_points, p2_points, score, p1_name, p2_name) = testcase
            game = play_game(TennisGame, p1_points, p2_points, p1_name, p2_name)
            with self.subTest(f"{TennisGame.__name__} - {testcase}"):
                self.assertEqual(score, game.score())


if __name__ == "__main__":
    unittest.main()
