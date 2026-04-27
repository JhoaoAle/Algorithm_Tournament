import random

COOPERAR = 0
DESVIAR = 1


def strategy(my_moves, opponent_moves):
    """
    Random strategy:
    4% cooperate, 96% defect
    """

    r = random.randint(0, 99)

    if r < 4:
        return 'C'
    else:
        return 'D'