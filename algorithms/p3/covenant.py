import random

FORGIVENESS_PROB = 12
PATIENCE_THRESHOLD = 4
MIN_DETECT_ROUNDS = 8
EXPLOITER_THRESHOLD = 60


def count_moves(moves, move):
    return sum(1 for m in moves if m == move)


def consecutive_cooperations(moves):
    count = 0
    for m in reversed(moves):
        if m == 'C':
            count += 1
        else:
            break
    return count


def strategy(my_moves, opponent_moves, rng=None):
    if rng is None:
        rng = random

    if len(my_moves) != len(opponent_moves):
        raise ValueError("Histories must have the same length")

    n = len(my_moves)

    # RULE 0 — Initial move
    if n == 0:
        return 'C'

    defections = count_moves(opponent_moves, 'D')

    # RULE 4 — Exploiter detector
    if n >= MIN_DETECT_ROUNDS:
        percentage = (defections * 100) // n
        if percentage > EXPLOITER_THRESHOLD:
            return 'D'

    # Base move (Tit-for-Tat)
    base = opponent_moves[-1]

    # RULE 3 — Deterministic forgiveness
    if (
        base == 'C' and
        defections > 0 and
        consecutive_cooperations(opponent_moves) >= PATIENCE_THRESHOLD
    ):
        return 'C'

    # RULE 2 — Stochastic forgiveness
    if base == 'D' and rng.randint(0, 99) < FORGIVENESS_PROB:
        return 'C'

    return base