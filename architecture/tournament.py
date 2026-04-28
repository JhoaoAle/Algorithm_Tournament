import importlib
import random
import sqlite3
from itertools import combinations
from collections import defaultdict

from architecture.db import init_db, DB_PATH


# -----------------------------
# CONFIG
# -----------------------------
MIN_ROUNDS = 350
MAX_ROUNDS = 450

PAYOFF = {
    ('C', 'C'): (30, 30),
    ('C', 'D'): (0, 50),
    ('D', 'C'): (50, 0),
    ('D', 'D'): (0, 0),
}

STRATEGIES = {
    "decmov": "algorithms.ds.decmov",
    "karma": "algorithms.ds.karma",
    "nash": "algorithms.ds.nash",
    "weave": "algorithms.ds.weave",
    "broken_chapulin": "algorithms.ds.broken_chapulin",

    "amast": "algorithms.p3.amast",
    "cagliostro": "algorithms.p3.cagliostro",
    "covenant": "algorithms.p3.covenant",
    "illyn": "algorithms.p3.illyn",
    "poirot": "algorithms.p3.poirot",
    "tit-for-tat": "algorithms.p3.tit-for-tat",

    "randy": "algorithms.randy",
    "trigger": "algorithms.trigger"
}


def load_strategy(path):
    module = importlib.import_module(path)
    return getattr(module, "strategy")

def maybe_flip(move, noise):
    if random.random() < noise:
        return 'D' if move == 'C' else 'C'
    return move

def play_match(strat_a, strat_b, noise = 0.05):
    rounds = random.randint(MIN_ROUNDS, MAX_ROUNDS)

    a_moves, b_moves = [], []
    a_seen_history, b_seen_history = [], []
    score_a, score_b = 0, 0

    action_log = []


    for r in range(rounds):
        a = strat_a(a_seen_history, b_seen_history)
        b = strat_b(b_seen_history, a_seen_history)

        # Store true moves
        a_moves.append(a)
        b_moves.append(b)

        sa, sb = PAYOFF[(a, b)]
        score_a += sa
        score_b += sb

        # Apply perception noise
        a_seen_by_b = maybe_flip(a, noise)
        b_seen_by_a = maybe_flip(b, noise)
        

        # Update perceived histories
        a_seen_history.append(a_seen_by_b)
        b_seen_history.append(b_seen_by_a)

        action_log.append((r, a, b, a_seen_by_b, b_seen_by_a))

    return score_a, score_b, rounds, action_log



# -----------------------------
# TOURNAMENT ITERATION
# -----------------------------
def run_single_iteration(iteration_id: int):
    results = defaultdict(float)

    strategies = {name: load_strategy(path) for name, path in STRATEGIES.items()}
    names = list(strategies.keys())

    # IMPORTANT: single DB connection per iteration (performance fix)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        for a, b in combinations(names, 2):
            score_a, score_b, rounds, log = play_match(
                strategies[a],
                strategies[b]
            )

            # -----------------------------
            # INSERT MATCH
            # -----------------------------
            cur.execute("""
                INSERT INTO matches (
                    iteration, competitor_a, competitor_b,
                    score_a, score_b, rounds
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (iteration_id, a, b, score_a, score_b, rounds))

            match_id = cur.lastrowid

            # -----------------------------
            # INSERT ACTIONS (BATCHED)
            # -----------------------------
            cur.executemany("""
                INSERT INTO match_actions (
                    match_id, iteration, round,
                    competitor_a, competitor_b,
                    action_a, action_b
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                (match_id, iteration_id, r, a, b, aa, bb)
                for r, aa, bb, *_ in log
            ])

            # in-memory aggregation (lightweight)
            results[a] += score_a
            results[b] += score_b

        conn.commit()

    return results



def print_results(results):
    ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)

    print("\nFINAL RESULTS\n")

    for i, (name, score) in enumerate(ranked, start=1):
        print(f"{i:2d}. {name:15s} {score:10.2f}")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    init_db()
    run_single_iteration(iteration_id=1)