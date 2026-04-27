import random

MAX = 100  #Not strictly needed


def strategy(my_moves, opponent_moves, rng=None):
    """
    Adaptive classification strategy

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' or 'D'
    """

    if rng is None:
        rng = random

    n = len(my_moves)

    # Safety check
    if n != len(opponent_moves):
        raise ValueError("Histories must have the same length")

    # First move: cooperate to gather information
    if n == 0:
        return 'C'

    # Count opponent behavior
    coop = sum(1 for m in opponent_moves if m == 'C')
    defect = n - coop

    coop_rate = coop / n

    # Detect always-cooperator → exploit
    if coop_rate > 0.9:
        return 'D'

    # Detect always-defector → defend
    if coop_rate < 0.1:
        return 'D'

    # Detect Tit-for-Tat behavior
    if n >= 2:
        tit_for_tat = True
        for i in range(1, n):
            if opponent_moves[i] != my_moves[i - 1]:
                tit_for_tat = False
                break

        if tit_for_tat:
            return 'C'

    # Mixed/random behavior → biased aggression
    if 0.3 < coop_rate < 0.7:
        return 'D' if rng.randint(0, 99) < 70 else 'C'

    # Default: Tit-for-Tat fallback
    return opponent_moves[-1]