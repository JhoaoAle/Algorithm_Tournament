import sqlite3
from collections import defaultdict
from statistics import pstdev

from weasyprint import HTML

from architecture.db import DB_PATH


# -----------------------------
# CONFIG
# -----------------------------
T = 50
R = 30
P = 10
S = 0


# -----------------------------
# CLASSIFICATION
# -----------------------------
def classify(coop, punishment, forgiveness):
    if coop > 0.9:
        return "Unconditional Cooperator"
    if coop < 0.1:
        return "Unconditional Defector"
    if punishment > 0.8 and forgiveness < 0.2:
        return "Grim Trigger-like"
    if punishment > 0.6 and forgiveness > 0.4:
        return "Tit-for-Tat-like"
    if forgiveness > 0.7:
        return "Generous Strategy"
    return "Mixed Strategy"


def consistency_label(std_dev):
    if std_dev < 1:
        return "Highly Stable"
    elif std_dev < 3:
        return "Moderately Stable"
    return "Volatile"


# -----------------------------
# DATA EXTRACTION
# -----------------------------
def get_leaderboards(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, SUM(score) FROM (
            SELECT competitor_a AS competitor, score_a AS score FROM matches
            UNION ALL
            SELECT competitor_b AS competitor, score_b AS score FROM matches
        )
        GROUP BY competitor
        ORDER BY SUM(score) DESC
    """)
    total = cur.fetchall()

    cur.execute("""
        SELECT competitor, AVG(score) FROM (
            SELECT competitor_a AS competitor, score_a AS score FROM matches
            UNION ALL
            SELECT competitor_b AS competitor, score_b AS score FROM matches
        )
        GROUP BY competitor
        ORDER BY AVG(score) DESC
    """)
    avg = cur.fetchall()

    return total, avg


def get_avg_rounds(conn):
    return conn.execute("SELECT AVG(rounds) FROM matches").fetchone()[0]


def get_match_outcomes(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_a, competitor_b, score_a, score_b, rounds
        FROM matches
    """)

    wins = defaultdict(int)
    losses = defaultdict(int)
    ties = defaultdict(int)
    total_rounds = defaultdict(int)
    total_score = defaultdict(float)

    for a, b, sa, sb, r in cur.fetchall():
        total_score[a] += sa
        total_score[b] += sb

        total_rounds[a] += r
        total_rounds[b] += r

        if sa > sb:
            wins[a] += 1
            losses[b] += 1
        elif sb > sa:
            wins[b] += 1
            losses[a] += 1
        else:
            ties[a] += 1
            ties[b] += 1

    return wins, losses, ties, total_score, total_rounds


def get_mutual_cooperation(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_a, competitor_b, action_a, action_b
        FROM match_actions
    """)

    mc = defaultdict(int)
    total = defaultdict(int)

    for a_name, b_name, a, b in cur.fetchall():
        total[a_name] += 1
        total[b_name] += 1

        if a == 'C' and b == 'C':
            mc[a_name] += 1
            mc[b_name] += 1

    return {k: mc[k] / total[k] if total[k] else 0 for k in total}


def get_behavior_stats(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_a, competitor_b, action_a, action_b, match_id, round
        FROM match_actions
    """)

    data = defaultdict(list)

    for a_name, b_name, a, b, match_id, r in cur.fetchall():
        data[a_name].append((match_id, r, a, b))
        data[b_name].append((match_id, r, b, a))

    stats = {}

    for comp, rows in data.items():
        rows.sort()

        coop = total = 0
        first_moves = []
        switch_count = 0

        prev_action = {}
        prev_opponent = {}

        cc = cd = dc = dd = 0

        for match_id, r, a, b in rows:
            total += 1
            if a == 'C':
                coop += 1

            if r == 0:
                first_moves.append(a)

            if match_id in prev_action:
                if prev_action[match_id] != a:
                    switch_count += 1

            prev_action[match_id] = a

            if match_id in prev_opponent:
                prev_b = prev_opponent[match_id]

                if prev_b == 'C':
                    if a == 'C':
                        cc += 1
                    else:
                        dc += 1
                else:
                    if a == 'C':
                        cd += 1
                    else:
                        dd += 1

            prev_opponent[match_id] = b

        total_c = cc + dc
        total_d = cd + dd

        stats[comp] = {
            "coop": coop / total if total else 0,
            "opening": sum(x == 'C' for x in first_moves) / len(first_moves) if first_moves else 0,
            "reciprocity": cc / total_c if total_c else 0,
            "exploit": dc / total_c if total_c else 0,
            "forgiveness": cd / total_d if total_d else 0,
            "punishment": dd / total_d if total_d else 0,
            "switch": switch_count / total if total else 0
        }

    return stats


def get_variability(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor, score FROM (
            SELECT competitor_a AS competitor, score_a AS score FROM matches
            UNION ALL
            SELECT competitor_b AS competitor, score_b AS score FROM matches
        )
    """)

    data = defaultdict(list)
    for comp, score in cur.fetchall():
        data[comp].append(score)

    return {k: pstdev(v) if len(v) > 1 else 0 for k, v in data.items()}


# -----------------------------
# NEW: DEFECTION LOOP ANALYSIS
# -----------------------------
def get_defection_loops(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_a, competitor_b, action_a, action_b, match_id, round
        FROM match_actions
        ORDER BY match_id, round
    """)

    data = defaultdict(list)

    for a_name, b_name, a, b, match_id, r in cur.fetchall():
        data[a_name].append((match_id, r, a, b))
        data[b_name].append((match_id, r, b, a))

    results = {}

    for comp, rows in data.items():
        rows.sort()

        loops = 0
        loop_lengths = []

        in_loop = False
        current_length = 0
        current_match = None

        for match_id, r, a, b in rows:
            if current_match != match_id:
                if in_loop:
                    loop_lengths.append(current_length)
                in_loop = False
                current_length = 0
                current_match = match_id

            if a == 'D' and b == 'D':
                if not in_loop:
                    loops += 1
                    in_loop = True
                    current_length = 1
                else:
                    current_length += 1
            else:
                if in_loop:
                    loop_lengths.append(current_length)
                in_loop = False
                current_length = 0

        if in_loop:
            loop_lengths.append(current_length)

        results[comp] = {
            "loops": loops,
            "avg_length": sum(loop_lengths)/len(loop_lengths) if loop_lengths else 0,
            "max_length": max(loop_lengths) if loop_lengths else 0
        }

    return results


# -----------------------------
# HTML GENERATION
# -----------------------------
def generate_html(iteration, total_lb, avg_lb, avg_rounds,
                  wins, losses, ties,
                  total_score, total_rounds,
                  behavior, variability, mc_rate, defection):

    total_lookup = dict(total_lb)

    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial; max-width: 900px; margin:auto; padding:40px; line-height:1.7; }}
        h1 {{ text-align:center; }}
        h2 {{ border-bottom:2px solid #ddd; padding-bottom:5px; }}
        .agent {{ margin-bottom:35px; padding:15px; border:1px solid #eee; border-radius:8px; }}
        .desc {{ color:#444; font-size:14px; }}
    </style>
    </head>
    <body>

    <h1>Iterated Prisoner's Dilemma Tournament Report</h1>

    <p class="desc">
    This report summarizes the performance and behavioral patterns of agents competing in an 
    Iterated Prisoner's Dilemma tournament. Agents repeatedly choose to either cooperate (C) 
    or defect (D), balancing trust and exploitation over time.
    </p>

    <p>
    <b>Iteration:</b> {iteration}<br>
    <b>Average Match Length:</b> {avg_rounds:.2f} rounds
    </p>

    <h2>Leaderboards</h2>

    <p class="desc">
    <b>Total Score</b> reflects overall accumulated payoff.<br>
    <b>Average Score</b> reflects efficiency per match.
    </p>

    <b>Total Score Ranking</b>
    <ol>{''.join(f"<li>{n}: {s:.2f}</li>" for n,s in total_lb)}</ol>

    <b>Average Score Ranking</b>
    <ol>{''.join(f"<li>{n}: {s:.2f}</li>" for n,s in avg_lb)}</ol>

    <h2>Strategy Profiles</h2>

    <p class="desc">
    Each agent is analyzed based on cooperation rate, responsiveness to opponents, 
    stability, and ability to avoid destructive defection cycles.
    </p>
    """

    for i, (name, avg_score) in enumerate(avg_lb, 1):
        total = total_lookup.get(name, 0)
        beh = behavior.get(name, {})
        std = variability.get(name, 0)
        d = defection.get(name, {})

        rounds = total_rounds.get(name, 1)
        efficiency = total / (rounds * T) if rounds else 0

        coop = beh.get("coop", 0)
        forgiveness = beh.get("forgiveness", 0)
        punishment = beh.get("punishment", 0)

        strategy = classify(coop, punishment, forgiveness)
        stability = consistency_label(std)

        # Narrative interpretations
        if coop > 0.75:
            coop_text = "highly cooperative"
        elif coop > 0.4:
            coop_text = "moderately cooperative"
        else:
            coop_text = "mostly defecting"

        if forgiveness > 0.6:
            forgive_text = "forgives opponents easily"
        elif forgiveness < 0.3:
            forgive_text = "rarely forgives defection"
        else:
            forgive_text = "balances retaliation and forgiveness"

        if d.get("avg_length",0) > 15:
            loop_text = "gets trapped in long mutual defection cycles, which harms long-term payoff."
        elif d.get("avg_length",0) > 5:
            loop_text = "sometimes falls into defection loops but recovers."
        elif d.get("loops",0) > 0:
            loop_text = "encounters brief defection cycles but escapes quickly."
        else:
            loop_text = "successfully avoids mutual defection."

        html += f"""
        <div class="agent">
            <h3>#{i} — {name}</h3>

            <b>Summary</b><br>
            This agent follows a <b>{strategy}</b> approach. It is {coop_text} and {forgive_text}. 
            Overall behavior is <b>{stability}</b> across matches.

            <br><br>

            <b>Performance</b><br>
            Total Score: {total:.2f}<br>
            Average Score: {avg_score:.2f}<br>
            Efficiency: {efficiency:.2f} (score relative to theoretical maximum)<br>
            Variability: {std:.2f} ({stability})

            <br><br>

            <b>Match Outcomes</b><br>
            Wins: {wins[name]} | Losses: {losses[name]} | Ties: {ties[name]}

            <br><br>

            <b>Behavioral Metrics</b><br>
            Cooperation Rate: {coop:.2f}<br>
            Opening Cooperation: {beh.get("opening",0):.2f}<br>
            Mutual Cooperation Rate: {mc_rate.get(name,0):.2f}

            <br><br>

            <b>Conditional Responses</b><br>
            After Cooperation → Cooperate: {beh.get("reciprocity",0):.2f}<br>
            After Cooperation → Defect (Exploit): {beh.get("exploit",0):.2f}<br>
            After Defection → Cooperate (Forgiveness): {forgiveness:.2f}<br>
            After Defection → Defect (Punishment): {punishment:.2f}

            <br><br>

            <b>Defection Loop Behavior</b><br>
            Loop Count: {d.get("loops",0)}<br>
            Average Length: {d.get("avg_length",0):.2f}<br>
            Maximum Length: {d.get("max_length",0)}<br>
            Insight: This agent {loop_text}
        </div>
        """

    html += """
    <h2>Interpretation Guide</h2>
    <p class="desc">
    <b>Cooperation Rate:</b> Fraction of moves where the agent chose cooperation.<br>
    <b>Reciprocity:</b> Likelihood of cooperating after opponent cooperates.<br>
    <b>Forgiveness:</b> Likelihood of returning to cooperation after opponent defects.<br>
    <b>Punishment:</b> Likelihood of continuing to defect after opponent defects.<br>
    <b>Defection Loops:</b> Periods where both players repeatedly defect, reducing payoffs.
    </p>

    </body></html>
    """

    return html


# -----------------------------
# MAIN
# -----------------------------
def generate_report(iteration: int):
    with sqlite3.connect(DB_PATH) as conn:
        total_lb, avg_lb = get_leaderboards(conn)
        avg_rounds = get_avg_rounds(conn)

        wins, losses, ties, total_score, total_rounds = get_match_outcomes(conn)

        behavior = get_behavior_stats(conn)
        variability = get_variability(conn)
        mc_rate = get_mutual_cooperation(conn)
        defection = get_defection_loops(conn)

    html = generate_html(
        iteration,
        total_lb,
        avg_lb,
        avg_rounds,
        wins,
        losses,
        ties,
        total_score,
        total_rounds,
        behavior,
        variability,
        mc_rate,
        defection
    )

    file = f"tournament_report_{iteration}.pdf"
    HTML(string=html).write_pdf(file)

    print(f"Saved: {file}")