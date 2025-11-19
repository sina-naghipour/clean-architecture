import pytest
from tennis_unittest import play_game, test_cases

from tennis.game import Player, TennisGame


@pytest.mark.parametrize(
    "p1_points p2_points score p1_name p2_name".split(), test_cases
)
def test_get_score_most_games(p1_points, p2_points, score, p1_name, p2_name):
    game = play_game(TennisGame, p1_points, p2_points, p1_name, p2_name)
    assert score == game.score()


@pytest.mark.parametrize(
    "idiom,expected",
    [
        ("Love", 0),
        ("Fifteen", 1),
        ("Thirty", 2),
        ("Forty", 3),
    ],
)
def test_idiom_to_score_translation(idiom, expected):
    player1 = Player("Alice")
    player2 = Player("Bob")
    game = TennisGame(player1, player2)

    assert game._TennisGame__translate_idiom_to_score(idiom) == expected


def test_idiom_to_score_invalid_raises():
    player1 = Player("Alice")
    player2 = Player("Bob")
    game = TennisGame(player1, player2)

    with pytest.raises(ValueError):
        game._TennisGame__translate_idiom_to_score("Invalid")
