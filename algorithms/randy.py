import random


def strategy(my_moves, opponent_moves, rng=None):
    """
    Random strategy (coin flip)

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """

    if rng is None:
        rng = random

    if len(my_moves) != len(opponent_moves):
        raise ValueError("Histories must have the same length")
        
    return 'C' if rng.random() < 0.5 else 'D'