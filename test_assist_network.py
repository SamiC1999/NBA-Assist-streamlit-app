"""
test_assist_network.py
----------------------
Test suite for the NBA Assist Network project.
Run with:  python3 -m pytest test_assist_network.py -v

Tests serve as living documentation:
  - What a graph looks like after construction
  - What each of the four interactions guarantees
  - Edge cases: unknown players, disconnected nodes, empty queries
  - Graph properties: directed edges, weighted, no self-loops
  - OOP contracts: return types, data integrity
"""

import pytest
import networkx as nx

from demo_data import build_demo_graph
from query_engine import AssistQueryEngine, PlayerStats, AssistRelationship


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def graph():
    """Shared graph for all tests — built once from demo data."""
    return build_demo_graph(season=2023)


@pytest.fixture(scope="module")
def engine(graph):
    """Shared query engine for all tests."""
    return AssistQueryEngine(graph)


# ── Graph structure tests ─────────────────────────────────────────────────────

class TestGraphStructure:
    """The graph must be a directed, weighted network with valid node data."""

    def test_graph_is_directed(self, graph):
        assert isinstance(graph, nx.DiGraph), \
            "Graph must be directed (DiGraph) — assists have a giver and receiver"

    def test_graph_has_nodes(self, graph):
        assert graph.number_of_nodes() > 0, "Graph must contain player nodes"

    def test_graph_has_edges(self, graph):
        assert graph.number_of_edges() > 0, "Graph must contain assist edges"

    def test_edges_have_positive_weight(self, graph):
        for u, v, data in graph.edges(data=True):
            assert data.get("weight", 0) > 0, \
                f"Edge {u}->{v} must have positive weight"

    def test_no_self_loops(self, graph):
        for node in graph.nodes():
            assert not graph.has_edge(node, node), \
                f"Player {node} cannot assist themselves"

    def test_nodes_have_required_attributes(self, graph):
        required = {"name", "team_abbr", "ast_total", "pts_total",
                    "reb_total", "games_played", "ast_per_game"}
        for nid, attrs in graph.nodes(data=True):
            missing = required - set(attrs.keys())
            assert not missing, f"Node {nid} missing attributes: {missing}"

    def test_node_stats_are_non_negative(self, graph):
        for nid, attrs in graph.nodes(data=True):
            assert attrs["ast_total"]    >= 0
            assert attrs["pts_total"]    >= 0
            assert attrs["games_played"] >= 0

    def test_season_stored_in_graph(self, graph):
        assert "season" in graph.graph, "Graph must store season metadata"


# ── Interaction 1: top_assist_partners ───────────────────────────────────────

class TestTopAssistPartners:
    """Search a player and return their top-5 assist recipients."""

    def test_returns_five_results_for_known_player(self, engine):
        results = engine.top_assist_partners("Jokic")
        assert len(results) == 5, "Must return exactly 5 assist partners"

    def test_returns_assist_relationship_objects(self, engine):
        results = engine.top_assist_partners("Jokic")
        for r in results:
            assert isinstance(r, AssistRelationship)

    def test_results_sorted_by_weight_descending(self, engine):
        results = engine.top_assist_partners("Jokic")
        weights = [r.weight for r in results]
        assert weights == sorted(weights, reverse=True), \
            "Partners must be sorted highest assists first"

    def test_all_weights_positive(self, engine):
        results = engine.top_assist_partners("LeBron")
        for r in results:
            assert r.weight > 0

    def test_assister_name_is_consistent(self, engine):
        results = engine.top_assist_partners("Haliburton")
        names = {r.assister_name for r in results}
        assert len(names) == 1, "All results must share the same assister name"

    def test_unknown_player_returns_empty(self, engine):
        results = engine.top_assist_partners("ZZZNOTAPLAYER999")
        assert results == [], "Unknown player must return empty list, not error"

    def test_partial_name_match_works(self, engine):
        results = engine.top_assist_partners("Young")
        assert len(results) > 0, "Partial last-name search must work"

    def test_case_insensitive_search(self, engine):
        lower = engine.top_assist_partners("jokic")
        upper = engine.top_assist_partners("JOKIC")
        assert len(lower) == len(upper) == 5


# ── Interaction 2: players_who_assisted ──────────────────────────────────────

class TestPlayersWhoAssisted:
    """Return all players who directed assists toward a given player."""

    def test_returns_list_of_relationships(self, engine):
        results = engine.players_who_assisted("Jamal Murray")
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, AssistRelationship)

    def test_receiver_name_is_consistent(self, engine):
        results = engine.players_who_assisted("Anthony Davis")
        if results:
            names = {r.receiver_name for r in results}
            assert len(names) == 1

    def test_sorted_by_weight_descending(self, engine):
        results = engine.players_who_assisted("Jamal Murray")
        if len(results) > 1:
            weights = [r.weight for r in results]
            assert weights == sorted(weights, reverse=True)

    def test_unknown_player_returns_empty(self, engine):
        results = engine.players_who_assisted("ZZZNOTAPLAYER999")
        assert results == []

    def test_high_scorer_has_assisters(self, engine):
        """A prolific scorer should appear as a receiver in the graph."""
        results = engine.players_who_assisted("Anthony Davis")
        assert len(results) > 0, "High scorer must have recorded assisters"


# ── Interaction 3: player_stats ───────────────────────────────────────────────

class TestPlayerStats:
    """Return a full stat profile for any player."""

    def test_returns_player_stats_object(self, engine):
        stats = engine.player_stats("LeBron")
        assert isinstance(stats, PlayerStats)

    def test_unknown_player_returns_none(self, engine):
        stats = engine.player_stats("ZZZNOTAPLAYER999")
        assert stats is None

    def test_assists_given_equals_node_total(self, engine, graph):
        stats = engine.player_stats("Nikola Jokic")
        pid   = engine.find_player_id("Nikola Jokic")
        assert stats.ast_total == graph.nodes[pid]["ast_total"]

    def test_assists_received_is_non_negative(self, engine):
        stats = engine.player_stats("LeBron")
        assert stats.assists_received_total >= 0

    def test_top_partners_sorted_descending(self, engine):
        stats = engine.player_stats("Nikola Jokic")
        if len(stats.top_partners) > 1:
            weights = [w for _, w in stats.top_partners]
            assert weights == sorted(weights, reverse=True)

    def test_stats_fields_are_correct_types(self, engine):
        stats = engine.player_stats("LeBron")
        assert isinstance(stats.name,                  str)
        assert isinstance(stats.team,                  str)
        assert isinstance(stats.games_played,          int)
        assert isinstance(stats.ast_total,             int)
        assert isinstance(stats.assists_received_total,int)

    def test_games_played_at_least_10(self, engine):
        """All players in the graph played at least 10 games."""
        stats = engine.player_stats("LeBron")
        assert stats.games_played >= 10


# ── Interaction 4: top_10_assisters ──────────────────────────────────────────

class TestTop10Assisters:
    """Return a ranked leaderboard of the top assist givers."""

    def test_returns_exactly_10(self, engine):
        results = engine.top_10_assisters()
        assert len(results) == 10

    def test_ranked_in_order(self, engine):
        results = engine.top_10_assisters()
        totals  = [ast for _, _, _, ast, _ in results]
        assert totals == sorted(totals, reverse=True), \
            "Leaderboard must be sorted highest assists first"

    def test_ranks_are_1_through_10(self, engine):
        results = engine.top_10_assisters()
        ranks   = [rank for rank, *_ in results]
        assert ranks == list(range(1, 11))

    def test_each_entry_has_five_fields(self, engine):
        for entry in engine.top_10_assisters():
            rank, name, team, ast, apg = entry   # must unpack cleanly

    def test_all_assist_totals_positive(self, engine):
        for _, _, _, ast, _ in engine.top_10_assisters():
            assert ast > 0

    def test_top_assister_is_jokic(self, engine):
        """Nikola Jokic leads the demo dataset in total assists."""
        top = engine.top_10_assisters()[0]
        assert "Jokic" in top[1]


# ── Bonus: PageRank centrality ────────────────────────────────────────────────

class TestPlaymakerCentrality:
    """PageRank must return a valid influence ranking."""

    def test_returns_requested_count(self, engine):
        assert len(engine.playmaker_centrality(5))  == 5
        assert len(engine.playmaker_centrality(10)) == 10

    def test_scores_sum_to_approximately_one(self, engine):
        # PageRank scores over the full graph sum to ~1
        all_scores = [s for _, s in engine.playmaker_centrality(
            len(list(engine.G.nodes()))
        )]
        assert abs(sum(all_scores) - 1.0) < 0.01

    def test_scores_are_positive(self, engine):
        for _, score in engine.playmaker_centrality(10):
            assert score > 0


# ── Bonus: assist path finder ─────────────────────────────────────────────────

class TestAssistPath:
    """Shortest directed path between two players."""

    def test_known_path_exists(self, engine):
        path = engine.assist_path("LeBron James", "Jamal Murray")
        assert path is not None, "A path must exist between connected players"

    def test_path_is_list_of_strings(self, engine):
        path = engine.assist_path("LeBron James", "Jamal Murray")
        assert isinstance(path, list)
        for name in path:
            assert isinstance(name, str)

    def test_path_starts_and_ends_correctly(self, engine):
        path = engine.assist_path("LeBron James", "Jamal Murray")
        assert path[0]  == "LeBron James"
        assert path[-1] == "Jamal Murray"

    def test_unknown_player_returns_none(self, engine):
        path = engine.assist_path("ZZZFAKE", "Jamal Murray")
        assert path is None

    def test_same_player_path(self, engine):
        """Path from a player to themselves should be a single-node list."""
        path = engine.assist_path("Nikola Jokic", "Nikola Jokic")
        assert path is not None
        assert len(path) == 1
