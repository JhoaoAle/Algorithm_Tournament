import time
from architecture.tournament import run_single_iteration, init_db
from report_generator import generate_report

SLEEP_TIME = 0
MAX_ITERATIONS = 500

if __name__ == "__main__":
    init_db()

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"Running iteration {iteration}")

        #start = time.time()
        run_single_iteration(iteration)
        #duration = time.time() - start

        #print(f"Iteration {iteration} finished in {duration:.2f}s")

        #if iteration < MAX_ITERATIONS:
        #    time.sleep(max(0, SLEEP_TIME - duration))

    print("\nAll iterations complete. Generating final report\n")
    generate_report(MAX_ITERATIONS)