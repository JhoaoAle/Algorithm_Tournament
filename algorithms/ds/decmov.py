import random


def strategy(history_a, history_b, rng=None):
    """
    Simple probabilistic Tit-for-Tat variant

    history_a: list of own past moves
    history_b: list of opponent past moves
    step: current round index (0-based)

    Returns: 'C' or 'D'
    """
    step = len(history_a)

    if rng is None:
        rng = random

    # Step 0: always cooperate
    if step == 0:
        return 'C'

    prev_opp_move = history_b[step - 1]

    # Mirror cooperation
    if prev_opp_move == 'C':
        return 'C'

    # Otherwise: 8% chance to cooperate, 92% defect
    chance = rng.random()

    return 'C' if chance < 0.08 else 'D'