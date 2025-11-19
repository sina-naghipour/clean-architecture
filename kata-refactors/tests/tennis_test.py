import pytest
from tennis_unittest import play_game, test_cases

from tennis.game import TennisGame


@pytest.mark.parametrize(
    "p1_points p2_points score p1_name p2_name".split(), test_cases
)
def test_get_score_most_games(p1_points, p2_points, score, p1_name, p2_name):
    game = play_game(TennisGame, p1_points, p2_points, p1_name, p2_name)
    assert score == game.score()
