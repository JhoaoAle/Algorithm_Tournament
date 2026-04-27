GRACE_PERIOD = 2
BETRAYAL_THRESHOLD = 0.5

def strategy(my_moves, opponent_moves):
    """
    Adaptive Mirror strategy

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """


    n = len(opponent_moves)

    # Safety check
    if len(my_moves) != n:
        raise ValueError("Histories must have the same length")

    # Rule 1: initial cooperation (good faith)
    if n < GRACE_PERIOD:
        return 'C'

    # Compute betrayal rate
    defections = sum(1 for m in opponent_moves if m == 'D')
    betrayal_rate = defections / n

    # Rule 2: mirror last move (if opponent cooperated)
    if opponent_moves[-1] == 'C':
        return 'C'

    # Rule 3: opponent defected → evaluate history
    if betrayal_rate > BETRAYAL_THRESHOLD:
        return 'D'

    # Rule 4: occasional betrayal → forgive
    return 'C'