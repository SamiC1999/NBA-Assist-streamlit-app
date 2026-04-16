"""
demo_data.py
------------
Realistic NBA assist DiGraph — 60 players across 12 teams, based on
2023-24 season stats. Works offline with no API key needed.

Call:
    from demo_data import build_demo_graph
    G = build_demo_graph()
"""

import networkx as nx


def build_demo_graph(season: int = 2023) -> nx.DiGraph:
    G = nx.DiGraph()
    G.graph["season"] = season
    G.graph["source"] = "demo"

    # (id, name, team, ast_total, ast_per_game, pts_total, pts_per_game, reb_total, gp)
    players = [
        # Denver Nuggets
        ( 1, "Nikola Jokic",         "DEN",  903, 11.7, 1593, 26.4,  784, 79),
        ( 2, "Jamal Murray",         "DEN",  287,  4.2, 1103, 21.2,  356, 63),
        ( 3, "Michael Porter Jr.",   "DEN",  198,  3.1,  921, 16.7,  412, 65),
        ( 4, "Aaron Gordon",         "DEN",  243,  3.5,  765, 13.9,  589, 76),
        ( 5, "Kentavious Caldwell",  "DEN",  156,  2.3,  612, 10.1,  198, 67),
        # Indiana Pacers
        ( 6, "Tyrese Haliburton",    "IND",  746, 10.9, 1204, 20.1,  312, 69),
        ( 7, "Pascal Siakam",        "IND",  243,  3.8, 1312, 21.3,  589, 62),
        ( 8, "Bennedict Mathurin",   "IND",  156,  2.4,  987, 15.9,  298, 65),
        ( 9, "Myles Turner",         "IND",   98,  1.5,  876, 13.9,  612, 60),
        (10, "T.J. McConnell",       "IND",  312,  5.6,  543,  8.4,  198, 68),
        # Atlanta Hawks
        (11, "Trae Young",           "ATL",  697, 10.8, 1521, 25.7,  218, 64),
        (12, "Dejounte Murray",      "ATL",  312,  5.1, 1109, 21.4,  412, 60),
        (13, "Clint Capela",         "ATL",   87,  1.4,  612, 11.2,  876, 60),
        (14, "Bogdan Bogdanovic",    "ATL",  201,  3.8,  876, 14.1,  234, 56),
        (15, "De'Andre Hunter",      "ATL",  134,  2.3,  765, 13.4,  312, 58),
        # LA Lakers
        (16, "LeBron James",         "LAL",  589,  8.3, 1627, 25.7,  524, 71),
        (17, "Anthony Davis",        "LAL",  156,  2.3, 1654, 24.7,  989, 71),
        (18, "D'Angelo Russell",     "LAL",  312,  5.2,  876, 18.0,  256, 60),
        (19, "Austin Reaves",        "LAL",  189,  2.8,  754, 13.0,  256, 72),
        (20, "Rui Hachimura",        "LAL",  112,  2.0,  698, 13.2,  312, 57),
        # Dallas Mavericks
        (21, "Luka Doncic",          "DAL",  576,  9.8, 1893, 33.9,  489, 66),
        (22, "Kyrie Irving",         "DAL",  312,  5.8, 1321, 25.6,  298, 51),
        (23, "PJ Washington",        "DAL",  156,  2.9,  698, 12.1,  512, 57),
        (24, "Tim Hardaway Jr.",     "DAL",  134,  2.5,  756, 14.7,  187, 52),
        (25, "Derrick Jones Jr.",    "DAL",   98,  1.8,  512,  9.4,  312, 57),
        # Golden State Warriors
        (26, "Stephen Curry",        "GSW",  312,  5.3, 1654, 26.4,  421, 74),
        (27, "Draymond Green",       "GSW",  487,  6.8,  412,  9.1,  612, 55),
        (28, "Chris Paul",           "GSW",  498,  7.8,  654, 10.4,  298, 58),
        (29, "Klay Thompson",        "GSW",  189,  2.9, 1102, 17.9,  312, 60),
        (30, "Jonathan Kuminga",     "GSW",  145,  2.4,  876, 16.1,  312, 55),
        # OKC Thunder
        (31, "Shai Gilgeous",        "OKC",  312,  5.5, 1876, 30.1,  298, 75),
        (32, "Chet Holmgren",        "OKC",  189,  2.9, 1102, 16.5,  698, 69),
        (33, "Josh Giddey",          "OKC",  312,  5.0,  876, 14.6,  498, 55),
        (34, "Luguentz Dort",        "OKC",  112,  2.1,  698, 13.7,  198, 62),
        (35, "Isaiah Joe",           "OKC",   87,  1.8,  543, 10.2,  145, 55),
        # LA Clippers
        (36, "James Harden",         "LAC",  521,  8.5, 1102, 16.6,  389, 60),
        (37, "Kawhi Leonard",        "LAC",  201,  4.1, 1098, 23.7,  489, 50),
        (38, "Paul George",          "LAC",  267,  4.9, 1102, 22.6,  412, 52),
        (39, "Russell Westbrook",    "LAC",  301,  5.6,  698, 11.1,  356, 65),
        (40, "Ivica Zubac",          "LAC",   87,  1.4,  698, 11.2,  756, 70),
        # Boston Celtics
        (41, "Jaylen Brown",         "BOS",  234,  3.8, 1487, 23.0,  423, 70),
        (42, "Jayson Tatum",         "BOS",  312,  4.9, 1698, 26.9,  612, 74),
        (43, "Jrue Holiday",         "BOS",  287,  4.5,  876, 12.5,  345, 68),
        (44, "Al Horford",           "BOS",  201,  2.9,  654,  9.2,  512, 65),
        (45, "Kristaps Porzingis",   "BOS",  134,  2.2, 1012, 20.1,  512, 57),
        # Milwaukee Bucks
        (46, "Giannis Antetokounmpo","MIL",  456,  6.5, 1876, 30.4,  897, 73),
        (47, "Damian Lillard",       "MIL",  498,  7.4, 1567, 24.3,  312, 73),
        (48, "Brook Lopez",          "MIL",  112,  1.6,  987, 12.5,  512, 70),
        (49, "Khris Middleton",      "MIL",  245,  4.2, 1098, 20.8,  367, 56),
        (50, "Bobby Portis",         "MIL",  112,  1.8,  876, 14.6,  512, 72),
        # Phoenix Suns
        (51, "Kevin Durant",         "PHX",  287,  4.4, 1698, 27.1,  512, 75),
        (52, "Devin Booker",         "PHX",  412,  6.9, 1654, 27.8,  356, 68),
        (53, "Bradley Beal",         "PHX",  312,  5.2,  987, 18.2,  245, 53),
        (54, "Jusuf Nurkic",         "PHX",  189,  2.9,  698, 11.4,  756, 65),
        (55, "Eric Gordon",          "PHX",  134,  2.8,  654, 13.5,  198, 56),
        # Miami Heat
        (56, "Bam Adebayo",          "MIA",  312,  4.9, 1098, 19.3,  756, 71),
        (57, "Tyler Herro",          "MIA",  312,  5.1, 1102, 20.8,  298, 60),
        (58, "Jimmy Butler",         "MIA",  312,  5.3, 1102, 20.8,  356, 60),
        (59, "Caleb Martin",         "MIA",  134,  2.4,  698, 12.1,  298, 65),
        (60, "Kyle Lowry",           "MIA",  287,  5.1,  543,  8.7,  198, 62),
    ]

    for pid, name, team, ast, apg, pts, ppg, reb, gp in players:
        G.add_node(pid, name=name, team_abbr=team, ast_total=ast,
                   ast_per_game=apg, pts_total=pts, pts_per_game=ppg,
                   reb_total=reb, games_played=gp)

    edges = [
        # Denver Nuggets
        ( 1,  2, 312), ( 1,  3, 198), ( 1,  4, 243), ( 1,  5,  67), ( 1, 16,  38),
        ( 2,  1,  89), ( 4,  1, 112), ( 3,  1,  67), ( 5,  1,  45),
        ( 2,  3,  98), ( 4,  3,  78), ( 2,  4,  87),
        # Indiana Pacers
        ( 6,  7, 287), ( 6,  8, 198), ( 6,  9, 145), ( 6, 10, 112),
        (10,  6, 134), (10,  7, 112), ( 7,  8,  89), ( 8,  6,  45),
        (10,  8,  98), ( 7,  9,  76),
        # Atlanta Hawks
        (11, 12, 243), (11, 13, 187), (11, 14, 156), (11, 15, 112),
        (12, 11,  89), (12, 13,  78), (14, 11,  67), (15, 11,  45),
        (12, 14,  98), (14, 15,  56),
        # LA Lakers
        (16, 17, 312), (16, 18, 156), (16, 19,  98), (16, 20,  67), (16,  1,  22),
        (18, 16,  78), (19, 16,  45), (18, 17,  89), (20, 16,  34),
        (18, 19,  67), (19, 17,  78),
        # Dallas Mavericks
        (21, 22, 289), (21, 23, 178), (21, 24, 134), (21, 25,  89),
        (22, 21, 189), (22, 23, 112), (23, 21,  78), (24, 21,  56),
        (22, 24,  98), (23, 24,  67),
        # Golden State Warriors
        (27, 26, 198), (27, 29, 156), (27, 28,  89), (27, 30,  78),
        (28, 26, 234), (28, 27,  89), (28, 29,  87), (28, 30,  67),
        (26, 29, 134), (26, 27,  78), (29, 26,  56),
        # OKC Thunder
        (33, 31, 198), (33, 32, 156), (31, 32,  89), (32, 31,  67),
        (31, 33, 112), (34, 31,  78), (35, 31,  56), (33, 34,  98),
        # LA Clippers
        (36, 37, 245), (36, 38, 198), (36, 39, 134), (36, 40,  89),
        (39, 36,  78), (38, 37, 134), (39, 37, 112), (38, 36,  56),
        (37, 38,  98), (39, 40,  67),
        # Boston Celtics
        (43, 42, 198), (43, 41, 178), (42, 41, 156), (44, 42, 134),
        (41, 42, 145), (43, 44,  89), (42, 43,  67), (44, 41,  78),
        (45, 42, 112), (43, 45,  98),
        # Milwaukee Bucks
        (47, 46, 234), (47, 49, 156), (47, 50, 112), (46, 47,  89),
        (46, 49, 145), (49, 46,  78), (50, 46,  67), (47, 48, 134),
        (48, 46,  56), (49, 48,  78),
        # Phoenix Suns
        (52, 51, 245), (52, 53, 156), (53, 52, 134), (52, 54, 112),
        (51, 52,  89), (53, 51,  78), (54, 51,  67), (55, 52,  89),
        (52, 55,  98), (51, 53,  67),
        # Miami Heat
        (60, 56, 198), (60, 57, 156), (58, 56, 145), (58, 57, 134),
        (56, 58,  89), (57, 58,  78), (60, 58, 112), (59, 58,  67),
        (56, 57,  98), (57, 56,  67),
    ]

    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    return G


if __name__ == "__main__":
    G = build_demo_graph()
    print(f"Demo graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    from query_engine import AssistQueryEngine
    engine = AssistQueryEngine(G)
    print("\nTop 10 assisters:")
    for rank, name, team, ast, apg in engine.top_10_assisters():
        print(f"  {rank:2}. {name:<26} ({team})  {ast} ast  {apg}/gm")
