import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# CONFIG
# -----------------------------
DB_PATH = Path("tournament_results/tournament.db")

st.set_page_config(page_title="Algorithm Tournament", layout="wide")
st_autorefresh(interval=15000, key="live_refresh")

# -----------------------------
# LOAD DATA
# -----------------------------
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM matches", conn)
    conn.close()
    return df

df = load_data()
df["total_score"] = df["score_a"] + df["score_b"]
df["advantage"] = df["score_a"] - df["score_b"]
df["a_wins"] = (df["score_a"] > df["score_b"]).astype(int)
df["b_wins"] = (df["score_b"] > df["score_a"]).astype(int)

# -----------------------------
# TITLE
# -----------------------------
st.title("Algorithm Tournament Dashboard")
st.caption("Live view of strategies' match-ups from SQLite")

iterations = sorted(df["iteration"].unique())
selected_iter = st.sidebar.multiselect(
    "Select iterations",
    iterations,
    default=iterations
)
df = df[df["iteration"].isin(selected_iter)]

# -----------------------------
# LEADERBOARD
# -----------------------------
st.header("Leaderboard")

# --- TOTAL SCORE (existing) ---
leader_a = df.groupby("competitor_a")["score_a"].sum()
leader_b = df.groupby("competitor_b")["score_b"].sum()
total = leader_a.add(leader_b, fill_value=0).sort_values(ascending=True)

# --- AVERAGE SCORE PER ITERATION ---
count_a = df.groupby("competitor_a")["score_a"].count()
count_b = df.groupby("competitor_b")["score_b"].count()

avg_a = leader_a / count_a
avg_b = leader_b / count_b

avg_total = avg_a.add(avg_b, fill_value=0).sort_values(ascending=True)

# -----------------------------
# FIGURE WITH TWO LEADERBOARDS
# -----------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_alpha(0)

# --- LEFT: TOTAL ---
ax1.set_facecolor("none")
colors1 = sns.color_palette("viridis", len(total))

ax1.barh(total.index, total.values, color=colors1, edgecolor="none")
ax1.set_title("Total Score", color="white")
ax1.tick_params(colors="white")

# --- RIGHT: AVERAGE ---
ax2.set_facecolor("none")
colors2 = sns.color_palette("magma", len(avg_total))

ax2.barh(avg_total.index, avg_total.values, color=colors2, edgecolor="none")
ax2.set_title("Average Score per Iteration", color="white")
ax2.tick_params(colors="white")

plt.tight_layout()
st.pyplot(fig)

# -----------------------------
# MATCHUPS HEATMAP
# -----------------------------
st.header("Matchups (Win Advantage Heatmap)")
win_matrix = df.pivot_table(
    index="competitor_a",
    columns="competitor_b",
    values="a_wins",
    aggfunc="mean",
    fill_value=0
)

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(
    win_matrix,
    cmap="RdYlGn",
    vmin=0,
    vmax=1,
    center=0.5,
    linewidths=0.5,
    ax=ax
)
ax.set_title("Probability that A beats B")
st.pyplot(fig)

# -----------------------------
# PERFORMANCE OVER TIME
# -----------------------------
st.header("Performance Over Time")

# Group by iteration and competitors, and sum the scores for both competitors
evolution = df.groupby(["iteration", "competitor_a", "competitor_b"])[["score_a", "score_b"]].sum().reset_index()

# Pivot the dataframe for each competitor's performance using pivot_table to handle duplicates
pivot_a = evolution.pivot_table(
    index="iteration",
    columns="competitor_a",
    values="score_a",
    aggfunc="sum",
    fill_value=0
)

pivot_b = evolution.pivot_table(
    index="iteration",
    columns="competitor_b",
    values="score_b",
    aggfunc="sum",
    fill_value=0
)

# Smooth the data with a rolling window of size 2
pivot_a = pivot_a.rolling(window=2).mean()
pivot_b = pivot_b.rolling(window=2).mean()

# Combine the two pivot tables (competitor_a and competitor_b)
combined_pivot = pivot_a.add(pivot_b, fill_value=0)

# Plot the results for both competitors
st.line_chart(combined_pivot)

# -----------------------------
# STRATEGY DOMINANCE SCORE
# -----------------------------
st.header("Strategy Dominance Score")
dominance = df.groupby("competitor_a").agg({
    "advantage": "mean",
    "a_wins": "mean",
    "total_score": "mean"
}).rename(columns={
    "advantage": "avg_advantage",
    "a_wins": "win_rate",
    "total_score": "efficiency"
})
dominance = dominance.sort_values("win_rate", ascending=False)
st.dataframe(dominance, width='stretch')

# -----------------------------
# INTERACTION GRAPH
# -----------------------------
st.header("Interaction Graph")
edge_weights = {}
for _, row in df.iterrows():
    if row["score_a"] > row["score_b"]:
        a, b = row["competitor_a"], row["competitor_b"]
        w = row["score_a"] - row["score_b"]
    else:
        a, b = row["competitor_b"], row["competitor_a"]
        w = row["score_b"] - row["score_a"]
    edge_weights[(a, b)] = edge_weights.get((a, b), 0) + w

net = Network(
    height="600px",
    width="100%",
    bgcolor="#0e1117",
    font_color="white",
    directed=True
)
net.force_atlas_2based(gravity=-50)

nodes = set()
for (a, b), w in edge_weights.items():
    if a not in nodes:
        net.add_node(a, label=a)
        nodes.add(a)
    if b not in nodes:
        net.add_node(b, label=b)
        nodes.add(b)
    net.add_edge(a, b, value=float(w), title=f"Advantage: {w:.1f}")

net_html = net.generate_html()
components.html(net_html, height=650)

# -----------------------------
# MATCH ACTION ANALYSIS
# -----------------------------
st.header("Action Analysis per Competitor")
conn = sqlite3.connect(DB_PATH)
actions_df = pd.read_sql_query("SELECT * FROM match_actions", conn)
conn.close()

action_summary = actions_df.groupby(["competitor_a", "action_a"]).size().reset_index(name="count_a")
action_summary_b = actions_df.groupby(["competitor_b", "action_b"]).size().reset_index(name="count_b")

actions_combined = pd.merge(
    action_summary.rename(columns={"competitor_a": "competitor", "action_a": "action", "count_a": "count"}),
    action_summary_b.rename(columns={"competitor_b": "competitor", "action_b": "action", "count_b": "count"}),
    on=["competitor", "action"],
    how="outer"
).fillna(0)

actions_combined["total_count"] = actions_combined["count_x"] + actions_combined["count_y"]
actions_combined = actions_combined[["competitor", "action", "total_count"]].sort_values(["competitor", "total_count"], ascending=[True, False])
st.dataframe(actions_combined, width='stretch')

# -----------------------------
# FIRST-ROUND ACTIONS PIE CHART
# -----------------------------
st.header("First-Round Cooperation vs Defection (Grid)")

# Filter only the first round (adjust 0 or 1 depending on your DB)
first_round_df = actions_df[actions_df["round"] == 0]

# Count actions per competitor
def first_round_counts(df, competitor_col, action_col):
    return df.groupby([competitor_col, action_col]).size().reset_index(name="count")

counts_a = first_round_counts(first_round_df, "competitor_a", "action_a")
counts_a = counts_a.rename(columns={"competitor_a": "competitor", "action_a": "action"})

counts_b = first_round_counts(first_round_df, "competitor_b", "action_b")
counts_b = counts_b.rename(columns={"competitor_b": "competitor", "action_b": "action"})

first_round_counts_combined = pd.concat([counts_a, counts_b])
first_round_counts_combined = first_round_counts_combined.groupby(["competitor", "action"])["count"].sum().reset_index()

# Grid layout
competitors = first_round_counts_combined["competitor"].unique()
n_cols = 5
cols = st.columns(n_cols)

for i, comp in enumerate(competitors):
    comp_data = first_round_counts_combined[first_round_counts_combined["competitor"] == comp]
    
    # Small, uniform figure with transparent background
    fig, ax = plt.subplots(figsize=(3, 3), facecolor="none")
    wedges, texts, autotexts = ax.pie(
        comp_data["count"],
        labels=comp_data["action"],
        autopct="%1.1f%%",
        startangle=90,
        colors=sns.color_palette("Set2", len(comp_data)),
        textprops={'color':"white"}
    )
    
    # Draw algorithm name in center
    ax.text(0, 0, comp, color='white', ha='center', va='center', fontsize=10, weight='bold')
    
    ax.axis("equal")  # Keep circle shape
    
    col = cols[i % n_cols]  # choose column
    col.pyplot(fig, transparent=True)
    
    # Wrap to new row after n_cols
    if (i + 1) % n_cols == 0 and i + 1 < len(competitors):
        cols = st.columns(n_cols)

# -----------------------------
# RAW DATA
# -----------------------------
with st.expander("Raw match data"):
    st.dataframe(df)