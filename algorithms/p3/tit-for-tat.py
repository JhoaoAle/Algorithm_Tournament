def strategy(my_moves, opponent_moves):
    """
    Classic Tit-for-Tat strategy

    my_moves: list of own past moves ['C','D',...]
    opponent_moves: list of opponent past moves ['C','D',...]

    Returns: 'C' (cooperate) or 'D' (defect)
    """

    # First move: cooperate
    if len(opponent_moves) == 0:
        return 'C'

    # Otherwise: copy opponent's last move
    return opponent_moves[-1]