import sqlite3
from collections import defaultdict
from statistics import mean, pstdev

from weasyprint import HTML

from architecture.db import DB_PATH


# -----------------------------
# HELPERS
# -----------------------------
def classify(coop, retaliation, forgiveness):
    if coop > 0.9:
        return "Very Nice"
    if coop < 0.2:
        return "Very Nasty"
    if retaliation > 0.75:
        return "Aggressive"
    if forgiveness > 0.6:
        return "Forgiving"
    return "Balanced"


def consistency_label(std_dev):
    if std_dev < 1:
        return "Highly Consistent"
    elif std_dev < 3:
        return "Moderately Consistent"
    else:
        return "Volatile"


# -----------------------------
# DATA EXTRACTION
# -----------------------------
def get_leaderboard(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, SUM(score) as total_score
        FROM (
            SELECT competitor_a as competitor, score_a as score FROM matches
            UNION ALL
            SELECT competitor_b, score_b FROM matches
        )
        GROUP BY competitor
        ORDER BY total_score DESC
    """)

    return cur.fetchall()


def get_average_leaderboard(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, AVG(score) as avg_score
        FROM (
            SELECT competitor_a as competitor, score_a as score FROM matches
            UNION ALL
            SELECT competitor_b, score_b FROM matches
        )
        GROUP BY competitor
        ORDER BY avg_score DESC
    """)

    return cur.fetchall()


def get_avg_rounds(conn):
    cur = conn.cursor()
    cur.execute("SELECT AVG(rounds) FROM matches")
    return cur.fetchone()[0]


def get_best_worst(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, opponent, score FROM (
            SELECT competitor_a as competitor, competitor_b as opponent, score_a as score FROM matches
            UNION ALL
            SELECT competitor_b, competitor_a, score_b FROM matches
        )
    """)

    data = defaultdict(list)
    for comp, opp, score in cur.fetchall():
        data[comp].append((opp, score))

    best = {}
    worst = {}

    for comp, matches in data.items():
        best[comp] = max(matches, key=lambda x: x[1])
        worst[comp] = min(matches, key=lambda x: x[1])

    return best, worst


def get_behavior_stats(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_a, action_a, action_b, match_id, round
        FROM match_actions
    """)

    data = defaultdict(list)

    for comp, a, b, match_id, r in cur.fetchall():
        data[comp].append((match_id, r, a, b))

    stats = {}

    for comp, rows in data.items():
        rows.sort()

        coop = 0
        total = 0

        retaliation_events = 0
        retaliation_total = 0

        forgiveness_events = 0

        prev_by_match = {}

        for match_id, r, a, b in rows:
            total += 1
            if a == 'C':
                coop += 1

            if match_id in prev_by_match:
                prev_b = prev_by_match[match_id]

                if prev_b == 'D':
                    retaliation_total += 1
                    if a == 'D':
                        retaliation_events += 1
                    if a == 'C':
                        forgiveness_events += 1

            prev_by_match[match_id] = b

        coop_rate = coop / total if total else 0
        retaliation_rate = (retaliation_events / retaliation_total) if retaliation_total else 0
        forgiveness_rate = (forgiveness_events / retaliation_total) if retaliation_total else 0

        stats[comp] = {
            "coop": coop_rate,
            "retaliation": retaliation_rate,
            "forgiveness": forgiveness_rate
        }

    return stats


def get_score_variability(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, score FROM (
            SELECT competitor_a as competitor, score_a as score FROM matches
            UNION ALL
            SELECT competitor_b, score_b FROM matches
        )
    """)

    data = defaultdict(list)

    for comp, score in cur.fetchall():
        data[comp].append(score)

    variability = {}

    for comp, scores in data.items():
        if len(scores) > 1:
            std_dev = pstdev(scores)
        else:
            std_dev = 0

        variability[comp] = std_dev

    return variability


# -----------------------------
# HTML GENERATION
# -----------------------------
def generate_html(iteration, leaderboard, avg_leaderboard, avg_rounds, best, worst, behavior, variability):

    # --- Leaderboard: Total ---
    total_lb_html = "<h2>Leaderboard (Total Score)</h2><ol>"
    for name, score in leaderboard:
        total_lb_html += f"<li>{name}: {score:.2f}</li>"
    total_lb_html += "</ol>"

    # --- Leaderboard: Average ---
    avg_lb_html = "<h2>Leaderboard (Average Score)</h2><ol>"
    for name, score in avg_leaderboard:
        avg_lb_html += f"<li>{name}: {score:.2f}</li>"
    avg_lb_html += "</ol>"

    # --- Detailed section sorted by average ---
    avg_lookup = dict(avg_leaderboard)
    total_lookup = dict(leaderboard)

    details = "<h2>Detailed Results (Ordered by Average Score)</h2>"

    for i, (name, avg_score) in enumerate(avg_leaderboard, start=1):
        total_score = total_lookup.get(name, 0)

        b_opp, b_score = best.get(name, ("-", 0))
        w_opp, w_score = worst.get(name, ("-", 0))

        beh = behavior.get(name, {})
        coop = beh.get("coop", 0)
        ret = beh.get("retaliation", 0)
        forg = beh.get("forgiveness", 0)

        std_dev = variability.get(name, 0)
        consistency = consistency_label(std_dev)

        label = classify(coop, ret, forg)

        if coop > 0.8 and forg > 0.5:
            insight = "Highly cooperative and resilient."
        elif ret > 0.8:
            insight = "Strongly retaliatory."
        elif coop < 0.3:
            insight = "Predominantly defecting."
        else:
            insight = "Balanced behavioral strategy."

        details += f"""
        <p>
        <b>#{i} — {name}</b><br>
        Total Score: {total_score:.2f} | Average Score: {avg_score:.2f}<br>
        Std Dev: {std_dev:.2f} → {consistency}<br>
        Best vs {b_opp} ({b_score:.1f}) | Worst vs {w_opp} ({w_score:.1f})<br>
        Coop: {coop:.2f}, Ret: {ret:.2f}, Forg: {forg:.2f} → {label}<br>
        {insight}
        </p>
        """

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 30px;
                line-height: 1.6;
            }}
            h1 {{
                text-align: center;
            }}
        </style>
    </head>
    <body>

        <h1>Tournament Report</h1>

        <p><b>Iteration:</b> {iteration}</p>
        <p><b>Average Rounds per Match:</b> {avg_rounds:.2f}</p>

        <hr>

        {total_lb_html}
        {avg_lb_html}

        <hr>

        {details}

    </body>
    </html>
    """

    return html


# -----------------------------
# MAIN ENTRY
# -----------------------------
def generate_report(iteration: int):
    print(f"Generating report for iteration {iteration}...")

    with sqlite3.connect(DB_PATH) as conn:
        leaderboard = get_leaderboard(conn)
        avg_leaderboard = get_average_leaderboard(conn)
        avg_rounds = get_avg_rounds(conn)
        best, worst = get_best_worst(conn)
        behavior = get_behavior_stats(conn)
        variability = get_score_variability(conn)

    html = generate_html(
        iteration,
        leaderboard,
        avg_leaderboard,
        avg_rounds,
        best,
        worst,
        behavior,
        variability
    )

    output_file = f"tournament_report_{iteration}.pdf"
    HTML(string=html).write_pdf(output_file)

    print(f"Report saved to {output_file}")