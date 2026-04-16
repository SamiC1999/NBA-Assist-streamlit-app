"""
streamlit_app.py
----------------
NBA Assist Network Explorer — Streamlit UI
Data source: stats.nba.com via nba_api (free, no key needed)

Run:
    streamlit run streamlit_app.py
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from query_engine import AssistQueryEngine

st.set_page_config(
    page_title="NBA Assist Network",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    .stat-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 10px; padding: 18px 22px;
        margin: 8px 0; text-align: center;
    }
    .stat-card h3 { margin:0 0 4px 0; font-size:12px; color:#8b949e;
                    text-transform:uppercase; letter-spacing:1px; }
    .stat-card p  { margin:0; font-size:26px; font-weight:700; color:#f97316; }
    .result-row {
        background: #161b22; border: 1px solid #30363d;
        border-left: 4px solid #f97316; border-radius: 8px;
        padding: 12px 18px; margin: 6px 0;
        display: flex; justify-content: space-between; align-items: center;
    }
    .result-row .player-name { font-size:16px; font-weight:600; color:#e6edf3; }
    .result-row .badge {
        background:#f97316; color:#0d1117; font-weight:700;
        font-size:13px; padding:3px 10px; border-radius:20px;
    }
    .lb-row {
        background:#161b22; border:1px solid #21262d; border-radius:6px;
        padding:10px 16px; margin:4px 0;
        display:flex; align-items:center; gap:16px;
    }
    .rnum        { font-size:18px; font-weight:800; color:#8b949e; width:28px; }
    .rnum-gold   { font-size:18px; font-weight:800; color:#ffd700; width:28px; }
    .rnum-silver { font-size:18px; font-weight:800; color:#c0c0c0; width:28px; }
    .rnum-bronze { font-size:18px; font-weight:800; color:#cd7f32; width:28px; }
    .sec-title {
        font-size:12px; font-weight:600; color:#8b949e;
        text-transform:uppercase; letter-spacing:1.5px;
        margin:20px 0 10px 0; border-bottom:1px solid #21262d; padding-bottom:6px;
    }
    .stTextInput > div > div > input {
        background:#21262d !important; border:1px solid #30363d !important;
        color:#e6edf3 !important; border-radius:8px !important;
    }
    .stButton > button {
        background:#f97316 !important; color:#0d1117 !important;
        font-weight:700 !important; border:none !important;
        border-radius:8px !important;
    }
    #MainMenu { visibility:hidden; }
    footer     { visibility:hidden; }
    header     { visibility:hidden; }
</style>
""", unsafe_allow_html=True)


# ── Graph loader with live progress ───────────────────────────────────────────
def load_graph(season: int):
    cache_key = f"live_graph_{season}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    from graph_builder import AssistGraphBuilder
    builder    = AssistGraphBuilder()
    status_box = st.empty()
    log_lines  = []

    def progress_cb(msg):
        log_lines.append(msg)
        status_box.markdown(
            "<div style='background:#161b22;border:1px solid #30363d;"
            "border-radius:8px;padding:14px 18px;font-family:monospace;"
            "font-size:13px;color:#8b949e'>"
            + "<br>".join(
                ("[ done ] " if ("Done" in l or "cache" in l or "done" in l) else "[ ... ] ") + l
                for l in log_lines[-8:]
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    G = builder.build(season=season, progress_cb=progress_cb)
    st.session_state[cache_key] = G
    status_box.empty()
    return G


def _get_visualizer():
    try:
        import graph_visualizer as gv
        return gv
    except ImportError:
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## NBA Assist Network Explorer")
    st.markdown("---")
    season = st.selectbox("Season", [2025, 2024, 2023, 2022, 2021], index=0)
    st.markdown(
        "<div style='font-size:12px;color:#8b949e;margin-bottom:12px'>"
        "Pulls from stats.nba.com"
        "</div>", unsafe_allow_html=True)
    if st.button("Clear cache and reload"):
        for k in list(st.session_state.keys()):
            if k.startswith("live_graph"):
                del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.markdown(
        "<div style='font-size:12px;color:#8b949e'>"
        "Directed weighted graph<br>"
        "Nodes = players<br>"
        "Edges = assist relationships<br><br>"
        "4 required interactions<br>"
        "Network viz · PageRank · Pathfinding"
        "</div>", unsafe_allow_html=True)


# ── Load graph ─────────────────────────────────────────────────────────────────
try:
    G      = load_graph(season)
    engine = AssistQueryEngine(G)
    graph_loaded = True
except Exception as exc:
    graph_loaded = False
    load_error   = str(exc)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:30px;font-weight:800;margin-bottom:2px'>"
    "NBA Assist Network Explorer</h1>"
    "<p style='color:#8b949e;margin-top:0'>Directed graph analysis of NBA playmaking</p>",
    unsafe_allow_html=True)

if not graph_loaded:
    st.error(f"Failed to load graph: {load_error}")
    st.stop()

# ── Summary metric cards ───────────────────────────────────────────────────────
total_ast   = sum(d.get("ast_total", 0) for _, d in G.nodes(data=True))
teams_count = len({d.get("team_abbr") for _, d in G.nodes(data=True)})

for col, label, val in zip(
    st.columns(4),
    ["Players", "Assist Edges", "Total Assists", "Teams"],
    [G.number_of_nodes(), G.number_of_edges(), f"{total_ast:,}", teams_count],
):
    with col:
        st.markdown(
            f"<div class='stat-card'><h3>{label}</h3><p>{val}</p></div>",
            unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Top Assist Partners",
    "Who Assisted",
    "Player Stats",
    "Top 10 Leaderboard",
    "Network Graph",
])


# ─── TAB 1 ────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div class='sec-title'>Interaction 1 — Search a player and see their top 5 assist partners</div>",
                unsafe_allow_html=True)
    ci, cb = st.columns([4, 1])
    with ci:
        name1 = st.text_input("Player name", placeholder="e.g. Jokic, LeBron, Haliburton", key="t1")
    with cb:
        st.markdown("<br>", unsafe_allow_html=True)
        go1 = st.button("Search", key="b1")

    if go1 or name1:
        if not name1.strip():
            st.info("Type a player name above.")
        else:
            results1 = engine.top_assist_partners(name1.strip())
            if not results1:
                st.error(f"No player found matching '{name1}'. Try a partial last name.")
            else:
                pn = results1[0].assister_name
                st.markdown(
                    f"<p style='color:#8b949e;margin:8px 0 16px'>Top 5 players that "
                    f"<strong style='color:#f97316'>{pn}</strong> assisted most:</p>",
                    unsafe_allow_html=True)
                labels = ["1.", "2.", "3.", "4.", "5."]
                for i, rel in enumerate(results1, 1):
                    st.markdown(
                        "<div class='result-row'>"
                        "<span class='player-name'>" + labels[i-1] + " &nbsp;" + rel.receiver_name + "</span>"
                        "<span class='badge'>~" + str(rel.weight) + " assists</span>"
                        "</div>", unsafe_allow_html=True)


# ─── TAB 2 ────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='sec-title'>Interaction 2 — All players who assisted a specific player</div>",
                unsafe_allow_html=True)
    ci2, cb2 = st.columns([4, 1])
    with ci2:
        name2 = st.text_input("Player name", placeholder="e.g. Anthony Davis, Curry", key="t2")
    with cb2:
        st.markdown("<br>", unsafe_allow_html=True)
        go2 = st.button("Search", key="b2")

    if go2 or name2:
        if not name2.strip():
            st.info("Type a player name above.")
        else:
            results2 = engine.players_who_assisted(name2.strip())
            if not results2:
                st.error(f"No data found for '{name2}'.")
            else:
                pn2 = results2[0].receiver_name
                st.markdown(
                    f"<p style='color:#8b949e;margin:8px 0 16px'>Players who assisted "
                    f"<strong style='color:#f97316'>{pn2}</strong>:</p>",
                    unsafe_allow_html=True)
                for rel in results2:
                    st.markdown(
                        "<div class='result-row'>"
                        "<span class='player-name'>" + rel.assister_name + "</span>"
                        "<span class='badge'>~" + str(rel.weight) + " assists</span>"
                        "</div>", unsafe_allow_html=True)


# ─── TAB 3 ────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='sec-title'>Interaction 3 — Basic stats for any player</div>",
                unsafe_allow_html=True)
    ci3, cb3 = st.columns([4, 1])
    with ci3:
        name3 = st.text_input("Player name", placeholder="e.g. Trae Young, Luka, Giannis", key="t3")
    with cb3:
        st.markdown("<br>", unsafe_allow_html=True)
        go3 = st.button("Search", key="b3")

    if go3 or name3:
        if not name3.strip():
            st.info("Type a player name above.")
        else:
            stats = engine.player_stats(name3.strip())
            if stats is None:
                st.error(f"No player found matching '{name3}'.")
            else:
                st.markdown(
                    "<h2 style='margin:16px 0 2px;color:#e6edf3'>" + stats.name + "</h2>"
                    "<p style='color:#8b949e;margin:0 0 18px'>Team: <strong>" + stats.team + "</strong>"
                    " &nbsp;·&nbsp; " + str(stats.games_played) + " games played</p>",
                    unsafe_allow_html=True)

                for col, (lbl, val) in zip(st.columns(5), [
                    ("Assists Given",  stats.ast_total),
                    ("Ast / Game",     stats.ast_per_game),
                    ("Ast Received",   stats.assists_received_total),
                    ("Points",         stats.pts_total),
                    ("Rebounds",       stats.reb_total),
                ]):
                    with col:
                        st.markdown(
                            "<div class='stat-card'><h3>" + lbl + "</h3><p>" + str(val) + "</p></div>",
                            unsafe_allow_html=True)

                if stats.top_partners:
                    st.markdown("<div class='sec-title' style='margin-top:20px'>Top Assist Targets</div>",
                                unsafe_allow_html=True)
                    for partner_name, w in stats.top_partners:
                        st.markdown(
                            "<div class='result-row'>"
                            "<span class='player-name'>" + partner_name + "</span>"
                            "<span class='badge'>~" + str(w) + " assists</span>"
                            "</div>", unsafe_allow_html=True)


# ─── TAB 4 ────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("<div class='sec-title'>Interaction 4 — Top 10 players by total assists given</div>",
                unsafe_allow_html=True)

    top10   = engine.top_10_assisters()
    max_ast = top10[0][3] if top10 else 1
    rank_cls = {1: "rnum-gold", 2: "rnum-silver", 3: "rnum-bronze"}

    for rank, pname, team, ast, apg in top10:
        bar = int(ast / max_ast * 100)
        cls = rank_cls.get(rank, "rnum")
        st.markdown(
            "<div class='lb-row'>"
            "<span class='" + cls + "'>" + str(rank) + "</span>"
            "<span style='flex:1;font-weight:600;font-size:15px'>" + pname + "</span>"
            "<span style='color:#8b949e;font-size:12px;width:40px'>" + team + "</span>"
            "<span style='width:140px;background:#21262d;border-radius:4px;height:6px;"
            "display:inline-block;vertical-align:middle'>"
            "<span style='display:block;width:" + str(bar) + "%;background:#f97316;"
            "height:6px;border-radius:4px'></span></span>"
            "<span style='width:60px;text-align:right;font-weight:700;color:#f97316'>" + str(ast) + "</span>"
            "<span style='color:#8b949e;font-size:12px;width:60px;text-align:right'>" + str(apg) + "/gm</span>"
            "</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("Bonus: Playmaker Centrality (PageRank)"):
        st.markdown(
            "<p style='color:#8b949e;font-size:13px;margin-bottom:12px'>"
            "PageRank measures influence in the assist network — "
            "whose teammates depend on them most to facilitate scoring.</p>",
            unsafe_allow_html=True)
        for i, (pname, score) in enumerate(engine.playmaker_centrality(10), 1):
            st.markdown(
                "<div class='lb-row'>"
                "<span class='rnum'>" + str(i) + "</span>"
                "<span style='flex:1;font-weight:600'>" + pname + "</span>"
                "<span style='color:#f97316;font-weight:700'>" + f"{score:.4f}" + "</span>"
                "</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("Bonus: Assist Path Finder"):
        st.markdown(
            "<p style='color:#8b949e;font-size:13px;margin-bottom:12px'>"
            "Find the shortest assist chain between any two players.</p>",
            unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            path_from = st.text_input("From player", placeholder="e.g. LeBron James", key="pf")
        with pc2:
            path_to = st.text_input("To player", placeholder="e.g. Nikola Jokic", key="pt")
        if st.button("Find Path", key="path_btn"):
            if path_from and path_to:
                path = engine.assist_path(path_from.strip(), path_to.strip())
                if path is None:
                    st.warning("No directed path found between those players.")
                else:
                    chain = " → ".join(path)
                    st.success(f"Path ({len(path)-1} hops): {chain}")
            else:
                st.info("Enter both player names.")


# ─── TAB 5 ────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("<div class='sec-title'>Network Graph Visualizations</div>",
                unsafe_allow_html=True)

    gv = _get_visualizer()
    if gv is None:
        st.warning("Install matplotlib to enable: pip install matplotlib")
    else:
        viz_type = st.radio(
            "View",
            ["Top Assist Flows", "Team Subgraph", "Full Network"],
            horizontal=True,
        )

        if viz_type == "Top Assist Flows":
            top_n = st.slider("Top edges to show", 8, 30, 15)
            with st.spinner("Rendering..."):
                fig = gv.top_flow_graph(G, top_n=top_n)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

        elif viz_type == "Team Subgraph":
            teams_avail = sorted({
                d.get("team_abbr", "") for _, d in G.nodes(data=True) if d.get("team_abbr")
            })
            sel_team = st.selectbox("Select team", teams_avail)
            with st.spinner("Rendering..."):
                fig = gv.team_subgraph(G, sel_team)
                if fig is None:
                    st.warning("Not enough players for this team in the graph.")
                else:
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)

        else:
            top_e = st.slider("Max edges to display", 20, 100, 50)
            with st.spinner("Rendering full network..."):
                fig = gv.full_network(
                    G, top_n_edges=top_e,
                    title="NBA Assist Network — " + str(season) + " Season",
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

        st.markdown(
            "<p style='color:#8b949e;font-size:12px;margin-top:8px'>"
            "Node size = total assists · Node colour = team · "
            "Edge thickness = assist volume · Arrows show direction (assister to receiver)</p>",
            unsafe_allow_html=True)
