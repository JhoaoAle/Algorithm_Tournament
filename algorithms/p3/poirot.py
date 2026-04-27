import random


def strategy(my_moves, opponent_moves, rng=None):
    """
    Dynamic Strategy

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """

    if rng is None:
        rng = random

    n = len(opponent_moves)

    # Safety check
    if len(my_moves) != n:
        raise ValueError("Histories must have the same length")

    # --- Early fixed behavior ---
    if n == 0:
        return 'C'  # Round 1
    if n == 1:
        return 'C'  # Round 2
    if n == 2:
        return 'D'  # Round 3 (probe)
    if n == 3:
        return 'C'  # Round 4 (observe reaction)

    # --- From round 5 onward: adaptive logic ---

    # Check last two moves of opponent
    last = opponent_moves[-1]
    last_two_defections = (opponent_moves[-1] == 'D' and opponent_moves[-2] == 'D')

    if last_two_defections:
        # Compute cooperation rate
        coop_rate = opponent_moves.count('C') / n

        # Forgiveness probability: 5% to 30%
        # More cooperative opponent → more forgiveness
        # More defecting opponent → less forgiveness
        forgiveness_prob = 0.05 + 0.25 * coop_rate  # range [0.05, 0.30]

        if rng.random() < forgiveness_prob:
            return 'C'
        else:
            return 'D'

    # Default behavior: Tit-for-Tat
    return last