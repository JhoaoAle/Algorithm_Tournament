import random


def strategy(my_moves, opponent_moves, rng=None):
    """
    Enhanced Tit-for-Tat with noise, detection, and forgiveness.

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

    # --- Helper metrics ---
    def coop_rate(moves):
        return moves.count('C') / len(moves) if moves else 1.0

    def instability(moves):
        # counts how often opponent changes behavior
        return sum(
            1 for i in range(1, len(moves))
            if moves[i] != moves[i - 1]
        ) / max(1, len(moves) - 1)

    # --- 1. Initial cooperation ---
    if n == 0:
        return 'C'

    # --- 2. Detect random-like opponent ---
    if n >= 5:
        cr = coop_rate(opponent_moves)
        inst = instability(opponent_moves)

        # high randomness → always defect
        if 0.3 < cr < 0.7 and inst > 0.5:
            return 'D'

    # --- 3. Forgiveness mechanism ---
    if n >= 3:
        last_two_defections = (
            opponent_moves[-1] == 'D' and
            opponent_moves[-2] == 'D'
        )
        if last_two_defections:
            return 'C'

    # --- 4. Noise (small chance to defect unexpectedly) ---
    noise_prob = 0.05  # 5% unpredictability
    if rng.random() < noise_prob:
        return 'D'

    # --- 5. Core Tit-for-Tat behavior ---
    return opponent_moves[-1]