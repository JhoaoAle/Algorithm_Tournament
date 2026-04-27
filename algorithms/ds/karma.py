def strategy(my_moves, opponent_moves):
    """
    Karma-based strategy

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """

    KARMA_INITIAL = 5.0
    COOP_WEIGHT = 1.0
    DEFECT_WEIGHT = 2.0
    RECENT_WEIGHT = 1.5
    THRESHOLD = 0.0

    n = len(opponent_moves)

    # Safety check
    if len(my_moves) != n:
        raise ValueError("Histories must have the same length")

    # Initial move
    if n == 0:
        return 'C'

    karma = KARMA_INITIAL

    for i in range(n):
        weight = RECENT_WEIGHT if i == n - 1 else 1.0

        if opponent_moves[i] == 'C':
            karma += COOP_WEIGHT * weight
        else:
            karma -= DEFECT_WEIGHT * weight

    return 'C' if karma > THRESHOLD else 'D'