# NBA Assist Network Explorer

A directed weighted graph of NBA assist relationships built on real data from stats.nba.com. Visualizes passing patterns, playmaker rankings, and assist flows across the league.

---

## What It Does

The app models the NBA as a network where:
- **Nodes** are players
- **Edges** are directed assist relationships (A assisted B)
- **Edge weights** represent assist volume between pairs

This graph structure reveals things flat stat tables cannot show, like which players are the true engines of their offense, how assists flow within a team, and how connected any two players are through passing chains.

---

## Four Core Interactions

| Tab | What it does |
|-----|--------------|
| Top Assist Partners | Search any player and see the 5 players they assisted most |
| Who Assisted | See every player who passed to a specific player |
| Player Stats | Full stat card with assists given, received, points, and rebounds |
| Top 10 Leaderboard | League-wide ranking by total assists given |

### Bonus Features
- **Playmaker Centrality** using PageRank to measure influence in the assist network
- **Assist Path Finder** finds the shortest passing chain between any two players
- **Network Visualizations** with three graph views: top assist flows, team subgraph, and full network

---

## Tech Stack

- **NetworkX** for the directed weighted graph
- **nba_api** to pull real data from stats.nba.com (no API key needed)
- **Streamlit** for the web interface
- **matplotlib** for network visualizations
- **pytest** for the test suite (42 tests)

---

## Project Structure

```
nba_assist_network/
├── streamlit_app.py       # Streamlit web UI
├── graph_builder.py       # Builds and persists the NetworkX DiGraph
├── query_engine.py        # All four interactions and bonus features
├── data_fetcher.py        # API wrapper with local JSON caching
├── graph_visualizer.py    # matplotlib network diagram functions
├── demo_data.py           # 60-player offline mock graph for testing
├── main.py                # Command line interface
├── test_assist_network.py # Full test suite (42 tests)
└── requirements.txt
```

---


## Live App

The app is deployed on Streamlit Community Cloud. Link Below

https://nba-assist--app-iec4xpnvlnvs2sfv9i7fbt.streamlit.app/


---

## Data Source

Player stats are fetched from stats.nba.com using the nba_api Python package. Seasons 2021 through 2025 are supported. Data is cached locally after the first load so subsequent runs are instant.

Assist edges are estimated using a scoring-share heuristic: each player's total assists are distributed across teammates proportionally to their share of team scoring. This is a standard approximation used when play-by-play assist-to-player data is unavailable.
