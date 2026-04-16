"""
graph_visualizer.py
-------------------
Produces matplotlib figures of the assist network.
Three views are available:
  1. full_network()     — full graph, nodes sized by assists, colored by team
  2. team_subgraph()    — one team's internal assist flows
  3. top_flow_graph()   — only the heaviest assist edges in the whole league

All functions return a matplotlib Figure so Streamlit can render them with
st.pyplot(fig) without any display side-effects.
"""

from __future__ import annotations
import math
from typing import Optional

import networkx as nx
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — safe in Streamlit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba


# ── Team colour palette (NBA brand colours, 30 teams) ────────────────────────
TEAM_COLORS: dict[str, str] = {
    "ATL": "#C1D32F", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160",
    "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#0E2240",
    "DET": "#C8102E", "GSW": "#1D428A", "HOU": "#CE1141", "IND": "#002D62",
    "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9", "MIA": "#98002E",
    "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#006BB6",
    "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160",
    "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141",
    "UTA": "#002B5C", "WAS": "#002B5C",
}
DEFAULT_COLOR = "#888888"


def _node_colors(G: nx.DiGraph, nodes: list) -> list[str]:
    return [TEAM_COLORS.get(G.nodes[n].get("team_abbr", ""), DEFAULT_COLOR) for n in nodes]


def _node_sizes(G: nx.DiGraph, nodes: list, scale: float = 1.0) -> list[float]:
    """Size nodes proportionally to their total assists."""
    asts = [G.nodes[n].get("ast_total", 1) for n in nodes]
    max_a = max(asts) if asts else 1
    return [80 + 1200 * (a / max_a) * scale for a in asts]


def _edge_weights(G: nx.DiGraph, edges) -> list[float]:
    ws = [G[u][v].get("weight", 1) for u, v in edges]
    max_w = max(ws) if ws else 1
    return [0.3 + 3.5 * (w / max_w) for w in ws]


# ── 1. Full network ───────────────────────────────────────────────────────────

def full_network(
    G: nx.DiGraph,
    top_n_edges: int = 60,
    figsize: tuple = (14, 10),
    title: str = "NBA Assist Network",
) -> plt.Figure:
    """
    Draw the full assist network.  Only the top_n_edges heaviest edges are
    shown to avoid a hairball.  Nodes are coloured by team.
    """
    # Keep only heavy edges to avoid clutter
    all_edges = sorted(G.edges(data=True), key=lambda e: e[2].get("weight", 0), reverse=True)
    shown_edges = [(u, v) for u, v, _ in all_edges[:top_n_edges]]
    active_nodes = list({n for e in shown_edges for n in e})

    sub = G.subgraph(active_nodes)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#0d1117")
    ax.set_facecolor("#0d1117")

    pos = nx.spring_layout(sub, k=2.2 / math.sqrt(max(len(active_nodes), 1)),
                           seed=42, weight="weight")

    colors = _node_colors(sub, list(sub.nodes()))
    sizes  = _node_sizes(sub, list(sub.nodes()))
    widths = _edge_weights(sub, shown_edges)

    nx.draw_networkx_edges(
        sub, pos,
        edgelist=shown_edges,
        width=widths,
        edge_color="#f97316",
        alpha=0.35,
        arrows=True,
        arrowsize=8,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.08",
        ax=ax,
    )
    nx.draw_networkx_nodes(
        sub, pos,
        node_color=colors,
        node_size=sizes,
        alpha=0.92,
        ax=ax,
    )

    # Labels only for high-assist nodes
    ast_threshold = sorted(
        [G.nodes[n].get("ast_total", 0) for n in active_nodes], reverse=True
    )[min(14, len(active_nodes) - 1)]
    label_nodes = {
        n: G.nodes[n]["name"].split()[-1]          # last name only
        for n in active_nodes
        if G.nodes[n].get("ast_total", 0) >= ast_threshold
    }
    nx.draw_networkx_labels(
        sub, pos,
        labels=label_nodes,
        font_size=7,
        font_color="white",
        font_weight="bold",
        ax=ax,
    )

    # Team legend (teams present in graph)
    present_teams = {G.nodes[n].get("team_abbr", "") for n in active_nodes}
    patches = [
        mpatches.Patch(color=TEAM_COLORS.get(t, DEFAULT_COLOR), label=t)
        for t in sorted(present_teams)
        if t
    ]
    ax.legend(
        handles=patches,
        loc="lower left",
        ncol=5,
        fontsize=6,
        framealpha=0.2,
        labelcolor="white",
        facecolor="#161b22",
        edgecolor="#30363d",
    )

    ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()
    return fig


# ── 2. Team subgraph ──────────────────────────────────────────────────────────

def team_subgraph(
    G: nx.DiGraph,
    team_abbr: str,
    figsize: tuple = (9, 7),
) -> Optional[plt.Figure]:
    """
    Draw the internal assist network for one team.
    Returns None if the team has fewer than 2 players.
    """
    members = [n for n, d in G.nodes(data=True) if d.get("team_abbr") == team_abbr]
    if len(members) < 2:
        return None

    sub = G.subgraph(members)
    team_color = TEAM_COLORS.get(team_abbr, DEFAULT_COLOR)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#0d1117")
    ax.set_facecolor("#0d1117")

    pos = nx.circular_layout(sub)

    edge_list = list(sub.edges())
    widths = _edge_weights(sub, edge_list) if edge_list else []
    sizes  = _node_sizes(sub, members, scale=1.4)

    if edge_list:
        nx.draw_networkx_edges(
            sub, pos,
            edgelist=edge_list,
            width=widths,
            edge_color=team_color,
            alpha=0.6,
            arrows=True,
            arrowsize=12,
            connectionstyle="arc3,rad=0.12",
            ax=ax,
        )

    nx.draw_networkx_nodes(
        sub, pos,
        node_color=team_color,
        node_size=sizes,
        alpha=0.9,
        ax=ax,
    )

    labels = {n: G.nodes[n]["name"].split()[-1] for n in members}
    nx.draw_networkx_labels(sub, pos, labels=labels, font_size=9,
                            font_color="white", font_weight="bold", ax=ax)

    ax.set_title(f"{team_abbr} — Internal Assist Network",
                 color="white", fontsize=13, fontweight="bold", pad=10)
    ax.axis("off")
    plt.tight_layout()
    return fig


# ── 3. Top-flow graph ─────────────────────────────────────────────────────────

def top_flow_graph(
    G: nx.DiGraph,
    top_n: int = 15,
    figsize: tuple = (11, 8),
) -> plt.Figure:
    """
    Highlight the top_n heaviest assist relationships league-wide.
    Uses a Kamada-Kawai layout for clarity.
    """
    top_edges = sorted(G.edges(data=True), key=lambda e: e[2].get("weight", 0), reverse=True)[:top_n]
    active_nodes = list({n for u, v, _ in top_edges for n in (u, v)})
    sub = G.subgraph(active_nodes)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#0d1117")
    ax.set_facecolor("#0d1117")

    try:
        pos = nx.kamada_kawai_layout(sub, weight="weight")
    except Exception:
        pos = nx.spring_layout(sub, seed=42)

    edge_list = [(u, v) for u, v, _ in top_edges]
    weights   = [d.get("weight", 1) for _, _, d in top_edges]
    max_w     = max(weights)
    widths    = [0.5 + 5.0 * (w / max_w) for w in weights]
    alphas    = [0.3 + 0.65 * (w / max_w) for w in weights]

    # Draw edges one by one so each gets its own alpha
    for (u, v), wd, al in zip(edge_list, widths, alphas):
        nx.draw_networkx_edges(
            sub, pos,
            edgelist=[(u, v)],
            width=wd,
            edge_color="#f97316",
            alpha=al,
            arrows=True,
            arrowsize=14,
            connectionstyle="arc3,rad=0.1",
            ax=ax,
        )

    colors = _node_colors(sub, active_nodes)
    sizes  = _node_sizes(sub, active_nodes, scale=1.2)
    nx.draw_networkx_nodes(sub, pos, node_color=colors, node_size=sizes, alpha=0.95, ax=ax)

    labels = {n: G.nodes[n]["name"].split()[-1] for n in active_nodes}
    nx.draw_networkx_labels(sub, pos, labels=labels, font_size=8,
                            font_color="white", font_weight="bold", ax=ax)

    ax.set_title(f"Top {top_n} Assist Flows — League Wide",
                 color="white", fontsize=13, fontweight="bold", pad=10)
    ax.axis("off")
    plt.tight_layout()
    return fig


# ── Smoke-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from demo_data import build_demo_graph

    G = build_demo_graph()
    print("Testing full_network …")
    fig = full_network(G)
    fig.savefig("/tmp/test_full.png", dpi=80)
    print("  saved /tmp/test_full.png")

    print("Testing team_subgraph DEN …")
    fig2 = team_subgraph(G, "DEN")
    fig2.savefig("/tmp/test_den.png", dpi=80)
    print("  saved /tmp/test_den.png")

    print("Testing top_flow_graph …")
    fig3 = top_flow_graph(G, top_n=12)
    fig3.savefig("/tmp/test_flow.png", dpi=80)
    print("  saved /tmp/test_flow.png")

    print("graph_visualizer.py OK")
