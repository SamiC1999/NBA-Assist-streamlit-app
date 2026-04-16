"""
query_engine.py
---------------
Object-oriented query layer over the assist DiGraph.
All four required interactions live here as clean methods.

Usage:
    from query_engine import AssistQueryEngine
    engine = AssistQueryEngine(G)          # G is a nx.DiGraph from graph_builder
    engine.top_assist_partners("LeBron James")
    engine.players_who_assisted("Anthony Davis")
    engine.player_stats("Nikola Jokic")
    engine.top_10_assisters()
"""

from __future__ import annotations
import networkx as nx
from dataclasses import dataclass, field
from typing import Optional


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class PlayerStats:
    player_id: int
    name: str
    team: str
    games_played: int
    ast_total: int
    ast_per_game: float
    pts_total: int
    pts_per_game: float
    reb_total: int
    assists_given_total: int    # out-degree weighted
    assists_received_total: int # in-degree weighted
    top_partners: list[tuple[str, int]] = field(default_factory=list)

    def display(self) -> str:
        lines = [
            f"  Player:             {self.name}",
            f"  Team:               {self.team}",
            f"  Games Played:       {self.games_played}",
            f"  Assists Given:      {self.ast_total}  ({self.ast_per_game}/gm)",
            f"  Assists Received:   {self.assists_received_total}",
            f"  Points:             {self.pts_total}  ({self.pts_per_game}/gm)",
            f"  Rebounds:           {self.reb_total}",
        ]
        if self.top_partners:
            lines.append("  Top Assist Partners:")
            for name, w in self.top_partners:
                lines.append(f"      → {name}  ({w} est. assists)")
        return "\n".join(lines)


@dataclass
class AssistRelationship:
    assister_name: str
    receiver_name: str
    weight: int   # estimated assists

    def __str__(self) -> str:
        return f"{self.assister_name} → {self.receiver_name}  ({self.weight} est. assists)"


# ── Query Engine ──────────────────────────────────────────────────────────────

class AssistQueryEngine:
    """
    Wraps a NetworkX DiGraph and exposes the four required interactions
    plus helper utilities.
    """

    def __init__(self, G: nx.DiGraph):
        self.G = G
        # Build a fast name→id lookup (lowercased for case-insensitive search)
        self._name_index: dict[str, int] = {
            attrs["name"].lower(): nid
            for nid, attrs in G.nodes(data=True)
        }

    # ── Name resolution ───────────────────────────────────────────────────────

    def find_player_id(self, name_query: str) -> Optional[int]:
        """
        Case-insensitive partial name match. Returns player_id or None.
        If multiple matches, returns the one with the most assists (best known).
        """
        query = name_query.lower().strip()

        # Exact match first
        if query in self._name_index:
            return self._name_index[query]

        # Partial match
        matches = [
            (nid, self.G.nodes[nid]["ast_total"])
            for name, nid in self._name_index.items()
            if query in name
        ]
        if not matches:
            return None
        # Return the most prolific assister among matches
        return sorted(matches, key=lambda x: x[1], reverse=True)[0][0]

    def _node(self, pid: int) -> dict:
        return self.G.nodes[pid]

    # ── Interaction 1: Top 5 assist partners ──────────────────────────────────

    def top_assist_partners(self, name_query: str, k: int = 5) -> list[AssistRelationship]:
        """
        Search for a player and return their top-k assist recipients.
        These are players they most often assisted.
        """
        pid = self.find_player_id(name_query)
        if pid is None:
            return []

        out_edges = [
            (v, d["weight"])
            for _, v, d in self.G.out_edges(pid, data=True)
        ]
        top = sorted(out_edges, key=lambda x: x[1], reverse=True)[:k]

        return [
            AssistRelationship(
                assister_name=self._node(pid)["name"],
                receiver_name=self._node(v)["name"],
                weight=w,
            )
            for v, w in top
        ]

    # ── Interaction 2: Who assisted a specific player ─────────────────────────

    def players_who_assisted(self, name_query: str) -> list[AssistRelationship]:
        """
        Return all players who assisted a given player (in-edges), sorted by
        assist weight descending.
        """
        pid = self.find_player_id(name_query)
        if pid is None:
            return []

        in_edges = [
            (u, d["weight"])
            for u, _, d in self.G.in_edges(pid, data=True)
        ]
        top = sorted(in_edges, key=lambda x: x[1], reverse=True)

        return [
            AssistRelationship(
                assister_name=self._node(u)["name"],
                receiver_name=self._node(pid)["name"],
                weight=w,
            )
            for u, w in top
        ]

    # ── Interaction 3: Basic stats for a player ───────────────────────────────

    def player_stats(self, name_query: str) -> Optional[PlayerStats]:
        """
        Return a PlayerStats object with assists given/received and basic stats.
        """
        pid = self.find_player_id(name_query)
        if pid is None:
            return None

        attrs = self._node(pid)

        assists_given = sum(
            d["weight"] for _, _, d in self.G.out_edges(pid, data=True)
        )
        assists_received = sum(
            d["weight"] for _, _, d in self.G.in_edges(pid, data=True)
        )

        top_partners = sorted(
            [(self._node(v)["name"], d["weight"])
             for _, v, d in self.G.out_edges(pid, data=True)],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return PlayerStats(
            player_id=pid,
            name=attrs["name"],
            team=attrs["team_abbr"],
            games_played=attrs["games_played"],
            ast_total=attrs["ast_total"],
            ast_per_game=attrs["ast_per_game"],
            pts_total=attrs["pts_total"],
            pts_per_game=attrs["pts_per_game"],
            reb_total=attrs["reb_total"],
            assists_given_total=assists_given,
            assists_received_total=assists_received,
            top_partners=top_partners,
        )

    # ── Interaction 4: Top 10 players by total assists given ──────────────────

    def top_10_assisters(self) -> list[tuple[int, str, str, int, float]]:
        """
        Return top 10 players ranked by ast_total (season total from API).
        Returns list of (rank, name, team, ast_total, ast_per_game).
        """
        ranked = sorted(
            [
                (
                    nid,
                    attrs["name"],
                    attrs["team_abbr"],
                    attrs["ast_total"],
                    attrs["ast_per_game"],
                )
                for nid, attrs in self.G.nodes(data=True)
                if attrs.get("ast_total", 0) > 0
            ],
            key=lambda x: x[3],
            reverse=True,
        )[:10]

        return [
            (i + 1, name, team, ast, apg)
            for i, (_, name, team, ast, apg) in enumerate(ranked)
        ]

    # ── Bonus: centrality analysis ────────────────────────────────────────────

    def playmaker_centrality(self, top_n: int = 10) -> list[tuple[str, float]]:
        """
        PageRank-based playmaker ranking — measures influence in the assist network.
        Falls back to a pure-Python power-iteration if scipy is not installed.
        High PageRank = many teammates rely on this player to facilitate.
        """
        try:
            pr = nx.pagerank(self.G, weight="weight")
        except Exception:
            # scipy unavailable — use pure-Python power iteration fallback
            pr = nx.pagerank_numpy(self.G) if hasattr(nx, "pagerank_numpy") else                  self._pagerank_fallback()
        ranked = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [(self._node(pid)["name"], round(score, 5)) for pid, score in ranked]

    def _pagerank_fallback(self, alpha: float = 0.85, max_iter: int = 100) -> dict:
        """Pure-Python power-iteration PageRank — no scipy needed."""
        nodes = list(self.G.nodes())
        n = len(nodes)
        if n == 0:
            return {}
        pr = {node: 1.0 / n for node in nodes}
        out_weight = {
            node: sum(d.get("weight", 1) for _, _, d in self.G.out_edges(node, data=True))
            for node in nodes
        }
        for _ in range(max_iter):
            new_pr = {}
            dangling_sum = sum(pr[node] for node in nodes if out_weight[node] == 0)
            for node in nodes:
                rank = (1 - alpha) / n + alpha * dangling_sum / n
                for pred, _, data in self.G.in_edges(node, data=True):
                    w = data.get("weight", 1)
                    if out_weight[pred] > 0:
                        rank += alpha * pr[pred] * w / out_weight[pred]
                new_pr[node] = rank
            pr = new_pr
        return pr

    def assist_path(self, from_name: str, to_name: str) -> Optional[list[str]]:
        """
        Shortest directed path of assists from one player to another
        (e.g., multi-hop passing chain exploration).
        Returns list of player names or None if no path exists.
        """
        src = self.find_player_id(from_name)
        dst = self.find_player_id(to_name)
        if src is None or dst is None:
            return None
        try:
            path_ids = nx.shortest_path(self.G, src, dst, weight=None)
            return [self._node(pid)["name"] for pid in path_ids]
        except nx.NetworkXNoPath:
            return None


# ── Smoke-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from graph_builder import AssistGraphBuilder

    print("Building graph …")
    G = AssistGraphBuilder().build(season=2023)
    engine = AssistQueryEngine(G)

    print("\n── Top 10 Assisters ──")
    for rank, name, team, ast, apg in engine.top_10_assisters():
        print(f"  {rank:2}. {name:<22} {team:<5} {ast:>4} ast  ({apg}/gm)")

    # Use first top assister for further tests
    top_player = engine.top_10_assisters()[0][1]

    print(f"\n── Top 5 Assist Partners for {top_player} ──")
    for rel in engine.top_assist_partners(top_player):
        print(f"  {rel}")

    print(f"\n── Players Who Assisted {top_player} ──")
    for rel in engine.players_who_assisted(top_player)[:5]:
        print(f"  {rel}")

    print(f"\n── Player Stats: {top_player} ──")
    stats = engine.player_stats(top_player)
    if stats:
        print(stats.display())
