"""
main.py
-------
Command-line interface for the NBA Assist Network.

Run:
    python main.py

Optional flags:
    --season 2023          (default: 2023)
    --seasons 2021 2022 2023   (merge multiple seasons)
    --rebuild              (force re-fetch data, ignore cache)
"""

import argparse
import sys

from graph_builder import AssistGraphBuilder
from query_engine import AssistQueryEngine


# ── Display helpers ───────────────────────────────────────────────────────────

DIVIDER = "─" * 54

def header(title: str) -> None:
    print(f"\n{'═' * 54}")
    print(f"  {title}")
    print(f"{'═' * 54}")

def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

def error(msg: str) -> None:
    print(f"\n  ✗  {msg}\n")

def success(msg: str) -> None:
    print(f"\n  ✓  {msg}")


# ── Menu actions ──────────────────────────────────────────────────────────────

def action_top_partners(engine: AssistQueryEngine) -> None:
    section("Search Player → Top 5 Assist Partners")
    name = input("  Enter player name: ").strip()
    if not name:
        error("No name entered.")
        return

    results = engine.top_assist_partners(name)
    if not results:
        error(f"No player found matching '{name}'. Try a partial last name.")
        return

    player_name = results[0].assister_name
    print(f"\n  Top 5 players that {player_name} assisted most:\n")
    for i, rel in enumerate(results, 1):
        print(f"    {i}. {rel.receiver_name:<25} ~{rel.weight} estimated assists")


def action_who_assisted(engine: AssistQueryEngine) -> None:
    section("Players Who Assisted a Specific Player")
    name = input("  Enter player name: ").strip()
    if not name:
        error("No name entered.")
        return

    results = engine.players_who_assisted(name)
    if not results:
        error(f"No player found matching '{name}'.")
        return

    player_name = results[0].receiver_name if results else name
    print(f"\n  All players who assisted {player_name} (sorted by volume):\n")
    if not results:
        print("    (none found — player may not appear in assist edges)")
        return
    for i, rel in enumerate(results, 1):
        print(f"    {i:2}. {rel.assister_name:<25} ~{rel.weight} estimated assists")


def action_player_stats(engine: AssistQueryEngine) -> None:
    section("Player Stats")
    name = input("  Enter player name: ").strip()
    if not name:
        error("No name entered.")
        return

    stats = engine.player_stats(name)
    if stats is None:
        error(f"No player found matching '{name}'.")
        return

    print(f"\n{stats.display()}")


def action_top_10(engine: AssistQueryEngine) -> None:
    section("Top 10 Players by Total Assists Given")
    top = engine.top_10_assisters()
    if not top:
        error("No data available.")
        return

    print()
    print(f"  {'#':<4} {'Player':<24} {'Team':<6} {'Total Ast':>9}  {'Ast/Gm':>7}")
    print(f"  {'-'*4} {'-'*24} {'-'*6} {'-'*9}  {'-'*7}")
    for rank, name, team, ast, apg in top:
        print(f"  {rank:<4} {name:<24} {team:<6} {ast:>9}  {apg:>7.1f}")


# ── Main menu loop ────────────────────────────────────────────────────────────

MENU_OPTIONS = {
    "1": ("Search player → top 5 assist partners", action_top_partners),
    "2": ("List who assisted a specific player",   action_who_assisted),
    "3": ("Show basic stats for a player",          action_player_stats),
    "4": ("Top 10 players by total assists given",  action_top_10),
    "q": ("Quit",                                   None),
}


def print_menu() -> None:
    header("NBA Assist Network Explorer")
    print()
    for key, (label, _) in MENU_OPTIONS.items():
        print(f"    [{key}]  {label}")
    print()


def run(engine: AssistQueryEngine) -> None:
    while True:
        print_menu()
        choice = input("  Select an option: ").strip().lower()
        if choice == "q":
            print("\n  Thanks for exploring the NBA Assist Network. Goodbye!\n")
            break
        if choice not in MENU_OPTIONS:
            error(f"'{choice}' is not a valid option. Please choose 1–4 or q.")
            continue
        _, action = MENU_OPTIONS[choice]
        action(engine)
        input("\n  Press Enter to return to menu…")


# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NBA Assist Network — command-line explorer"
    )
    parser.add_argument(
        "--season", type=int, default=2023,
        help="Season year to load (e.g. 2023 for the 2023-24 season)"
    )
    parser.add_argument(
        "--seasons", type=int, nargs="+",
        help="Multiple seasons to merge (overrides --season)"
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Ignore cache and re-fetch data from API"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    builder = AssistGraphBuilder()

    try:
        if args.seasons:
            print(f"\nBuilding merged graph for seasons: {args.seasons} …")
            G = builder.merge_seasons(args.seasons)
            season_label = "+".join(str(s) for s in args.seasons)
        else:
            print(f"\nLoading {args.season} season graph …")
            G = builder.build(season=args.season, force_rebuild=args.rebuild)
            season_label = str(args.season)

        engine = AssistQueryEngine(G)
        print(f"  Graph ready — {G.number_of_nodes()} players, "
              f"{G.number_of_edges()} assist edges  [season: {season_label}]")
        run(engine)

    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        print("  Make sure your BALLDONTLIE_API_KEY env variable is set "
              "or the cache directory has data.\n")
        sys.exit(1)
