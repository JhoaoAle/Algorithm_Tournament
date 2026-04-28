import random

# Función que intenta detectar si el oponente juega de manera aleatoria
def is_random(opponent_moves):
    n = len(opponent_moves)

    # Se necesita un mínimo de rondas para poder analizar comportamiento
    if n < 20:
        return False

    # Cuenta cuántas veces el oponente ha cooperado
    cooperations = opponent_moves.count('C')

    # Cuenta cuántas veces cambia de jugada (C -> D o D -> C)
    changes = sum(1 for i in range(1, n) if opponent_moves[i] != opponent_moves[i-1])

    # Calcula proporción de cooperación
    coop_rate = cooperations / n

    # Calcula frecuencia de cambios de decisión
    change_rate = changes / (n - 1)

    # Si coopera cerca del 50% y cambia mucho, se considera aleatorio
    return 0.4 < coop_rate < 0.6 and change_rate > 0.55


# Función principal del agente
def strategy(my_moves, opponent_moves, rng=None):
    n = len(my_moves)
    
    if rng is None:
        rng = random


    # Primera ronda: siempre cooperar
    if n == 0:
        return 'C'
    

    
    # Introduce ruido: pequeña probabilidad de traicionar
    # Esto evita que el agente sea completamente predecible
    if random.random() < 0.02:
        return 'D'

    # Si el oponente parece aleatorio, se responde siempre con traición
    if is_random(opponent_moves):
        return 'D'

    # Cuenta cuántas traiciones consecutivas ha hecho el oponente
    defections = 0
    for move in reversed(opponent_moves):
        if move == 'D':
            defections += 1
        else:
            break

    # Mecanismo de perdón: intenta cooperar tras varias traiciones seguidas
    if 3 <= defections <= 5:
        return 'C'

    # Estrategia base: copiar la última jugada del oponente (Tit for Tat)
    return opponent_moves[-1]