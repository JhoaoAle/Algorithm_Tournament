import time
from architecture.tournament import run_single_iteration, init_db

SLEEP_TIME = 5

if __name__ == "__main__":
    init_db()
    iteration = 1

    while True:
        print(f"Running iteration {iteration}")

        start = time.time()
        run_single_iteration(iteration)
        duration = time.time() - start

        print(f"Iteration {iteration} finished in {duration:.2f}s")

        iteration += 1
        time.sleep(max(0, SLEEP_TIME - duration))