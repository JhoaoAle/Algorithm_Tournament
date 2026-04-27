import random


def strategy(my_moves, opponent_moves, rng=None):
    """
    AMAST Strategy: Logical Analysis Model

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """

    if rng is None:
        rng = random

    n = len(opponent_moves)

    if n == 0:
        return "C"

    # Safety check
    if len(my_moves) != n:
        raise ValueError("Histories must have the same length")

    # --- Helper calculations ---
    def coop_rate(moves):
        if len(moves) == 0:
            return 1.0
        return moves.count('C') / len(moves)

    # --- A. Confidence calculation ---
    global_coop = coop_rate(opponent_moves)

    last5 = opponent_moves[-5:] if n >= 5 else opponent_moves
    recent_coop = coop_rate(last5)

    confidence = 0.7 * global_coop + 0.3 * recent_coop

    # --- B. Risk evaluation (retaliation analysis) ---
    retaliation_risk = 0.0
    if n > 0:
        my_defections = my_moves.count('D')
        if my_defections > 0:
            # how often opponent punished after our defections
            punishments = sum(
                1 for i in range(1, n)
                if my_moves[i - 1] == 'D' and opponent_moves[i] == 'D'
            )
            retaliation_risk = punishments / my_defections

    # --- Base decision ---
    last_move = opponent_moves[-1] if n > 0 else 'C'

    # --- C. Exploration (high confidence, low risk) ---
    if confidence > 0.7 and retaliation_risk < 0.5:
        if rng.random() < 0.25:
            return 'D'

    # --- D. Adaptive forgiveness ---
    if n > 0 and last_move == 'D':
        forgiveness_prob = confidence  # higher trust → more forgiveness
        if rng.random() < forgiveness_prob:
            return 'C'
        else:
            return 'D'

    # --- Default behavior ---
    return 'C' if last_move == 'C' else 'D'