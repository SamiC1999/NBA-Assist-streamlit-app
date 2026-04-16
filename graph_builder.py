"""
graph_builder.py
----------------
Builds the assist DiGraph using nba_api — completely FREE, no API key needed.
Pulls data directly from stats.nba.com via the nba_api Python package.

One call to LeagueDashPlayerStats returns every player's season stats.
"""

from __future__ import annotations
import os, time, pickle
from collections import defaultdict
from typing import Optional, Callable
import networkx as nx

GRAPH_CACHE_DIR = "cache/graphs"

# Season format for nba_api: year -> "YYYY-YY"
def _season_str(year: int) -> str:
    return f"{year}-{str(year + 1)[-2:]}"   # 2023 -> "2023-24"


class AssistGraphBuilder:

    def __init__(self, api_key: Optional[str] = None):
        # api_key not needed for nba_api — kept for interface compatibility
        os.makedirs(GRAPH_CACHE_DIR, exist_ok=True)

    def _cache_path(self, season: int) -> str:
        return os.path.join(GRAPH_CACHE_DIR, f"assist_graph_{season}.pkl")

    def _load_cache(self, season: int):
        p = self._cache_path(season)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return pickle.load(f)
        return None

    def _save_cache(self, G, season: int):
        with open(self._cache_path(season), "wb") as f:
            pickle.dump(G, f)

    def _assign_edges(self, G):
        """Distribute each player's assists across teammates by scoring share."""
        teams = defaultdict(list)
        for nid, d in G.nodes(data=True):
            teams[d["team_abbr"]].append(nid)
        for abbr, members in teams.items():
            pts_map = {p: G.nodes[p]["pts_total"] for p in members
                       if G.nodes[p]["pts_total"] > 0}
            if not pts_map:
                continue
            for assister in members:
                n_ast = G.nodes[assister]["ast_total"]
                if n_ast == 0:
                    continue
                receivers = {p: v for p, v in pts_map.items() if p != assister}
                if not receivers:
                    continue
                total = sum(receivers.values())
                for receiver, pts in receivers.items():
                    w = round(n_ast * pts / total)
                    if w > 0:
                        if G.has_edge(assister, receiver):
                            G[assister][receiver]["weight"] += w
                        else:
                            G.add_edge(assister, receiver, weight=w)

    def build(self, season: int, force_rebuild: bool = False,
              progress_cb: Optional[Callable[[str], None]] = None) -> nx.DiGraph:

        def log(msg):
            print(msg)
            if progress_cb:
                progress_cb(msg)

        if not force_rebuild:
            cached = self._load_cache(season)
            if cached is not None:
                log(f"✓ Loaded from cache — {cached.number_of_nodes()} players, "
                    f"{cached.number_of_edges()} edges")
                return cached

        # ── Import nba_api ────────────────────────────────────────────────────
        try:
            from nba_api.stats.endpoints import leaguedashplayerstats
        except ImportError:
            raise ImportError(
                "nba_api not installed. Run: pip install nba_api"
            )

        season_str = _season_str(season)
        log(f"Step 1/2 — Fetching {season_str} player stats from stats.nba.com…")
        log("  (this is a single request — usually takes 5-15 seconds)")

        time.sleep(1)   # polite pause before hitting stats.nba.com
        try:
            # Try Totals mode first; fall back to PerGame if param name differs
            try:
                endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
                    season=season_str,
                    per_mode_simple="Totals",
                    timeout=60,
                )
            except TypeError:
                try:
                    endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
                        season=season_str,
                        per_mode_type="Totals",
                        timeout=60,
                    )
                except TypeError:
                    # Oldest versions: no per_mode param at all (returns PerGame)
                    endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
                        season=season_str,
                        timeout=60,
                    )
            df = endpoint.get_data_frames()[0]
            # If we got PerGame data instead of Totals, we still handle it below
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch from stats.nba.com: {e}\n"
                "Check your internet connection and try again."
            )

        log(f"  → {len(df)} player records received")

        # ── Build graph ───────────────────────────────────────────────────────
        log("Step 2/2 — Building assist graph…")
        G = nx.DiGraph()
        G.graph["season"] = season

        # Detect if we got Totals or PerGame data by checking AST magnitude
        # Totals: AST will be hundreds. PerGame: AST will be 0-15.
        # We normalise everything to totals + per_game.
        sample_ast = df["AST"].median() if "AST" in df.columns else 0
        is_per_game = sample_ast < 20   # per-game averages are always < 20

        log(f"  data mode: {'PerGame averages' if is_per_game else 'Season totals'}")

        for _, row in df.iterrows():
            gp = int(row.get("GP", 0) or 0)
            if gp < 10:
                continue

            pid  = int(row["PLAYER_ID"])
            name = str(row["PLAYER_NAME"])
            team = str(row.get("TEAM_ABBREVIATION", "?"))

            raw_ast = float(row.get("AST", 0) or 0)
            raw_pts = float(row.get("PTS", 0) or 0)
            raw_reb = float(row.get("REB", 0) or 0)

            if is_per_game:
                ast_pg  = round(raw_ast, 2)
                pts_pg  = round(raw_pts, 2)
                ast     = round(raw_ast * gp)
                pts     = round(raw_pts * gp)
                reb     = round(raw_reb * gp)
            else:
                ast     = int(raw_ast)
                pts     = int(raw_pts)
                reb     = int(raw_reb)
                ast_pg  = round(raw_ast / gp, 2) if gp else 0
                pts_pg  = round(raw_pts / gp, 2) if gp else 0

            G.add_node(pid,
                name         = name,
                team_abbr    = team,
                ast_total    = ast,
                ast_per_game = ast_pg,
                pts_total    = pts,
                pts_per_game = pts_pg,
                reb_total    = reb,
                games_played = gp,
            )

        self._assign_edges(G)
        self._save_cache(G, season)
        log(f"✓ Done — {G.number_of_nodes()} players, {G.number_of_edges()} edges")
        return G

    def merge_seasons(self, seasons):
        graphs = [self.build(s) for s in seasons]
        merged = nx.DiGraph()
        for G in graphs:
            for nid, attrs in G.nodes(data=True):
                if nid in merged:
                    for k in ("ast_total","pts_total","reb_total","games_played"):
                        merged.nodes[nid][k] = merged.nodes[nid].get(k,0) + attrs.get(k,0)
                else:
                    merged.add_node(nid, **attrs)
            for u, v, data in G.edges(data=True):
                if merged.has_edge(u, v):
                    merged[u][v]["weight"] += data.get("weight", 0)
                else:
                    merged.add_edge(u, v, **data)
        return merged
